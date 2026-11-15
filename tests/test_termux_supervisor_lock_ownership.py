"""Regression tests for TermuxSupervisor's persistent-inode ownership lock."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.termux_supervisor as supervisor


class SupervisorLockOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        state = Path(self.temp.name) / "state"
        state.mkdir()
        self.lock_path = state / "supervisor.lock"
        self.pid_path = state / "supervisor.pid"
        self.original_paths = (
            supervisor.SUPERVISOR_LOCK,
            supervisor.SUPERVISOR_PID,
        )
        supervisor.SUPERVISOR_LOCK = self.lock_path
        supervisor.SUPERVISOR_PID = self.pid_path

    def tearDown(self):
        supervisor.SUPERVISOR_LOCK, supervisor.SUPERVISOR_PID = self.original_paths
        self.temp.cleanup()

    def new_lock(self):
        lock = supervisor.SupervisorLock()
        lock.lock_path = self.lock_path
        lock.pid_path = self.pid_path
        return lock

    def test_three_participant_contention_preserves_one_inode(self):
        import fcntl

        owner_a = self.new_lock()
        contender_c = self.new_lock()

        self.assertTrue(owner_a.try_acquire())
        inode = self.lock_path.stat().st_ino
        owner_marker = self.pid_path.read_text()

        # B opens the old inode before A releases it. Its failed nonblocking
        # flock must not alter A's marker, and B deliberately keeps this fd.
        contender_b_fd = os.open(str(self.lock_path), os.O_RDWR | os.O_CREAT, 0o600)
        self.assertEqual(os.fstat(contender_b_fd).st_ino, inode)
        with self.assertRaises(BlockingIOError):
            fcntl.flock(contender_b_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.assertEqual(self.pid_path.read_text(), owner_marker)
        self.assertEqual(self.lock_path.read_text(), owner_marker)

        owner_a.release()
        self.assertTrue(self.lock_path.exists())
        self.assertEqual(self.lock_path.stat().st_ino, inode)

        # B now acquires using its already-open descriptor. C opens by pathname
        # and must contend on the exact same inode rather than a replacement.
        fcntl.flock(contender_b_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.ftruncate(contender_b_fd, 0)
        os.lseek(contender_b_fd, 0, os.SEEK_SET)
        os.write(contender_b_fd, str(os.getpid()).encode("ascii"))
        os.fsync(contender_b_fd)
        self.pid_path.write_text(str(os.getpid()))
        self.assertFalse(contender_c.try_acquire())
        self.assertEqual(self.pid_path.read_text(), str(os.getpid()))
        self.assertEqual(self.lock_path.stat().st_ino, inode)

        self.pid_path.unlink()
        os.ftruncate(contender_b_fd, 0)
        os.fsync(contender_b_fd)
        fcntl.flock(contender_b_fd, fcntl.LOCK_UN)
        os.close(contender_b_fd)
        self.assertTrue(self.lock_path.exists())
        self.assertEqual(self.lock_path.stat().st_ino, inode)
        self.assertEqual(self.lock_path.read_text(), "")
    def test_release_does_not_remove_mismatched_pid_marker(self):
        owner = self.new_lock()
        self.assertTrue(owner.try_acquire())
        self.pid_path.write_text("99999999")
        owner.release()

        self.assertEqual(self.pid_path.read_text(), "99999999")
        # The persistent inode remains even if its owner record was unexpected.
        self.assertTrue(self.lock_path.exists())

    def test_stale_or_corrupt_pid_is_replaced_only_after_lock_acquired(self):
        self.lock_path.write_text("stale-lock-record")
        self.pid_path.write_text("not-a-pid")
        owner = self.new_lock()

        self.assertTrue(owner.try_acquire())
        self.assertEqual(self.lock_path.read_text(), str(os.getpid()))
        self.assertEqual(self.pid_path.read_text(), str(os.getpid()))
        owner.release()
        self.assertFalse(self.pid_path.exists())
        self.assertTrue(self.lock_path.exists())

    def test_partial_lock_record_writes_are_completed(self):
        owner = self.new_lock()
        original_write = os.write

        def write_one_byte(fd, data):
            return original_write(fd, data[:1])

        with mock.patch.object(supervisor.os, "write", side_effect=write_one_byte):
            self.assertTrue(owner.try_acquire())

        self.assertEqual(self.lock_path.read_text(), str(os.getpid()))
        self.assertEqual(self.pid_path.read_text(), str(os.getpid()))
        owner.release()
        self.assertFalse(self.pid_path.exists())
        self.assertEqual(self.lock_path.read_text(), "")

    def test_pid_marker_write_failure_releases_only_our_lock(self):
        owner = self.new_lock()
        original_write_text = Path.write_text

        def fail_pid_marker(path, data, *args, **kwargs):
            if path == self.pid_path:
                raise OSError("simulated marker write failure")
            return original_write_text(path, data, *args, **kwargs)

        with mock.patch.object(Path, "write_text", new=fail_pid_marker):
            self.assertFalse(owner.try_acquire())

        self.assertIsNone(owner.fd)
        self.assertIsNone(owner.owner_pid)
        self.assertTrue(self.lock_path.exists())
        self.assertEqual(self.lock_path.read_text(), "")
        self.assertFalse(self.pid_path.exists())

        next_owner = self.new_lock()
        self.assertTrue(next_owner.try_acquire())
        next_owner.release()

    def test_repeated_acquire_release_is_idempotent_and_keeps_inode(self):
        owner = self.new_lock()
        self.assertTrue(owner.try_acquire())
        inode = self.lock_path.stat().st_ino
        self.assertTrue(owner.try_acquire())
        owner.release()
        owner.release()

        self.assertTrue(self.lock_path.exists())
        self.assertEqual(self.lock_path.stat().st_ino, inode)
        self.assertFalse(self.pid_path.exists())

        next_owner = self.new_lock()
        self.assertTrue(next_owner.try_acquire())
        next_owner.release()


if __name__ == "__main__":
    unittest.main()
