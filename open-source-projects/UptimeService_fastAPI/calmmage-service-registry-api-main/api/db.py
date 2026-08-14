import logging
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings
from typing import Dict, Optional

from api.models import (
    Service,
    ServiceStatusResponse,
    ServiceResponse,
    format_datetime,
)


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "service_registry"
    api_host: str = "0.0.0.0"
    api_port: int = 5000
    monitoring_interval_seconds: int = 60  # How often to check service status

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.mongodb_db_name]

logger = logging.getLogger(__name__)


# Legacy Heartbeat Functions


async def store_heartbeat(service_key: str, metadata: Optional[dict] = None) -> None:
    """Store a service heartbeat"""
    heartbeat = {
        "service_key": service_key,
        "timestamp": format_datetime(datetime.now()),
        "metadata": metadata,
    }
    await db.heartbeats.insert_one(heartbeat)


def _compute_time_since_last_heartbeat(last_heartbeat: datetime) -> tuple[float, str]:
    """Helper to compute time since last heartbeat"""
    now = datetime.now()
    delta = now - last_heartbeat
    seconds = delta.total_seconds()

    if seconds < 60:
        readable = f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        readable = f"{minutes} minutes"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        readable = f"{hours} hours"
    else:
        days = int(seconds / 86400)
        readable = f"{days} days"

    return seconds, readable


async def get_all_services_status() -> Dict[str, ServiceStatusResponse]:
    """Get status of all services based on heartbeat history"""
    # Only look at heartbeats from last 7 days
    cutoff_time = format_datetime(datetime.now() - timedelta(days=7))

    # Get all services configuration
    services = {}
    async for service_data in db.services.find():
        services[service_data["service_key"]] = Service(**service_data)

    # Get all unique service keys with recent heartbeats
    service_keys = set()
    async for heartbeat in db.heartbeats.find({"timestamp": {"$gte": cutoff_time}}):
        service_keys.add(heartbeat["service_key"])

    # Compute status for each service
    services_status = {}
    for service_key in service_keys:
        # Get recent heartbeats for this service
        heartbeats = []
        cursor = db.heartbeats.find(
            {"service_key": service_key, "timestamp": {"$gte": cutoff_time}}
        ).sort("timestamp", -1)
        async for heartbeat in cursor:
            heartbeats.append(heartbeat)

        # Get or create service record
        service = services.get(service_key)
        if not service:
            # Create new service with default values if not found
            service = Service(service_key=service_key)
            services[service_key] = service

        # Compute time since last heartbeat if we have any
        last_heartbeat = None
        time_since_last_heartbeat_seconds = None
        time_since_last_heartbeat_readable = None
        median_interval = None

        if heartbeats:
            # Get last heartbeat info
            last_heartbeat = datetime.fromisoformat(heartbeats[0]["timestamp"])
            time_since_last_heartbeat_seconds, time_since_last_heartbeat_readable = (
                _compute_time_since_last_heartbeat(last_heartbeat)
            )

            # Compute status based on heartbeat history
            if len(heartbeats) >= 4:
                # Calculate intervals between heartbeats
                intervals = []
                for i in range(len(heartbeats) - 1):
                    current = datetime.fromisoformat(heartbeats[i]["timestamp"])
                    next_hb = datetime.fromisoformat(heartbeats[i + 1]["timestamp"])
                    intervals.append((current - next_hb).total_seconds())

                # Use median interval to determine expected frequency
                intervals.sort()
                median_interval = intervals[len(intervals) // 2]

        services_status[service_key] = ServiceStatusResponse(
            service=service,
            last_heartbeat=last_heartbeat.isoformat() if last_heartbeat else None,
            time_since_last_heartbeat_seconds=time_since_last_heartbeat_seconds,
            time_since_last_heartbeat_readable=time_since_last_heartbeat_readable,
            median_interval=median_interval,
            heartbeat_count=len(heartbeats),
        )

    return services_status

#Added
async def get_services_token(token: str) -> list[ServiceResponse]:
    """Get all services matching the token with their latest heartbeat."""

    service_responses: list[ServiceResponse] = []

    async for service_data in db.services.find({"token": token}):
        service = Service(**service_data)

        latest_heartbeat = await db.heartbeats.find_one(
            {"service_key": service.service_key},
            sort=[("timestamp", -1)]
        )

        if latest_heartbeat is None:
            continue

        last_notification = datetime.fromisoformat(latest_heartbeat["timestamp"])

        service_responses.append(
            ServiceResponse(
                serviceId=service.service_key,
                lastNotification=last_notification
            )
        )

    return service_responses

async def get_service(service_key: str) -> Optional[Service]:
    """Get a service by key"""
    service_data = await db.services.find_one({"service_key": service_key})
    return Service(**service_data) if service_data else None


async def get_all_services() -> Dict[str, Service]:
    """Get all configured services"""
    services = {}
    async for service_data in db.services.find():
        service = Service(**service_data)
        services[service.service_key] = service
    return services