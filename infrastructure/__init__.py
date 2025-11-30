"""
Autonomous Infrastructure Management

Self-upgrading infrastructure that automatically provisions, scales,
and upgrades hardware without user intervention.

The user should NEVER need to:
- Buy cloud servers manually
- Upgrade instance capabilities
- Purchase hardware
- Manage infrastructure scaling

The system handles ALL infrastructure decisions and executions autonomously.

Components:
- infra_types: Data models for infrastructure management
- cloud_providers: API integrations (DigitalOcean, AWS, etc.)
- auto_provisioner: Autonomous provisioning and scaling
- autonomous_infra_manager: Master controller for full autonomy

Standard: Yair Siegel Master Level Operations - Full Self-Control

Note: All datetime operations use timezone-aware UTC (datetime.now(timezone.utc))
for Python 3.12+ compatibility.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    This replaces deprecated datetime.utcnow() for Python 3.12+ compatibility.

    Returns:
        Current UTC time with timezone info
    """
    return datetime.now(timezone.utc)

from infrastructure.infra_types import (
    CloudProvider,
    InstanceSize,
    InfrastructureAction,
    ServerSpec,
    Server,
    ServerRole,
    ScalingDecision,
    InfrastructureBudget,
    ProvisioningRequest,
    MigrationPlan,
    DIGITALOCEAN_INSTANCES,
    AWS_INSTANCES,
)

from infrastructure.cloud_providers import (
    CloudProviderAPI,
    DigitalOceanAPI,
    AWSAPI,
    MockCloudAPI,
    get_cloud_provider,
    get_best_available_provider,
)

from infrastructure.auto_provisioner import (
    AutoProvisioner,
    get_auto_provisioner,
)

from infrastructure.autonomous_infra_manager import (
    AutonomousInfraManager,
)

__all__ = [
    # Utilities
    'utc_now',

    # Types
    'CloudProvider',
    'InstanceSize',
    'InfrastructureAction',
    'ServerSpec',
    'Server',
    'ServerRole',
    'ScalingDecision',
    'InfrastructureBudget',
    'ProvisioningRequest',
    'MigrationPlan',

    # Instance catalogs
    'DIGITALOCEAN_INSTANCES',
    'AWS_INSTANCES',

    # Cloud providers
    'CloudProviderAPI',
    'DigitalOceanAPI',
    'AWSAPI',
    'MockCloudAPI',
    'get_cloud_provider',
    'get_best_available_provider',

    # Provisioner
    'AutoProvisioner',
    'get_auto_provisioner',

    # Manager
    'AutonomousInfraManager',
]


def start_autonomous_infrastructure(
    budget: float = 500.0,
    dry_run: bool = False
):
    """
    Start the autonomous infrastructure manager.

    This is the main entry point for fully autonomous infrastructure.
    Once started, the system will:
    - Monitor all hardware health
    - Automatically upgrade servers when needed
    - Provision new servers when capacity is needed
    - Scale down when resources are underutilized
    - Handle all infrastructure without user intervention

    Args:
        budget: Monthly budget limit in USD
        dry_run: If True, don't actually provision (testing)
    """
    manager = AutonomousInfraManager(
        budget_monthly=budget,
        auto_provision=True,
        auto_upgrade=True,
        auto_scale=True,
        dry_run=dry_run
    )
    manager.start()


def check_infrastructure() -> dict:
    """
    Quick infrastructure health check.

    Returns current infrastructure status without starting the manager.
    """
    provisioner = get_auto_provisioner(dry_run=True)
    return provisioner.get_infrastructure_status()
