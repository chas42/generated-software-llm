from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Union

# Constants for datetime handling
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"  # ISO format with microseconds


def format_datetime(dt: datetime) -> str:
    """Convert datetime to string in our standard format"""
    return dt.strftime(DATETIME_FORMAT)


class ServiceType(str, Enum):
    """Type of service being monitored"""

    CLOUD_SERVICE = "cloud_service"  # Long-running cloud service
    LOCAL_JOB = "local_job"  # Periodic local job that can disappear sometimes


class ServiceStatus(str, Enum):
    """Service status based on monitoring"""

    UNKNOWN = "unknown"  # Not enough data (< 4 heartbeats)
    ALIVE = "alive"  # Service is responding within expected period
    DOWN = "down"  # Service is not responding
    DEAD = "dead"  # Service has been down for too long


class HeartbeatRequest(BaseModel):
    serviceId: str = Field(..., description="Unique identifier for the service")
    token:       str
    metadata: Optional[dict] = None


class Service(BaseModel):
    """Service configuration and current status.

    Attributes:
        service_key: Unique identifier for the service
        token: works like a password of sort
        display_name: Human-readable name for the service (defaults to formatted service_key)
        service_type: Type of service (cloud_service or local_job)
        service_group: Group name for organizing related services
        expected_period: Expected time between heartbeats in seconds
        dead_after: Time after which to consider service dead in seconds
        status: Current service status
        updated_at: Last update timestamp
        alerts_enabled: Whether to send alerts for state transitions
        metadata: Additional service metadata
    """

    service_key: str
    token:       str   
    display_name: Optional[str] = None  # Will be set to formatted service_key if None
    service_type: Optional[ServiceType] = None
    service_group: Optional[str] = "default"
    expected_period: Optional[int] = None  # seconds
    dead_after: Optional[int] = None  # seconds
    status: ServiceStatus = ServiceStatus.ALIVE
    updated_at: datetime = Field(default_factory=datetime.now)
    alerts_enabled: bool = Field(default=True)  # Default to True for backward compatibility
    metadata: Optional[Dict] = Field(default_factory=dict)  # Initialize empty dict by default

    @field_validator("alerts_enabled", mode="before")
    @classmethod
    def parse_alerts_enabled(cls, value: Union[bool, str]) -> bool:
        """Convert string representation of boolean to actual boolean"""
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)


class ServiceStatusResponse(BaseModel):
    """Status information for a single service"""

    service: Service  # The full service record
    last_heartbeat: Optional[str] = None
    time_since_last_heartbeat_seconds: Optional[float] = None
    time_since_last_heartbeat_readable: Optional[str] = None
    median_interval: Optional[float] = None
    heartbeat_count: int

#Added
class ServiceResponse(BaseModel):
    serviceId:       str
    lastNotification: datetime

#Added
class  ServiceRequest(BaseModel):
    token: str    

