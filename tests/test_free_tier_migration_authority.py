import ast
from pathlib import Path

SOURCE = Path("autonomous/free_tier_migration.py").read_text()
TREE = ast.parse(SOURCE)


def test_no_process_execution_or_generated_file_write():
    text = SOURCE
    assert "os.system" not in text
    assert "subprocess" not in text
    assert "pip install" not in text
    assert "provider_file.write_text" not in text


def test_run_migration_fails_closed():
    namespace = {"__name__": "free_tier_migration_test"}
    exec(compile(SOURCE, "autonomous/free_tier_migration.py", "exec"), namespace)
    migration = namespace["FreeTierMigration"]()
    assert migration.run_migration() is False
    assert migration.state["migration_status"] == "blocked_authority_boundary"
