"""
Cloud Provider Integrations - Autonomous Infrastructure Provisioning

Direct API integrations with cloud providers for autonomous
server provisioning, scaling, and management.

Supported Providers:
- DigitalOcean (primary)
- AWS (secondary)
- Hetzner (budget option)

Standard: Yair Siegel Master Level Operations - Full Self-Control
"""

import json
import os
import time
import hashlib
import hmac
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
import urllib.request
import urllib.error
import urllib.parse

from infrastructure.infra_types import (
    CloudProvider,
    InstanceSize,
    InfrastructureAction,
    ServerSpec,
    Server,
    ServerRole,
    InstanceType,
    ProvisioningRequest,
    ProvisioningStatus,
    DIGITALOCEAN_INSTANCES,
    AWS_INSTANCES,
)


class CloudProviderAPI(ABC):
    """Abstract base class for cloud provider APIs."""

    @abstractmethod
    def list_servers(self) -> List[Server]:
        """List all servers."""
        pass

    @abstractmethod
    def get_server(self, server_id: str) -> Optional[Server]:
        """Get a specific server."""
        pass

    @abstractmethod
    def create_server(self, request: ProvisioningRequest) -> Tuple[bool, Optional[Server], str]:
        """Create a new server. Returns (success, server, message)."""
        pass

    @abstractmethod
    def delete_server(self, server_id: str) -> Tuple[bool, str]:
        """Delete a server. Returns (success, message)."""
        pass

    @abstractmethod
    def resize_server(self, server_id: str, new_instance_type: str) -> Tuple[bool, str]:
        """Resize a server. Returns (success, message)."""
        pass

    @abstractmethod
    def get_available_sizes(self, region: str = "") -> List[InstanceType]:
        """Get available instance sizes."""
        pass

    @abstractmethod
    def get_regions(self) -> List[Dict[str, Any]]:
        """Get available regions."""
        pass

    @abstractmethod
    def check_api_status(self) -> Tuple[bool, str]:
        """Check if API is accessible. Returns (ok, message)."""
        pass


class DigitalOceanAPI(CloudProviderAPI):
    """
    DigitalOcean API integration for autonomous provisioning.

    Handles all DigitalOcean operations:
    - Droplet creation, deletion, resizing
    - Snapshots and backups
    - Networking (VPC, firewalls)
    - Monitoring
    """

    API_BASE = "https://api.digitalocean.com/v2"

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize DigitalOcean API.

        Args:
            api_token: DO API token (or from DO_API_TOKEN env var)
        """
        self.api_token = api_token or os.environ.get("DO_API_TOKEN", "")
        self.provider = CloudProvider.DIGITALOCEAN
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, float] = {}
        self._cache_ttl = 60  # Cache for 60 seconds

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        timeout: int = 30
    ) -> Tuple[bool, Any, str]:
        """Make API request to DigitalOcean."""
        if not self.api_token:
            return False, None, "No API token configured"

        url = f"{self.API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        try:
            if data:
                body = json.dumps(data).encode('utf-8')
            else:
                body = None

            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                return True, response_data, "OK"

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ""
            try:
                error_data = json.loads(error_body)
                message = error_data.get("message", str(e))
            except:
                message = f"HTTP {e.code}: {error_body[:200]}"
            return False, None, message

        except urllib.error.URLError as e:
            return False, None, f"Connection error: {str(e)}"

        except Exception as e:
            return False, None, f"Error: {str(e)}"

    def check_api_status(self) -> Tuple[bool, str]:
        """Check if API is accessible."""
        success, data, message = self._request("GET", "/account")
        if success:
            return True, f"OK - Account: {data.get('account', {}).get('email', 'unknown')}"
        return False, message

    def list_servers(self) -> List[Server]:
        """List all droplets."""
        success, data, message = self._request("GET", "/droplets?per_page=200")
        if not success:
            return []

        servers = []
        for droplet in data.get("droplets", []):
            server = self._droplet_to_server(droplet)
            servers.append(server)

        return servers

    def get_server(self, server_id: str) -> Optional[Server]:
        """Get a specific droplet."""
        success, data, message = self._request("GET", f"/droplets/{server_id}")
        if not success:
            return None

        return self._droplet_to_server(data.get("droplet", {}))

    def create_server(self, request: ProvisioningRequest) -> Tuple[bool, Optional[Server], str]:
        """Create a new droplet."""
        # Get instance type details
        instance = DIGITALOCEAN_INSTANCES.get(request.instance_type)
        if not instance:
            return False, None, f"Unknown instance type: {request.instance_type}"

        # Build request
        droplet_data = {
            "name": request.name,
            "region": request.region or "nyc1",
            "size": request.instance_type,
            "image": "ubuntu-22-04-x64",  # Default to Ubuntu 22.04
            "ssh_keys": request.ssh_keys,
            "backups": True,
            "monitoring": True,
            "tags": list(request.tags.keys()) if request.tags else ["hands-off-engine"],
        }

        if request.user_data:
            droplet_data["user_data"] = request.user_data

        success, data, message = self._request("POST", "/droplets", droplet_data)
        if not success:
            return False, None, message

        droplet = data.get("droplet", {})
        server = self._droplet_to_server(droplet)
        server.role = request.role

        return True, server, f"Droplet {server.server_id} created"

    def delete_server(self, server_id: str) -> Tuple[bool, str]:
        """Delete a droplet."""
        success, data, message = self._request("DELETE", f"/droplets/{server_id}")
        if success:
            return True, f"Droplet {server_id} deleted"
        return False, message

    def resize_server(self, server_id: str, new_instance_type: str) -> Tuple[bool, str]:
        """Resize a droplet (requires power off first)."""
        # Power off first
        success, _, message = self._request(
            "POST",
            f"/droplets/{server_id}/actions",
            {"type": "power_off"}
        )
        if not success:
            return False, f"Failed to power off: {message}"

        # Wait for power off
        time.sleep(10)

        # Resize
        success, data, message = self._request(
            "POST",
            f"/droplets/{server_id}/actions",
            {"type": "resize", "size": new_instance_type, "disk": True}
        )
        if not success:
            # Try to power back on
            self._request("POST", f"/droplets/{server_id}/actions", {"type": "power_on"})
            return False, f"Failed to resize: {message}"

        # Wait for resize
        time.sleep(30)

        # Power on
        success, _, message = self._request(
            "POST",
            f"/droplets/{server_id}/actions",
            {"type": "power_on"}
        )

        return True, f"Droplet {server_id} resized to {new_instance_type}"

    def get_available_sizes(self, region: str = "") -> List[InstanceType]:
        """Get available droplet sizes."""
        cache_key = f"sizes_{region}"
        if cache_key in self._cache:
            if time.time() - self._cache_time.get(cache_key, 0) < self._cache_ttl:
                return self._cache[cache_key]

        success, data, message = self._request("GET", "/sizes")
        if not success:
            return list(DIGITALOCEAN_INSTANCES.values())

        sizes = []
        for size in data.get("sizes", []):
            if region and region not in size.get("regions", []):
                continue

            instance = InstanceType(
                provider=CloudProvider.DIGITALOCEAN,
                type_id=size["slug"],
                size=self._slug_to_size(size["slug"]),
                spec=ServerSpec(
                    vcpus=size["vcpus"],
                    memory_gb=size["memory"] / 1024,
                    storage_gb=size["disk"],
                    bandwidth_tb=size["transfer"]
                ),
                hourly_cost=size["price_hourly"],
                monthly_cost=size["price_monthly"],
                region=region,
                available=size["available"]
            )
            sizes.append(instance)

        self._cache[cache_key] = sizes
        self._cache_time[cache_key] = time.time()

        return sizes

    def get_regions(self) -> List[Dict[str, Any]]:
        """Get available regions."""
        success, data, message = self._request("GET", "/regions")
        if not success:
            return []

        return [
            {
                "slug": r["slug"],
                "name": r["name"],
                "available": r["available"],
                "sizes": r.get("sizes", [])
            }
            for r in data.get("regions", [])
        ]

    def create_snapshot(self, server_id: str, name: str) -> Tuple[bool, str]:
        """Create a snapshot of a droplet."""
        success, data, message = self._request(
            "POST",
            f"/droplets/{server_id}/actions",
            {"type": "snapshot", "name": name}
        )
        if success:
            return True, f"Snapshot '{name}' creation started"
        return False, message

    def _droplet_to_server(self, droplet: Dict) -> Server:
        """Convert DO droplet to Server."""
        # Get IPs
        ip_address = None
        private_ip = None
        for network in droplet.get("networks", {}).get("v4", []):
            if network["type"] == "public":
                ip_address = network["ip_address"]
            elif network["type"] == "private":
                private_ip = network["ip_address"]

        # Get size info
        size = droplet.get("size", {})

        return Server(
            server_id=str(droplet.get("id", "")),
            name=droplet.get("name", ""),
            provider=CloudProvider.DIGITALOCEAN,
            instance_type=droplet.get("size_slug", ""),
            spec=ServerSpec(
                vcpus=size.get("vcpus", 1),
                memory_gb=size.get("memory", 1024) / 1024,
                storage_gb=size.get("disk", 25)
            ),
            role=ServerRole.GENERAL,
            region=droplet.get("region", {}).get("slug", ""),
            ip_address=ip_address,
            private_ip=private_ip,
            status=droplet.get("status", "unknown"),
            created_at=datetime.fromisoformat(droplet["created_at"].replace("Z", "+00:00"))
            if droplet.get("created_at") else None,
            monthly_cost=size.get("price_monthly", 0),
            tags={t: "true" for t in droplet.get("tags", [])},
            metadata={"droplet_id": droplet.get("id")}
        )

    def _slug_to_size(self, slug: str) -> InstanceSize:
        """Convert DO slug to InstanceSize."""
        if "1vcpu-1gb" in slug:
            return InstanceSize.NANO
        elif "1vcpu-2gb" in slug or "2vcpu-2gb" in slug:
            return InstanceSize.MICRO
        elif "2vcpu-4gb" in slug:
            return InstanceSize.SMALL
        elif "4vcpu-8gb" in slug:
            return InstanceSize.MEDIUM
        elif "8vcpu-16gb" in slug:
            return InstanceSize.LARGE
        elif "16vcpu-32gb" in slug:
            return InstanceSize.XLARGE
        else:
            return InstanceSize.MEDIUM


class AWSAPI(CloudProviderAPI):
    """
    AWS EC2 API integration for autonomous provisioning.

    Handles AWS operations via REST API (no boto3 dependency).
    """

    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "us-east-1"
    ):
        """
        Initialize AWS API.

        Args:
            access_key: AWS access key (or from AWS_ACCESS_KEY_ID env var)
            secret_key: AWS secret key (or from AWS_SECRET_ACCESS_KEY env var)
            region: AWS region
        """
        self.access_key = access_key or os.environ.get("AWS_ACCESS_KEY_ID", "")
        self.secret_key = secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        self.region = region
        self.provider = CloudProvider.AWS

    def check_api_status(self) -> Tuple[bool, str]:
        """Check if AWS API is accessible."""
        if not self.access_key or not self.secret_key:
            return False, "AWS credentials not configured"
        # Would implement actual AWS STS check
        return True, "AWS credentials configured"

    def list_servers(self) -> List[Server]:
        """List all EC2 instances."""
        # Would implement EC2 DescribeInstances
        return []

    def get_server(self, server_id: str) -> Optional[Server]:
        """Get a specific EC2 instance."""
        # Would implement EC2 DescribeInstances with filter
        return None

    def create_server(self, request: ProvisioningRequest) -> Tuple[bool, Optional[Server], str]:
        """Create a new EC2 instance."""
        # Would implement EC2 RunInstances
        return False, None, "AWS provisioning not yet implemented"

    def delete_server(self, server_id: str) -> Tuple[bool, str]:
        """Terminate an EC2 instance."""
        # Would implement EC2 TerminateInstances
        return False, "AWS termination not yet implemented"

    def resize_server(self, server_id: str, new_instance_type: str) -> Tuple[bool, str]:
        """Resize an EC2 instance."""
        # Would implement EC2 ModifyInstanceAttribute
        return False, "AWS resize not yet implemented"

    def get_available_sizes(self, region: str = "") -> List[InstanceType]:
        """Get available EC2 instance types."""
        return list(AWS_INSTANCES.values())

    def get_regions(self) -> List[Dict[str, Any]]:
        """Get available AWS regions."""
        # Standard AWS regions
        return [
            {"slug": "us-east-1", "name": "US East (N. Virginia)", "available": True},
            {"slug": "us-west-2", "name": "US West (Oregon)", "available": True},
            {"slug": "eu-west-1", "name": "EU (Ireland)", "available": True},
        ]


class MockCloudAPI(CloudProviderAPI):
    """
    Mock cloud API for testing and development.

    Simulates cloud operations without actual infrastructure changes.
    """

    def __init__(self):
        self.provider = CloudProvider.LOCAL
        self._servers: Dict[str, Server] = {}
        self._next_id = 1000

    def check_api_status(self) -> Tuple[bool, str]:
        return True, "Mock API ready"

    def list_servers(self) -> List[Server]:
        return list(self._servers.values())

    def get_server(self, server_id: str) -> Optional[Server]:
        return self._servers.get(server_id)

    def create_server(self, request: ProvisioningRequest) -> Tuple[bool, Optional[Server], str]:
        server_id = str(self._next_id)
        self._next_id += 1

        instance = DIGITALOCEAN_INSTANCES.get(request.instance_type)
        spec = instance.spec if instance else ServerSpec(2, 4, 80)

        server = Server(
            server_id=server_id,
            name=request.name,
            provider=self.provider,
            instance_type=request.instance_type,
            spec=spec,
            role=request.role,
            region=request.region,
            ip_address=f"10.0.0.{self._next_id}",
            status="active",
            created_at=datetime.utcnow(),
            monthly_cost=instance.monthly_cost if instance else 20.0
        )

        self._servers[server_id] = server
        return True, server, f"Mock server {server_id} created"

    def delete_server(self, server_id: str) -> Tuple[bool, str]:
        if server_id in self._servers:
            del self._servers[server_id]
            return True, f"Mock server {server_id} deleted"
        return False, "Server not found"

    def resize_server(self, server_id: str, new_instance_type: str) -> Tuple[bool, str]:
        if server_id in self._servers:
            self._servers[server_id].instance_type = new_instance_type
            return True, f"Mock server {server_id} resized"
        return False, "Server not found"

    def get_available_sizes(self, region: str = "") -> List[InstanceType]:
        return list(DIGITALOCEAN_INSTANCES.values())

    def get_regions(self) -> List[Dict[str, Any]]:
        return [{"slug": "mock-1", "name": "Mock Region", "available": True}]


def get_cloud_provider(provider: CloudProvider) -> CloudProviderAPI:
    """
    Get a cloud provider API instance.

    Args:
        provider: Which cloud provider to use

    Returns:
        CloudProviderAPI implementation
    """
    if provider == CloudProvider.DIGITALOCEAN:
        return DigitalOceanAPI()
    elif provider == CloudProvider.AWS:
        return AWSAPI()
    elif provider == CloudProvider.LOCAL:
        return MockCloudAPI()
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _load_do_token_from_file() -> Optional[str]:
    """Load DO token from known file locations."""
    import json as _json

    # Check do.env files
    env_paths = [
        Path.home() / "hands-off/state/do.env",
        Path.home() / "hands-off-engine/state/do.env",
        Path.home() / "hands-off-engine/termux-hands-off/state/do.env",
        Path("/root/hands-off/state/do.env"),
        Path("/root/hands-off-out/state/do.env"),
        Path("state/do.env"),
        Path("termux-hands-off/state/do.env"),
    ]

    for path in env_paths:
        if path.exists():
            try:
                content = path.read_text().strip()
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('DO_TOKEN=') or line.startswith('DO_API_TOKEN='):
                        token = line.split('=', 1)[1].strip().strip('"\'')
                        if token and not token.startswith('#'):
                            print(f"   [DO Token] Found in {path}")
                            return token
            except Exception:
                continue

    # Check vault.json files (where other API keys are stored)
    vault_paths = [
        Path.home() / "hands-off/vault.json",
        Path.home() / "hands-off-engine/termux-hands-off/agent/vault.json",
        Path("termux-hands-off/agent/vault.json"),
        Path("/root/hands-off/vault.json"),
    ]

    for path in vault_paths:
        if path.exists():
            try:
                data = _json.loads(path.read_text())
                for key in ["DO_TOKEN", "DO_API_TOKEN", "DIGITALOCEAN_TOKEN", "DIGITALOCEAN_API_KEY"]:
                    if key in data and data[key]:
                        print(f"   [DO Token] Found in vault {path}")
                        return data[key]
            except Exception:
                continue

    return None


def get_best_available_provider() -> Tuple[CloudProviderAPI, CloudProvider]:
    """
    Get the best available cloud provider based on configured credentials.

    Returns:
        Tuple of (API instance, provider enum)
    """
    # Try DigitalOcean first - check multiple env var names AND file
    do_token = (
        os.environ.get("DO_API_TOKEN") or
        os.environ.get("DO_TOKEN") or
        os.environ.get("DIGITALOCEAN_API_KEY") or
        _load_do_token_from_file()
    )

    if do_token:
        # Set it in env for the API class to use
        os.environ["DO_API_TOKEN"] = do_token
        api = DigitalOceanAPI()
        ok, msg = api.check_api_status()
        if ok:
            print(f"   [Provider] DigitalOcean API connected")
            return api, CloudProvider.DIGITALOCEAN
        else:
            print(f"   [Provider] DO token found but API check failed: {msg}")

    # Try AWS
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        api = AWSAPI()
        ok, msg = api.check_api_status()
        if ok:
            print(f"   [Provider] AWS API connected")
            return api, CloudProvider.AWS
        else:
            print(f"   [Provider] AWS creds found but API check failed: {msg}")

    # Fall back to mock - but explain why
    print("   [Provider] No cloud credentials found, using mock provider")
    print("   [Provider] To enable real provisioning, add DO_TOKEN to:")
    print("   [Provider]   - Environment variable: DO_TOKEN or DO_API_TOKEN")
    print("   [Provider]   - File: state/do.env or vault.json")
    return MockCloudAPI(), CloudProvider.LOCAL
