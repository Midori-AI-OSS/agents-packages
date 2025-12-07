"""Service status enumeration for Midori AI state reporting."""

from enum import Enum

class ServiceStatus(str, Enum):
    """Standardized status values for service state reporting."""

    HEALTHY = "Healthy"
    UNHEALTHY = "Unhealthy"
    DEGRADED = "Degraded"
    OFFLINE = "Offline"
    UNKNOWN = "Unknown"

    STARTING = "Starting"
    STOPPING = "Stopping"
    RESTARTING = "Restarting"
    UPDATING = "Updating"
    PROVISIONING = "Provisioning"
    MAINTENANCE = "Maintenance"
    RECOVERING = "Recovering"
    PAUSED = "Paused"
    FROZEN = "Frozen"
