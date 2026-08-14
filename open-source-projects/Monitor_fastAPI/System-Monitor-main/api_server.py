"""
FastAPI REST API Server for System Monitor

This module exposes system metrics through REST API.
OpenAPI (Swagger) documentation is automatically generated.

Usage:
    uvicorn api_server:app --reload --port 5000
    
Endpoints:
    POST /monitor/commands
"""

from __future__ import annotations

from typing import Optional
import psutil
import re
import os
import sys
from datetime import datetime

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException, Response
    from pydantic import BaseModel, Field
except ImportError:
    print("FastAPI not installed. To install: pip install fastapi uvicorn")
    sys.exit(1)

#Added
class ProcessRequest(BaseModel):
    filter_flags: Optional[str] = None #not implemented because of psutil, so the POST accept the parameter but it does NOT WORK
    command_regex: str

#Added
class ProcessResponse(BaseModel):
    processId:  int
    processString: str        


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(..., description="Error time")


# FastAPI Application
app = FastAPI(
    title="System Monitor API",
    description="""
    🖥️ **System Monitor REST API**
    
    This API allows you to monitor system processes in real-time.
    
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Endpoints
@app.post("/monitor/commands", response_model=list[ProcessResponse])
async def get_process_commands(request: ProcessRequest) -> list[ProcessResponse]:

    regex = request.command_regex
    
    #check if the regex is valid or raise an exception
    try:
        pattern_reg = re.compile(regex)

    except re.error as exc:
        raise HTTPException(status_code=400, detail={
                "code": 400,
                "message": f"Invalid regular expression: {exc}",
            },
        )

    process_responses: list[ProcessResponse] = []

    for proc in psutil.process_iter():
        #try except to skip processes that cause errors: psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess
        try:
            #entire cmdline string of the process (check psutil docs)
            process_string = " ".join(proc.cmdline())

            #if the cmdline is empty we skip the current process
            if not process_string:
                continue

            #if the input regex matches anything on the cmdline string we save pid as processId and cmdline as processString
            if(pattern_reg.search(process_string)):
                process_responses.append(ProcessResponse(processId=proc.pid,
                        processString=process_string))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue 
    #we return a list of processes that matched                      
    return process_responses


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return Response(
        content=ErrorResponse(
            error=type(exc).__name__,
            message=str(exc),
            timestamp=datetime.now()
        ).model_dump_json(),
        status_code=500,
        media_type="application/json"
    )


# Startup/Shutdown events
@app.on_event("startup")
async def startup_event():
    print("🚀 System Monitor API starting...")
    print("📊 Swagger UI: http://localhost:5000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    print("👋 System Monitor API closing...")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
