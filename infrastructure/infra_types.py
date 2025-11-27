"""
Infrastructure Types - Autonomous Hardware Provisioning Models

Data models for autonomous infrastructure management.
Supports cloud providers and physical hardware procurement.

Standard: Yair Siegel Master Level Operations - Full Self-Control
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4


class CloudProvider(Enum):
    """Supported cloud providers for autonomous provisioning."""
    DIGITALOCEAN = "digitalocean"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    HETZNER = "hetzner"
    VULTR = "vultr"
    LINODE = "linode"
    LOCAL = "local"  # Physical/local hardware


class InstanceSize(Enum):
    """Standard instance size tiers."""
    NANO = "nano"           # 1 vCPU, 1GB RAM
    MICRO = "micro"         # 1 vCPU, 2GB RAM
    SMALL = "small"         # 2 vCPU, 4GB RAM
    MEDIUM = "medium"       # 4 vCPU, 8GB RAM
    LARGE = "large"         # 8 vCPU, 16GB RAM
    XLARGE = "xlarge"       # 16 vCPU, 32GB RAM
    XXLARGE = "xxlarge"     # 32 vCPU, 64GB RAM
    DEDICATED = "dedicated" # Dedicated/bare metal


class InfrastructureAction(Enum):
    """Actions the system can take autonomously."""
    PROVISION_SERVER = "provision_server"
    TERMINATE_SERVER = "terminate_server"
    UPGRADE_SERVER = "upgrade_server"
    DOWNGRADE_SERVER = "downgrade_server"
    ADD_STORAGE = "add_storage"
    ADD_MEMORY = "add_memory"
    SCALE_HORIZONTALLY = "scale_horizontally"
    SCALE_DOWN = "scale_down"
    MIGRATE_WORKLOAD = "migrate_workload"
    FAILOVER = "failover"
    BACKUP = "backup"
    RESTORE = "restore"


class ServerRole(Enum):
    """Server roles in the trading infrastructure."""
    TRADING_PRIMARY = "trading_primary"
    TRADING_BACKUP = "trading_backup"
    ALPHA_ENGINE = "alpha_engine"
    AI_NEXUS = "ai_nexus"
    DATABASE = "database"
    MONITORING = "monitoring"
    GENERAL = "general"


class ProvisioningStatus(Enum):
    """Status of provisioning operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ServerSpec:
    """Specification for a server instance."""
    vcpus: int
    memory_gb: float
    storage_gb: float
    bandwidth_tb: float = 1.0
    gpu: bool = False
    gpu_count: int = 0
    ssd: bool = True
    dedicated: bool = False

    def meets_requirements(self, required: 'ServerSpec') -> bool:
        """Check if this spec meets requirements."""
        return (
            self.vcpus >= required.vcpus and
            self.memory_gb >= required.memory_gb and
            self.storage_gb >= required.storage_gb
        )


@dataclass
class InstanceType:
    """Cloud provider instance type mapping."""
    provider: CloudProvider
    type_id: str              # e.g., "s-2vcpu-4gb" for DO, "t3.medium" for AWS
    size: InstanceSize
    spec: ServerSpec
    hourly_cost: float
    monthly_cost: float
    region: str = ""
    available: bool = True


@dataclass
class Server:
    """Represents a provisioned server."""
    server_id: str
    name: str
    provider: CloudProvider
    instance_type: str
    spec: ServerSpec
    role: ServerRole
    region: str
    ip_address: Optional[str] = None
    private_ip: Optional[str] = None
    status: str = "unknown"
    created_at: Optional[datetime] = None
    monthly_cost: float = 0.0
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScalingDecision:
    """Autonomous scaling decision."""
    decision_id: str
    timestamp: datetime
    action: InfrastructureAction
    reason: str

    # What triggered this
    trigger_metrics: Dict[str, Any]

    # What to do
    target_server: Optional[str] = None  # Server ID if targeting specific server
    new_instance_type: Optional[str] = None
    new_spec: Optional[ServerSpec] = None
    new_region: Optional[str] = None

    # Cost analysis
    current_monthly_cost: float = 0.0
    projected_monthly_cost: float = 0.0
    cost_change: float = 0.0

    # Approval
    auto_approved: bool = False
    requires_approval: bool = True
    approval_status: str = "pending"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Execution
    executed: bool = False
    executed_at: Optional[datetime] = None
    execution_result: Optional[str] = None
    rollback_available: bool = False

    # Trading protection
    trading_impact: str = "none"  # none, low, medium, high
    scheduled_maintenance_window: Optional[str] = None


@dataclass
class InfrastructureBudget:
    """Budget configuration for autonomous infrastructure spending."""
    monthly_limit: float                    # Maximum monthly spend
    current_spend: float = 0.0              # Current month spend
    reserved_for_emergency: float = 100.0   # Reserved for emergency scaling

    # Auto-approval thresholds
    auto_approve_hourly_increase: float = 0.10   # Auto-approve if hourly cost increase < this
    auto_approve_monthly_increase: float = 50.0  # Auto-approve if monthly cost increase < this

    # Spending alerts
    alert_at_percent: float = 80.0          # Alert when spend reaches this %
    hard_limit: bool = True                 # Hard stop at limit vs soft warning

    # ROI tracking
    trading_revenue_this_month: float = 0.0
    infrastructure_roi: float = 0.0         # revenue / spend ratio


@dataclass
class ProvisioningRequest:
    """Request to provision new infrastructure."""
    request_id: str
    timestamp: datetime
    action: InfrastructureAction

    # What to provision
    provider: CloudProvider
    instance_type: str
    region: str
    role: ServerRole
    name: str

    # Configuration
    spec: Optional[ServerSpec] = None
    user_data: Optional[str] = None  # Cloud-init script
    ssh_keys: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    # Status
    status: ProvisioningStatus = ProvisioningStatus.PENDING
    server_id: Optional[str] = None
    error: Optional[str] = None

    # Cost
    estimated_monthly_cost: float = 0.0


@dataclass
class MigrationPlan:
    """Plan for migrating workload to new hardware."""
    plan_id: str
    timestamp: datetime

    # Source and destination
    source_server: str
    destination_server: Optional[str]  # None if provisioning new
    destination_spec: ServerSpec

    # Migration details
    workloads: List[str]              # Services/processes to migrate
    data_to_migrate_gb: float
    estimated_downtime_minutes: float

    # Execution
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    status: str = "planned"

    # Rollback
    rollback_plan: Optional[Dict[str, Any]] = None


# Standard instance types for each provider
DIGITALOCEAN_INSTANCES: Dict[str, InstanceType] = {
    "s-1vcpu-1gb": InstanceType(
        CloudProvider.DIGITALOCEAN, "s-1vcpu-1gb", InstanceSize.NANO,
        ServerSpec(1, 1, 25), 0.007, 5.0
    ),
    "s-1vcpu-2gb": InstanceType(
        CloudProvider.DIGITALOCEAN, "s-1vcpu-2gb", InstanceSize.MICRO,
        ServerSpec(1, 2, 50), 0.015, 10.0
    ),
    "s-2vcpu-4gb": InstanceType(
        CloudProvider.DIGITALOCEAN, "s-2vcpu-4gb", InstanceSize.SMALL,
        ServerSpec(2, 4, 80), 0.030, 20.0
    ),
    "s-4vcpu-8gb": InstanceType(
        CloudProvider.DIGITALOCEAN, "s-4vcpu-8gb", InstanceSize.MEDIUM,
        ServerSpec(4, 8, 160), 0.060, 40.0
    ),
    "s-8vcpu-16gb": InstanceType(
        CloudProvider.DIGITALOCEAN, "s-8vcpu-16gb", InstanceSize.LARGE,
        ServerSpec(8, 16, 320), 0.119, 80.0
    ),
    "s-16vcpu-32gb": InstanceType(
        CloudProvider.DIGITALOCEAN, "s-16vcpu-32gb", InstanceSize.XLARGE,
        ServerSpec(16, 32, 640), 0.238, 160.0
    ),
    # CPU-optimized
    "c-4vcpu-8gb": InstanceType(
        CloudProvider.DIGITALOCEAN, "c-4vcpu-8gb", InstanceSize.MEDIUM,
        ServerSpec(4, 8, 100, dedicated=True), 0.085, 56.0
    ),
    "c-8vcpu-16gb": InstanceType(
        CloudProvider.DIGITALOCEAN, "c-8vcpu-16gb", InstanceSize.LARGE,
        ServerSpec(8, 16, 200, dedicated=True), 0.170, 112.0
    ),
}

AWS_INSTANCES: Dict[str, InstanceType] = {
    "t3.micro": InstanceType(
        CloudProvider.AWS, "t3.micro", InstanceSize.MICRO,
        ServerSpec(2, 1, 20), 0.0104, 7.5
    ),
    "t3.small": InstanceType(
        CloudProvider.AWS, "t3.small", InstanceSize.SMALL,
        ServerSpec(2, 2, 20), 0.0208, 15.0
    ),
    "t3.medium": InstanceType(
        CloudProvider.AWS, "t3.medium", InstanceSize.MEDIUM,
        ServerSpec(2, 4, 20), 0.0416, 30.0
    ),
    "t3.large": InstanceType(
        CloudProvider.AWS, "t3.large", InstanceSize.LARGE,
        ServerSpec(2, 8, 20), 0.0832, 60.0
    ),
    "c6i.large": InstanceType(
        CloudProvider.AWS, "c6i.large", InstanceSize.MEDIUM,
        ServerSpec(2, 4, 20, dedicated=True), 0.085, 61.0
    ),
    "c6i.xlarge": InstanceType(
        CloudProvider.AWS, "c6i.xlarge", InstanceSize.LARGE,
        ServerSpec(4, 8, 20, dedicated=True), 0.170, 122.0
    ),
}


def create_scaling_decision(
    action: InfrastructureAction,
    reason: str,
    trigger_metrics: Dict[str, Any],
    trading_impact: str = "none"
) -> ScalingDecision:
    """Create a new scaling decision."""
    return ScalingDecision(
        decision_id=f"scale_{uuid4().hex[:12]}",
        timestamp=datetime.utcnow(),
        action=action,
        reason=reason,
        trigger_metrics=trigger_metrics,
        trading_impact=trading_impact
    )


def create_provisioning_request(
    action: InfrastructureAction,
    provider: CloudProvider,
    instance_type: str,
    region: str,
    role: ServerRole,
    name: str
) -> ProvisioningRequest:
    """Create a new provisioning request."""
    return ProvisioningRequest(
        request_id=f"prov_{uuid4().hex[:12]}",
        timestamp=datetime.utcnow(),
        action=action,
        provider=provider,
        instance_type=instance_type,
        region=region,
        role=role,
        name=name
    )
