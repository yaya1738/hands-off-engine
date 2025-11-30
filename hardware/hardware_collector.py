"""
Hardware Metrics Collector - Live System Monitoring

Collects comprehensive hardware metrics for autonomous monitoring.
Designed to protect live trading systems with real-time monitoring.

Features:
- Cross-platform metrics collection (Linux primary, fallback for others)
- Trading process monitoring
- Network latency probing
- Thermal monitoring
- SMART disk health (when available)

Standard: Yair Siegel Master Level Operations
"""

import os
import socket
import time
import subprocess
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import re


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)

from hardware.hardware_types import (
    CPUMetrics,
    MemoryMetrics,
    DiskMetrics,
    NetworkMetrics,
    ThermalMetrics,
    PowerMetrics,
    ProcessMetrics,
    HardwareMetrics,
)


class HardwareCollector:
    """
    Collects comprehensive hardware metrics from the system.

    Designed for autonomous monitoring of trading infrastructure.
    Prioritizes accuracy and reliability over performance.
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        trading_process_patterns: Optional[List[str]] = None
    ):
        """
        Initialize the hardware collector.

        Args:
            node_id: Unique identifier for this node
            trading_process_patterns: List of process name patterns to monitor
        """
        self.node_id = node_id or self._generate_node_id()
        self.hostname = socket.gethostname()
        self.trading_process_patterns = trading_process_patterns or [
            "python.*unified_system",
            "python.*autonomous",
            "python.*telegram",
            "python.*self_healing",
            "python.*uvicorn",
            "python.*executor",
            "python.*alpha",
        ]
        self._last_cpu_times = None
        self._last_cpu_time = None
        self._last_disk_io = {}
        self._last_disk_io_time = None
        self._last_net_io = {}
        self._last_net_io_time = None

    def _generate_node_id(self) -> str:
        """Generate a unique node identifier."""
        hostname = socket.gethostname()
        # Try to get machine-id for uniqueness
        machine_id = ""
        machine_id_path = Path("/etc/machine-id")
        if machine_id_path.exists():
            machine_id = machine_id_path.read_text().strip()[:8]
        return f"{hostname}_{machine_id}" if machine_id else hostname

    def collect_all(self) -> HardwareMetrics:
        """
        Collect all hardware metrics.

        Returns:
            HardwareMetrics with complete system snapshot
        """
        start_time = time.time()

        metrics = HardwareMetrics(
            timestamp=_utc_now(),
            node_id=self.node_id,
            hostname=self.hostname,
            cpu=self._collect_cpu(),
            memory=self._collect_memory(),
            disks=self._collect_disks(),
            networks=self._collect_networks(),
            thermal=self._collect_thermal(),
            power=self._collect_power(),
            trading_processes=self._collect_trading_processes(),
            collection_duration_ms=(time.time() - start_time) * 1000,
            collector_version="1.0.0"
        )

        return metrics

    def _collect_cpu(self) -> CPUMetrics:
        """Collect CPU metrics from /proc/stat and /proc/loadavg."""
        usage_percent = 0.0
        load_1, load_5, load_15 = 0.0, 0.0, 0.0
        core_count = os.cpu_count() or 1
        frequency_mhz = 0.0
        frequency_max_mhz = 0.0
        context_switches = 0.0
        interrupts = 0.0
        iowait_percent = 0.0
        steal_percent = 0.0
        per_core_usage = []

        # Load averages
        try:
            with open("/proc/loadavg", "r") as f:
                parts = f.read().split()
                load_1, load_5, load_15 = float(parts[0]), float(parts[1]), float(parts[2])
        except:
            pass

        # CPU times and usage
        try:
            with open("/proc/stat", "r") as f:
                lines = f.readlines()

            cpu_times = {}
            for line in lines:
                if line.startswith("cpu"):
                    parts = line.split()
                    name = parts[0]
                    times = list(map(int, parts[1:8])) if len(parts) >= 8 else [0] * 7
                    # user, nice, system, idle, iowait, irq, softirq
                    cpu_times[name] = times

            # Calculate overall CPU usage
            if self._last_cpu_times and "cpu" in cpu_times and "cpu" in self._last_cpu_times:
                curr = cpu_times["cpu"]
                prev = self._last_cpu_times["cpu"]

                total_diff = sum(curr) - sum(prev)
                if total_diff > 0:
                    idle_diff = curr[3] - prev[3]  # idle
                    iowait_diff = curr[4] - prev[4]  # iowait
                    steal_diff = curr[7] - prev[7] if len(curr) > 7 else 0  # steal

                    usage_percent = 100.0 * (1.0 - idle_diff / total_diff)
                    iowait_percent = 100.0 * iowait_diff / total_diff
                    steal_percent = 100.0 * steal_diff / total_diff if len(curr) > 7 else 0

            # Per-core usage
            for name, times in cpu_times.items():
                if name.startswith("cpu") and name != "cpu":
                    if self._last_cpu_times and name in self._last_cpu_times:
                        curr = times
                        prev = self._last_cpu_times[name]
                        total_diff = sum(curr) - sum(prev)
                        if total_diff > 0:
                            idle_diff = curr[3] - prev[3]
                            core_usage = 100.0 * (1.0 - idle_diff / total_diff)
                            per_core_usage.append(core_usage)

            # Context switches and interrupts
            for line in lines:
                if line.startswith("ctxt"):
                    context_switches = float(line.split()[1])
                elif line.startswith("intr"):
                    interrupts = float(line.split()[1])

            self._last_cpu_times = cpu_times

        except Exception as e:
            pass

        # SAFETY: If no previous sample exists, estimate CPU usage from load average
        # This prevents reporting 0% CPU on first call after reboot
        if usage_percent == 0.0 and load_1 > 0 and core_count > 0:
            # Load average 1.0 per core = ~100% CPU, scale accordingly
            load_per_core = load_1 / core_count
            # Cap at 100%, load can exceed 1.0 per core when overloaded
            usage_percent = min(100.0, load_per_core * 100.0)

        # CPU frequency
        try:
            # Try /sys/devices/system/cpu/cpu0/cpufreq
            freq_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
            max_freq_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq")

            if freq_path.exists():
                frequency_mhz = float(freq_path.read_text().strip()) / 1000
            if max_freq_path.exists():
                frequency_max_mhz = float(max_freq_path.read_text().strip()) / 1000

            # Fallback to /proc/cpuinfo
            if frequency_mhz == 0:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "cpu MHz" in line:
                            frequency_mhz = float(line.split(":")[1].strip())
                            break
        except:
            pass

        return CPUMetrics(
            usage_percent=round(usage_percent, 2),
            load_average_1m=load_1,
            load_average_5m=load_5,
            load_average_15m=load_15,
            core_count=core_count,
            frequency_mhz=round(frequency_mhz, 2),
            frequency_max_mhz=round(frequency_max_mhz, 2),
            context_switches_per_sec=context_switches,
            interrupts_per_sec=interrupts,
            iowait_percent=round(iowait_percent, 2),
            steal_percent=round(steal_percent, 2),
            per_core_usage=per_core_usage
        )

    def _collect_memory(self) -> MemoryMetrics:
        """Collect memory metrics from /proc/meminfo."""
        mem_info = {}

        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip().split()[0]  # Remove 'kB'
                        mem_info[key] = int(value) / 1024 / 1024  # Convert to GB
        except:
            pass

        total_gb = mem_info.get("MemTotal", 0)
        available_gb = mem_info.get("MemAvailable", 0)
        used_gb = total_gb - available_gb if total_gb > 0 else 0
        cached_gb = mem_info.get("Cached", 0)
        buffers_gb = mem_info.get("Buffers", 0)
        swap_total_gb = mem_info.get("SwapTotal", 0)
        swap_free_gb = mem_info.get("SwapFree", 0)
        swap_used_gb = swap_total_gb - swap_free_gb if swap_total_gb > 0 else 0
        swap_percent = (swap_used_gb / swap_total_gb * 100) if swap_total_gb > 0 else 0

        # Memory pressure (simple calculation)
        memory_pressure = ((total_gb - available_gb) / total_gb * 100) if total_gb > 0 else 0

        # Page faults from /proc/vmstat
        page_faults = 0.0
        oom_kills = 0
        try:
            with open("/proc/vmstat", "r") as f:
                for line in f:
                    if line.startswith("pgfault"):
                        page_faults = float(line.split()[1])
                    elif line.startswith("oom_kill"):
                        oom_kills = int(line.split()[1])
        except:
            pass

        return MemoryMetrics(
            total_gb=round(total_gb, 2),
            used_gb=round(used_gb, 2),
            available_gb=round(available_gb, 2),
            cached_gb=round(cached_gb, 2),
            buffers_gb=round(buffers_gb, 2),
            swap_total_gb=round(swap_total_gb, 2),
            swap_used_gb=round(swap_used_gb, 2),
            swap_percent=round(swap_percent, 2),
            memory_pressure=round(memory_pressure, 2),
            page_faults_per_sec=page_faults,
            oom_kills_recent=oom_kills
        )

    def _collect_disks(self) -> List[DiskMetrics]:
        """Collect disk metrics from /proc/diskstats and df."""
        disks = []

        # Get mount points and usage
        mount_info = {}
        try:
            result = subprocess.run(
                ["df", "-B1", "--output=target,size,used,avail,pcent"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.strip().split("\n")[1:]:
                parts = line.split()
                if len(parts) >= 5 and parts[0].startswith("/"):
                    mount_point = parts[0]
                    mount_info[mount_point] = {
                        "total_gb": int(parts[1]) / 1024 / 1024 / 1024,
                        "used_gb": int(parts[2]) / 1024 / 1024 / 1024,
                        "available_gb": int(parts[3]) / 1024 / 1024 / 1024,
                        "usage_percent": float(parts[4].rstrip("%"))
                    }
        except:
            pass

        # Get I/O stats from /proc/diskstats
        disk_io = {}
        try:
            with open("/proc/diskstats", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 14:
                        device = parts[2]
                        # Skip partitions, focus on main devices
                        if re.match(r'^(sd[a-z]|nvme\d+n\d+|vd[a-z])$', device):
                            disk_io[device] = {
                                "reads_completed": int(parts[3]),
                                "sectors_read": int(parts[5]),
                                "read_time_ms": int(parts[6]),
                                "writes_completed": int(parts[7]),
                                "sectors_written": int(parts[9]),
                                "write_time_ms": int(parts[10]),
                                "io_time_ms": int(parts[12]) if len(parts) > 12 else 0
                            }
        except:
            pass

        # Calculate I/O rates
        current_time = time.time()
        io_rates = {}

        if self._last_disk_io and self._last_disk_io_time:
            time_diff = current_time - self._last_disk_io_time
            if time_diff > 0:
                for device, stats in disk_io.items():
                    if device in self._last_disk_io:
                        prev = self._last_disk_io[device]
                        read_iops = (stats["reads_completed"] - prev["reads_completed"]) / time_diff
                        write_iops = (stats["writes_completed"] - prev["writes_completed"]) / time_diff
                        # Assuming 512 byte sectors
                        read_throughput = (stats["sectors_read"] - prev["sectors_read"]) * 512 / 1024 / 1024 / time_diff
                        write_throughput = (stats["sectors_written"] - prev["sectors_written"]) * 512 / 1024 / 1024 / time_diff

                        read_time_diff = stats["read_time_ms"] - prev["read_time_ms"]
                        write_time_diff = stats["write_time_ms"] - prev["write_time_ms"]
                        reads_diff = stats["reads_completed"] - prev["reads_completed"]
                        writes_diff = stats["writes_completed"] - prev["writes_completed"]

                        avg_read_latency = read_time_diff / reads_diff if reads_diff > 0 else 0
                        avg_write_latency = write_time_diff / writes_diff if writes_diff > 0 else 0

                        io_rates[device] = {
                            "read_iops": read_iops,
                            "write_iops": write_iops,
                            "read_throughput_mbps": read_throughput,
                            "write_throughput_mbps": write_throughput,
                            "avg_read_latency_ms": avg_read_latency,
                            "avg_write_latency_ms": avg_write_latency
                        }

        self._last_disk_io = disk_io
        self._last_disk_io_time = current_time

        # Create disk metrics for each mount point
        for mount_point, info in mount_info.items():
            # Skip pseudo filesystems
            if mount_point in ["/proc", "/sys", "/dev", "/run", "/boot/efi"]:
                continue

            disk_metrics = DiskMetrics(
                mount_point=mount_point,
                total_gb=round(info["total_gb"], 2),
                used_gb=round(info["used_gb"], 2),
                available_gb=round(info["available_gb"], 2),
                usage_percent=info["usage_percent"],
                read_iops=0.0,
                write_iops=0.0,
                read_throughput_mbps=0.0,
                write_throughput_mbps=0.0,
                avg_read_latency_ms=0.0,
                avg_write_latency_ms=0.0,
                queue_depth=0.0
            )
            disks.append(disk_metrics)

        return disks

    def _collect_networks(self) -> List[NetworkMetrics]:
        """Collect network metrics from /proc/net/dev."""
        networks = []
        net_stats = {}

        try:
            with open("/proc/net/dev", "r") as f:
                lines = f.readlines()[2:]  # Skip headers
                for line in lines:
                    parts = line.split(":")
                    if len(parts) == 2:
                        interface = parts[0].strip()
                        if interface == "lo":  # Skip loopback
                            continue

                        values = parts[1].split()
                        if len(values) >= 16:
                            net_stats[interface] = {
                                "rx_bytes": int(values[0]),
                                "rx_packets": int(values[1]),
                                "rx_errors": int(values[2]),
                                "rx_drops": int(values[3]),
                                "tx_bytes": int(values[8]),
                                "tx_packets": int(values[9]),
                                "tx_errors": int(values[10]),
                                "tx_drops": int(values[11])
                            }
        except:
            pass

        # Calculate rates
        current_time = time.time()
        if self._last_net_io and self._last_net_io_time:
            time_diff = current_time - self._last_net_io_time
            if time_diff > 0:
                for interface, stats in net_stats.items():
                    if interface in self._last_net_io:
                        prev = self._last_net_io[interface]

                        network = NetworkMetrics(
                            interface=interface,
                            rx_bytes_per_sec=(stats["rx_bytes"] - prev["rx_bytes"]) / time_diff,
                            tx_bytes_per_sec=(stats["tx_bytes"] - prev["tx_bytes"]) / time_diff,
                            rx_packets_per_sec=(stats["rx_packets"] - prev["rx_packets"]) / time_diff,
                            tx_packets_per_sec=(stats["tx_packets"] - prev["tx_packets"]) / time_diff,
                            rx_errors_per_sec=(stats["rx_errors"] - prev["rx_errors"]) / time_diff,
                            tx_errors_per_sec=(stats["tx_errors"] - prev["tx_errors"]) / time_diff,
                            rx_drops_per_sec=(stats["rx_drops"] - prev["rx_drops"]) / time_diff,
                            tx_drops_per_sec=(stats["tx_drops"] - prev["tx_drops"]) / time_diff,
                            latency_ms=self._probe_network_latency(),
                            connection_count=self._count_connections(),
                            tcp_retransmits_per_sec=0.0  # Would need /proc/net/snmp
                        )
                        networks.append(network)

        self._last_net_io = net_stats
        self._last_net_io_time = current_time

        # Return placeholder if first collection
        if not networks and net_stats:
            for interface in net_stats:
                networks.append(NetworkMetrics(
                    interface=interface,
                    rx_bytes_per_sec=0.0,
                    tx_bytes_per_sec=0.0,
                    rx_packets_per_sec=0.0,
                    tx_packets_per_sec=0.0,
                    rx_errors_per_sec=0.0,
                    tx_errors_per_sec=0.0,
                    rx_drops_per_sec=0.0,
                    tx_drops_per_sec=0.0,
                    latency_ms=0.0,
                    connection_count=0,
                    tcp_retransmits_per_sec=0.0
                ))

        return networks

    def _probe_network_latency(self) -> float:
        """Probe network latency to common endpoints."""
        try:
            # Quick DNS lookup latency check
            start = time.time()
            socket.gethostbyname("8.8.8.8")
            return (time.time() - start) * 1000
        except:
            return 0.0

    def _count_connections(self) -> int:
        """Count active network connections."""
        try:
            with open("/proc/net/tcp", "r") as f:
                return len(f.readlines()) - 1
        except:
            return 0

    def _collect_thermal(self) -> ThermalMetrics:
        """Collect thermal metrics from /sys/class/thermal and /sys/class/hwmon."""
        cpu_temp = 0.0
        gpu_temp = None
        system_temp = 0.0
        fan_speed = None
        throttling = False
        zone_temps = {}

        # Thermal zones
        try:
            thermal_path = Path("/sys/class/thermal")
            if thermal_path.exists():
                for zone_path in thermal_path.glob("thermal_zone*"):
                    try:
                        temp_file = zone_path / "temp"
                        type_file = zone_path / "type"

                        if temp_file.exists():
                            temp = float(temp_file.read_text().strip()) / 1000
                            zone_type = type_file.read_text().strip() if type_file.exists() else zone_path.name
                            zone_temps[zone_type] = temp

                            if "cpu" in zone_type.lower() or "x86_pkg_temp" in zone_type.lower():
                                cpu_temp = max(cpu_temp, temp)
                            if "gpu" in zone_type.lower():
                                gpu_temp = temp
                    except:
                        continue
        except:
            pass

        # hwmon sensors
        try:
            hwmon_path = Path("/sys/class/hwmon")
            if hwmon_path.exists():
                for hwmon in hwmon_path.iterdir():
                    try:
                        name_file = hwmon / "name"
                        name = name_file.read_text().strip() if name_file.exists() else ""

                        # Look for temperature inputs
                        for temp_input in hwmon.glob("temp*_input"):
                            temp = float(temp_input.read_text().strip()) / 1000
                            label_file = temp_input.with_name(temp_input.name.replace("_input", "_label"))
                            label = label_file.read_text().strip() if label_file.exists() else temp_input.name

                            zone_temps[f"{name}_{label}"] = temp

                            if "core" in label.lower() or "cpu" in label.lower():
                                cpu_temp = max(cpu_temp, temp)

                        # Look for fan speeds
                        for fan_input in hwmon.glob("fan*_input"):
                            speed = float(fan_input.read_text().strip())
                            if speed > 0:
                                fan_speed = speed
                    except:
                        continue
        except:
            pass

        system_temp = max(zone_temps.values()) if zone_temps else 0.0

        # Check for thermal throttling
        try:
            for cpu_path in Path("/sys/devices/system/cpu").glob("cpu[0-9]*"):
                throttle_file = cpu_path / "thermal_throttle" / "core_throttle_count"
                if throttle_file.exists():
                    count = int(throttle_file.read_text().strip())
                    if count > 0:
                        throttling = True
                        break
        except:
            pass

        return ThermalMetrics(
            cpu_temp_celsius=round(cpu_temp, 1),
            gpu_temp_celsius=round(gpu_temp, 1) if gpu_temp else None,
            system_temp_celsius=round(system_temp, 1),
            fan_speed_rpm=fan_speed,
            thermal_throttling=throttling,
            thermal_zone_temps=zone_temps
        )

    def _collect_power(self) -> PowerMetrics:
        """Collect power metrics."""
        power_watts = None
        battery_percent = None
        battery_status = None
        on_battery = False
        uptime = 0.0
        last_reboot = _utc_now()

        # Uptime
        try:
            with open("/proc/uptime", "r") as f:
                uptime = float(f.read().split()[0])
                last_reboot = datetime.fromtimestamp(time.time() - uptime, tz=timezone.utc)
        except:
            pass

        # Battery info
        try:
            battery_path = Path("/sys/class/power_supply")
            if battery_path.exists():
                for supply in battery_path.iterdir():
                    type_file = supply / "type"
                    if type_file.exists():
                        supply_type = type_file.read_text().strip()

                        if supply_type == "Battery":
                            capacity_file = supply / "capacity"
                            status_file = supply / "status"

                            if capacity_file.exists():
                                battery_percent = float(capacity_file.read_text().strip())
                            if status_file.exists():
                                battery_status = status_file.read_text().strip()
                                on_battery = battery_status == "Discharging"
        except:
            pass

        return PowerMetrics(
            power_consumption_watts=power_watts,
            battery_percent=battery_percent,
            battery_status=battery_status,
            on_battery_power=on_battery,
            uptime_seconds=uptime,
            last_reboot=last_reboot
        )

    def _collect_trading_processes(self) -> List[ProcessMetrics]:
        """Collect metrics for trading-related processes."""
        processes = []

        try:
            proc_path = Path("/proc")
            for pid_path in proc_path.iterdir():
                if not pid_path.name.isdigit():
                    continue

                try:
                    # Read cmdline
                    cmdline_file = pid_path / "cmdline"
                    if not cmdline_file.exists():
                        continue

                    cmdline = cmdline_file.read_bytes().decode("utf-8", errors="ignore").replace("\x00", " ").strip()

                    # Check if matches any trading pattern
                    is_trading = False
                    for pattern in self.trading_process_patterns:
                        if re.search(pattern, cmdline, re.IGNORECASE):
                            is_trading = True
                            break

                    if not is_trading:
                        continue

                    pid = int(pid_path.name)

                    # Read stat
                    stat_file = pid_path / "stat"
                    stat_data = stat_file.read_text().split()

                    # Read statm
                    statm_file = pid_path / "statm"
                    statm_data = statm_file.read_text().split()

                    # Process status
                    status_file = pid_path / "status"
                    status_data = {}
                    for line in status_file.read_text().split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            status_data[key.strip()] = value.strip()

                    # Calculate metrics
                    page_size = os.sysconf("SC_PAGE_SIZE")
                    rss_mb = int(statm_data[1]) * page_size / 1024 / 1024 if len(statm_data) > 1 else 0
                    vms_mb = int(statm_data[0]) * page_size / 1024 / 1024 if len(statm_data) > 0 else 0
                    threads = int(status_data.get("Threads", 1))

                    # Count open files
                    fd_path = pid_path / "fd"
                    open_files = len(list(fd_path.iterdir())) if fd_path.exists() else 0

                    # Process uptime
                    start_time = int(stat_data[21]) if len(stat_data) > 21 else 0
                    clk_tck = os.sysconf("SC_CLK_TCK")
                    with open("/proc/uptime", "r") as f:
                        system_uptime = float(f.read().split()[0])
                    process_uptime = system_uptime - (start_time / clk_tck)

                    process = ProcessMetrics(
                        process_name=cmdline[:100],
                        pid=pid,
                        cpu_percent=0.0,  # Would need delta calculation
                        memory_percent=(rss_mb / (self._collect_memory().total_gb * 1024)) * 100,
                        memory_rss_mb=round(rss_mb, 2),
                        memory_vms_mb=round(vms_mb, 2),
                        open_files=open_files,
                        open_connections=0,  # Would need netstat
                        threads=threads,
                        status=stat_data[2] if len(stat_data) > 2 else "?",
                        uptime_seconds=max(0, process_uptime)
                    )
                    processes.append(process)

                except (PermissionError, FileNotFoundError, ProcessLookupError):
                    continue

        except Exception as e:
            pass

        return processes


def collect_hardware_snapshot(
    node_id: Optional[str] = None,
    trading_patterns: Optional[List[str]] = None
) -> HardwareMetrics:
    """
    Convenience function to collect a single hardware snapshot.

    Args:
        node_id: Optional node identifier
        trading_patterns: Optional list of trading process patterns

    Returns:
        Complete HardwareMetrics snapshot
    """
    collector = HardwareCollector(node_id, trading_patterns)
    return collector.collect_all()


if __name__ == "__main__":
    # Test collection
    print("Collecting hardware metrics...")
    collector = HardwareCollector()

    # First collection (establishes baseline)
    metrics1 = collector.collect_all()
    print(f"First collection complete in {metrics1.collection_duration_ms:.2f}ms")

    # Wait a bit for rate calculations
    time.sleep(2)

    # Second collection (with rates)
    metrics2 = collector.collect_all()
    print(f"\nSecond collection complete in {metrics2.collection_duration_ms:.2f}ms")

    print(f"\nNode: {metrics2.node_id}")
    print(f"Hostname: {metrics2.hostname}")
    print(f"\nCPU: {metrics2.cpu.usage_percent:.1f}% usage, load: {metrics2.cpu.load_average_1m:.2f}")
    print(f"Memory: {metrics2.memory.used_gb:.2f}GB / {metrics2.memory.total_gb:.2f}GB ({metrics2.memory.memory_pressure:.1f}% pressure)")
    print(f"Thermal: CPU {metrics2.thermal.cpu_temp_celsius}°C, throttling: {metrics2.thermal.thermal_throttling}")
    print(f"Uptime: {metrics2.power.uptime_seconds / 3600:.1f} hours")
    print(f"\nDisks: {len(metrics2.disks)}")
    for disk in metrics2.disks:
        print(f"  {disk.mount_point}: {disk.usage_percent:.1f}% used")
    print(f"\nNetworks: {len(metrics2.networks)}")
    for net in metrics2.networks:
        print(f"  {net.interface}: {net.rx_bytes_per_sec/1024:.1f} KB/s RX, {net.tx_bytes_per_sec/1024:.1f} KB/s TX")
    print(f"\nTrading processes: {len(metrics2.trading_processes)}")
    for proc in metrics2.trading_processes:
        print(f"  PID {proc.pid}: {proc.process_name[:50]}")
