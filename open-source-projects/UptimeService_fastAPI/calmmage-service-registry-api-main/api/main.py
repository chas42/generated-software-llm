from datetime import datetime
from fastapi import FastAPI, HTTPException
from loguru import logger
from typing import Set

from api.db import (
    get_all_services,
    store_heartbeat,
    get_services_token,
    db,
)
from api.models import (
    Service,
    ServiceStatus,
    HeartbeatRequest,
    ServiceRequest,
    ServiceResponse,
    format_datetime,
)

app = FastAPI(title="Service Registry API")


# In-memory cache of known services
known_services: Set[str] = set()


async def load_known_services():
    """Load known services into memory"""
    services = await get_all_services()
    known_services.update(services.keys())
    logger.info(f"Loaded {len(known_services)} known services")


# Heartbeat


@app.post("/heartbeat")
async def heartbeat(request: HeartbeatRequest) -> dict:
    """Record a service heartbeat. Creates service if it doesn't exist."""
    try:
        # Create service if it doesn't exist
        if request.serviceId not in known_services:
            logger.info(f"New service detected: {request.serviceId}")
            # Generate default display name from service key
            display_name = request.serviceId.replace("-", " ").replace("_", " ").title()
            # Initialize new service with all default values
            service = Service(
                service_key=request.serviceId,
                token=request.token,
                display_name=display_name,
                status=ServiceStatus.ALIVE,
                alerts_enabled=True,
                service_group="default",
                updated_at=datetime.now(),
            )
            update_data = service.model_dump()
            # Convert datetime and enums to MongoDB format
            if "updated_at" in update_data:
                update_data["updated_at"] = format_datetime(update_data["updated_at"])
            if "service_type" in update_data and update_data["service_type"] is not None:
                update_data["service_type"] = update_data["service_type"].value
            if "status" in update_data:
                update_data["status"] = update_data["status"].value
            await db.services.insert_one(update_data)
            known_services.add(request.serviceId)

        else:
            # Service exists: check that the provided token matches the stored token
            existing_service = await db.services.find_one(
                {"service_key": request.serviceId}
            )

            if not existing_service:
                # Cache says it exists, but DB does not: keep cache consistent
                known_services.discard(request.serviceId)
                raise HTTPException(status_code=400, detail="Service cache is inconsistent")

            if existing_service.get("token") != request.token:
                raise HTTPException(status_code=400, detail="Invalid token for service")

        # Store heartbeat only after token validation
        await store_heartbeat(
            service_key=request.serviceId,
            metadata=request.metadata,
        )

        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to store heartbeat")
        raise HTTPException(status_code=500, detail=str(e))

#Added
@app.post("/services", response_model=list[ServiceResponse])
async def get_services(request: ServiceRequest) -> list[ServiceResponse]:
    try:
        #function that gets a list of all the services with token
        services = await get_services_token(request.token)
        return services
    except Exception as e:
        logger.exception("Failed to get services through token")
        raise HTTPException(status_code=500, detail=str(e))        

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    await load_known_services()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    import uvicorn
    from api.db import settings

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
