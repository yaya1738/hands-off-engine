#!/usr/bin/env python3
"""
Hardware Interface Layer - Control Physical Devices

Provides unified interface for INTEGRAFIX to control:
- IoT devices (via MQTT, HTTP, etc.)
- Server hardware (GPIO, serial, USB)
- Network devices (switches, routers)
- Cloud infrastructure (servers, VMs)
- Trading hardware (display boards, indicators)

Architecture:
    INTEGRAFIX System
            ↓
    Hardware Interface
            ↓
    ┌───────┴────────┬──────────┬───────────┐
    ↓                ↓          ↓           ↓
  GPIO           Serial      Network     Cloud
 (Lights)       (Devices)   (Switches)  (Servers)
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum


STATE_FILE = Path(__file__).parent.parent / 'state' / 'hardware_interface.json'


class DeviceType(Enum):
    """Hardware device types."""
    GPIO = "gpio"                # GPIO pins (LEDs, buttons, sensors)
    SERIAL = "serial"            # Serial devices (Arduino, etc.)
    USB = "usb"                  # USB devices
    NETWORK = "network"          # Network devices (switches, routers)
    MQTT_IOT = "mqtt_iot"        # MQTT IoT devices
    HTTP_IOT = "http_iot"        # HTTP/REST IoT devices
    CLOUD_SERVER = "cloud"       # Cloud servers/VMs
    DISPLAY = "display"          # Display devices
    AUDIO = "audio"              # Audio output devices


class DeviceStatus(Enum):
    """Device status."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    UNKNOWN = "unknown"


class HardwareInterface:
    """
    Unified interface for hardware control.

    Provides abstraction layer for INTEGRAFIX to control any hardware
    without knowing implementation details.
    """

    def __init__(self):
        self.state = self.load_state()
        self.devices: Dict[str, Dict] = {}
        self.device_handlers: Dict[DeviceType, Any] = {}

        # Initialize device handlers
        self._init_handlers()

        # Discover available devices
        self.discover_devices()

    def load_state(self) -> dict:
        """Load interface state."""
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {
            'registered_devices': {},
            'total_commands': 0,
            'commands_by_device': {},
            'last_activity': None
        }

    def save_state(self):
        """Save interface state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    # ================================================================
    # DEVICE MANAGEMENT
    # ================================================================

    def register_device(
        self,
        device_id: str,
        device_type: DeviceType,
        config: Dict
    ):
        """
        Register hardware device.

        Args:
            device_id: Unique device identifier
            device_type: Type of device
            config: Device-specific configuration
        """
        self.devices[device_id] = {
            'type': device_type.value,
            'config': config,
            'status': DeviceStatus.UNKNOWN.value,
            'registered_at': datetime.now(timezone.utc).isoformat(),
            'last_command': None
        }

        self.state['registered_devices'][device_id] = {
            'type': device_type.value,
            'registered_at': datetime.now(timezone.utc).isoformat()
        }
        self.save_state()

        print(f"✓ Registered device: {device_id} ({device_type.value})")

    def discover_devices(self):
        """Auto-discover available hardware devices."""
        # GPIO devices (Raspberry Pi)
        if self._check_gpio_available():
            self.register_device(
                'gpio_status_led',
                DeviceType.GPIO,
                {'pin': 17, 'description': 'System status LED'}
            )

        # Serial devices
        serial_devices = self._discover_serial_devices()
        for device in serial_devices:
            self.register_device(
                f"serial_{device['port']}",
                DeviceType.SERIAL,
                device
            )

        # Cloud infrastructure (DigitalOcean droplet)
        self.register_device(
            'do_primary_server',
            DeviceType.CLOUD_SERVER,
            {'provider': 'digitalocean', 'droplet_id': 'self'}
        )

        # Virtual display (for status visualization)
        self.register_device(
            'status_display',
            DeviceType.DISPLAY,
            {'type': 'terminal', 'width': 80, 'height': 24}
        )

    # ================================================================
    # DEVICE CONTROL
    # ================================================================

    def send_command(
        self,
        device_id: str,
        command: str,
        params: Dict = None
    ) -> Dict:
        """
        Send command to hardware device.

        Args:
            device_id: Device identifier
            command: Command to execute
            params: Command parameters

        Returns:
            Result dict with success status
        """
        if device_id not in self.devices:
            return {'error': f'Device not found: {device_id}'}

        device = self.devices[device_id]
        device_type = DeviceType(device['type'])

        # Update stats
        self.state['total_commands'] += 1
        self.state['commands_by_device'][device_id] = \
            self.state['commands_by_device'].get(device_id, 0) + 1
        self.state['last_activity'] = datetime.now(timezone.utc).isoformat()
        self.save_state()

        # Route to appropriate handler
        handler = self.device_handlers.get(device_type)
        if not handler:
            return {'error': f'No handler for device type: {device_type.value}'}

        try:
            result = handler.send_command(device['config'], command, params or {})

            device['last_command'] = {
                'command': command,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'result': result
            }

            return result

        except Exception as e:
            return {'error': str(e)}

    def get_device_status(self, device_id: str) -> Dict:
        """Get current status of device."""
        if device_id not in self.devices:
            return {'error': f'Device not found: {device_id}'}

        device = self.devices[device_id]
        device_type = DeviceType(device['type'])

        handler = self.device_handlers.get(device_type)
        if handler and hasattr(handler, 'get_status'):
            return handler.get_status(device['config'])

        return {'status': device.get('status', 'unknown')}

    # ================================================================
    # DEVICE HANDLERS
    # ================================================================

    def _init_handlers(self):
        """Initialize device type handlers."""
        self.device_handlers[DeviceType.GPIO] = GPIOHandler()
        self.device_handlers[DeviceType.SERIAL] = SerialHandler()
        self.device_handlers[DeviceType.NETWORK] = NetworkHandler()
        self.device_handlers[DeviceType.MQTT_IOT] = MQTTHandler()
        self.device_handlers[DeviceType.HTTP_IOT] = HTTPIoTHandler()
        self.device_handlers[DeviceType.CLOUD_SERVER] = CloudServerHandler()
        self.device_handlers[DeviceType.DISPLAY] = DisplayHandler()
        self.device_handlers[DeviceType.AUDIO] = AudioHandler()

    def _check_gpio_available(self) -> bool:
        """Check if GPIO hardware is available."""
        # Check if running on Raspberry Pi or similar
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                return 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo
        except:
            return False

    def _discover_serial_devices(self) -> List[Dict]:
        """Discover serial devices."""
        devices = []

        # Check common serial ports
        import glob
        serial_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')

        for port in serial_ports:
            devices.append({
                'port': port,
                'description': f'Serial device on {port}'
            })

        return devices

    # ================================================================
    # HIGH-LEVEL CONTROL METHODS
    # ================================================================

    def set_status_indicator(self, status: str):
        """
        Set system status indicator.

        Args:
            status: 'running', 'trading', 'paused', 'error', 'idle'
        """
        # Update status LED if available
        if 'gpio_status_led' in self.devices:
            pattern = self._status_to_led_pattern(status)
            self.send_command('gpio_status_led', 'blink', {'pattern': pattern})

        # Update display if available
        if 'status_display' in self.devices:
            self.send_command('status_display', 'show_status', {'status': status})

    def alert_hardware(self, severity: str, message: str):
        """
        Trigger hardware alert.

        Args:
            severity: 'info', 'warning', 'critical'
            message: Alert message
        """
        # Visual alert (LED)
        if 'gpio_status_led' in self.devices:
            if severity == 'critical':
                self.send_command('gpio_status_led', 'flash', {'color': 'red'})

        # Audio alert
        if 'system_audio' in self.devices:
            self.send_command('system_audio', 'beep', {'count': 3 if severity == 'critical' else 1})

        # Display alert
        if 'status_display' in self.devices:
            self.send_command('status_display', 'show_alert', {
                'severity': severity,
                'message': message
            })

    def control_server(self, action: str):
        """
        Control cloud server.

        Args:
            action: 'reboot', 'shutdown', 'scale_up', 'scale_down'
        """
        if 'do_primary_server' in self.devices:
            return self.send_command('do_primary_server', action, {})

        return {'error': 'No server device available'}

    def _status_to_led_pattern(self, status: str) -> str:
        """Convert status to LED blink pattern."""
        patterns = {
            'running': 'steady_green',
            'trading': 'pulse_green',
            'paused': 'steady_yellow',
            'error': 'flash_red',
            'idle': 'dim_green'
        }
        return patterns.get(status, 'off')

    # ================================================================
    # STATISTICS
    # ================================================================

    def get_stats(self) -> Dict:
        """Get hardware interface statistics."""
        return {
            'registered_devices': len(self.devices),
            'devices_by_type': self._count_devices_by_type(),
            'total_commands': self.state['total_commands'],
            'commands_by_device': self.state['commands_by_device'],
            'last_activity': self.state['last_activity']
        }

    def _count_devices_by_type(self) -> Dict[str, int]:
        """Count devices by type."""
        counts = {}
        for device in self.devices.values():
            device_type = device['type']
            counts[device_type] = counts.get(device_type, 0) + 1
        return counts


# ================================================================
# DEVICE HANDLERS
# ================================================================

class GPIOHandler:
    """Handler for GPIO devices (Raspberry Pi pins, etc.)."""

    def send_command(self, config: Dict, command: str, params: Dict) -> Dict:
        """Control GPIO device."""
        # Check if GPIO library available
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)

            pin = config['pin']

            if command == 'on':
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)
                return {'success': True, 'state': 'on'}

            elif command == 'off':
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
                return {'success': True, 'state': 'off'}

            elif command == 'blink':
                pattern = params.get('pattern', 'steady')
                # Implementation would handle blink patterns
                return {'success': True, 'pattern': pattern}

            else:
                return {'error': f'Unknown command: {command}'}

        except ImportError:
            return {'error': 'GPIO library not available (not on Raspberry Pi)'}
        except Exception as e:
            return {'error': str(e)}


class SerialHandler:
    """Handler for serial devices."""

    def send_command(self, config: Dict, command: str, params: Dict) -> Dict:
        """Control serial device."""
        try:
            import serial

            port = config['port']
            baudrate = config.get('baudrate', 9600)

            with serial.Serial(port, baudrate, timeout=1) as ser:
                # Send command over serial
                cmd_str = f"{command}:{json.dumps(params)}\n"
                ser.write(cmd_str.encode())

                # Read response
                response = ser.readline().decode().strip()

                return {'success': True, 'response': response}

        except ImportError:
            return {'error': 'pyserial not available (pip install pyserial)'}
        except Exception as e:
            return {'error': str(e)}


class NetworkHandler:
    """Handler for network devices."""

    def send_command(self, config: Dict, command: str, params: Dict) -> Dict:
        """Control network device."""
        # Implementation would use SSH, SNMP, or device API
        return {'note': 'Network device control to be implemented'}


class MQTTHandler:
    """Handler for MQTT IoT devices."""

    def send_command(self, config: Dict, command: str, params: Dict) -> Dict:
        """Control MQTT device."""
        try:
            import paho.mqtt.client as mqtt

            broker = config.get('broker', 'localhost')
            port = config.get('port', 1883)
            topic = config['topic']

            client = mqtt.Client()
            client.connect(broker, port, 60)

            # Publish command
            payload = json.dumps({'command': command, 'params': params})
            client.publish(topic, payload)

            client.disconnect()

            return {'success': True}

        except ImportError:
            return {'error': 'paho-mqtt not available (pip install paho-mqtt)'}
        except Exception as e:
            return {'error': str(e)}


class HTTPIoTHandler:
    """Handler for HTTP/REST IoT devices."""

    def send_command(self, config: Dict, command: str, params: Dict) -> Dict:
        """Control HTTP IoT device."""
        try:
            import requests

            url = config['url']
            method = config.get('method', 'POST')

            payload = {'command': command, 'params': params}

            if method == 'POST':
                response = requests.post(url, json=payload, timeout=10)
            elif method == 'GET':
                response = requests.get(url, params=payload, timeout=10)
            else:
                return {'error': f'Unknown HTTP method: {method}'}

            return {
                'success': response.status_code == 200,
                'response': response.json() if response.headers.get('content-type') == 'application/json' else response.text
            }

        except Exception as e:
            return {'error': str(e)}


class CloudServerHandler:
    """Handler for cloud servers/VMs."""

    def send_command(self, config: Dict, command: str, params: Dict) -> Dict:
        """Control cloud server."""
        provider = config.get('provider')

        if provider == 'digitalocean':
            return self._control_digitalocean(config, command, params)
        elif provider == 'aws':
            return self._control_aws(config, command, params)
        else:
            return {'error': f'Unknown cloud provider: {provider}'}

    def _control_digitalocean(self, config: Dict, command: str, params: Dict) -> Dict:
        """Control DigitalOcean droplet."""
        # Would use DigitalOcean API
        return {'note': 'DigitalOcean control to be implemented'}

    def _control_aws(self, config: Dict, command: str, params: Dict) -> Dict:
        """Control AWS instance."""
        # Would use boto3
        return {'note': 'AWS control to be implemented'}


class DisplayHandler:
    """Handler for display devices."""

    def send_command(self, config: Dict, command: str, params: Dict) -> Dict:
        """Control display device."""
        if config['type'] == 'terminal':
            # Terminal display
            if command == 'show_status':
                status = params.get('status', 'unknown')
                print(f"\n[STATUS] {status.upper()}\n")
                return {'success': True}

            elif command == 'show_alert':
                severity = params.get('severity', 'info')
                message = params.get('message', '')
                print(f"\n[{severity.upper()}] {message}\n")
                return {'success': True}

        return {'note': 'Display control to be implemented'}


class AudioHandler:
    """Handler for audio devices."""

    def send_command(self, config: Dict, command: str, params: Dict) -> Dict:
        """Control audio device."""
        if command == 'beep':
            # System beep
            import os
            count = params.get('count', 1)
            for _ in range(count):
                os.system('printf "\a"')
                time.sleep(0.2)
            return {'success': True}

        return {'note': 'Audio control to be implemented'}


# ================================================================
# CONVENIENCE FUNCTIONS
# ================================================================

_interface_instance = None

def get_interface() -> HardwareInterface:
    """Get singleton hardware interface."""
    global _interface_instance
    if _interface_instance is None:
        _interface_instance = HardwareInterface()
    return _interface_instance


def control_device(device_id: str, command: str, params: Dict = None) -> Dict:
    """Control hardware device."""
    interface = get_interface()
    return interface.send_command(device_id, command, params or {})


def set_status(status: str):
    """Set system status indicator."""
    interface = get_interface()
    interface.set_status_indicator(status)


def hardware_alert(severity: str, message: str):
    """Trigger hardware alert."""
    interface = get_interface()
    interface.alert_hardware(severity, message)


# ================================================================
# TESTING
# ================================================================

def test_hardware_interface():
    """Test hardware interface."""
    print("="*60)
    print("HARDWARE INTERFACE TEST")
    print("="*60)
    print()

    interface = get_interface()

    print(f"Discovered {len(interface.devices)} devices:")
    for device_id, device in interface.devices.items():
        print(f"  • {device_id} ({device['type']})")
    print()

    # Test status indicator
    print("Testing status indicator...")
    interface.set_status_indicator('running')
    time.sleep(1)

    # Test alert
    print("Testing hardware alert...")
    interface.alert_hardware('info', 'Test alert from INTEGRAFIX')

    # Statistics
    print()
    print("Statistics:")
    stats = interface.get_stats()
    print(f"  Devices: {stats['registered_devices']}")
    print(f"  Commands: {stats['total_commands']}")

    print()
    print("="*60)


def main():
    """Run hardware interface."""
    import sys

    if '--test' in sys.argv:
        test_hardware_interface()
    elif '--stats' in sys.argv:
        interface = get_interface()
        stats = interface.get_stats()
        print(json.dumps(stats, indent=2))
    else:
        print("Hardware Interface")
        print()
        print("Usage:")
        print("  --test   Test hardware interface")
        print("  --stats  Show statistics")


if __name__ == '__main__':
    main()
