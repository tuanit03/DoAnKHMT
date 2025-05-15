import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

import config
from database import get_db
from models import AnomalyParamResponse, AnomalyParamCreate
from services.db_service import DBService

router = APIRouter(prefix="/anomalies", tags=["anomalies"])
# router = APIRouter(tags=["anomalies"])

# Configure logging
logger = logging.getLogger(__name__)

# In-memory store of connected SSE clients for real-time updates
anomaly_clients = []

@router.get("/", response_model=List[AnomalyParamResponse])
async def get_anomaly_params(
    skip: int = 0,
    limit: int = 100,
    classification_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get anomaly parameters with optional filtering
    """
    anomaly_params = await DBService.get_anomaly_params(
        db, 
        skip=skip, 
        limit=limit,
        classification_type=classification_type,
        start_time=start_time,
        end_time=end_time
    )
    return anomaly_params

@router.get("/recent", response_model=List[AnomalyParamResponse])
async def get_recent_anomalies(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent anomaly parameters for the specified time period
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    anomaly_params = await DBService.get_anomaly_params(
        db,
        classification_type="anomaly",
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return anomaly_params

@router.get("/unidentified", response_model=List[AnomalyParamResponse])
async def get_unidentified(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent unidentified parameters for the specified time period
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    unidentified_params = await DBService.get_anomaly_params(
        db,
        classification_type="unidentified",
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return unidentified_params

@router.get("/stream")
async def stream_anomalies(request: Request):
    """
    Stream anomaly parameters in real-time using SSE
    """
    async def event_generator():
        # Create a new queue for this client
        queue = asyncio.Queue()
        client_id = id(queue)  # Generate unique ID for this client
        anomaly_clients.append(queue)
        logger.info(f"Client connected to anomalies stream: {client_id}")
        
        # Initial keepalive to establish connection
        yield {
            "event": "ping",
            "id": "0",
            "data": json.dumps({"status": "connected"})
        }
        
        try:
            while True:
                # Check if client is still connected
                if await request.is_disconnected():
                    logger.info(f"Client {client_id} disconnected")
                    break
                    
                # Wait for new anomaly parameters with timeout
                try:
                    anomaly = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    # Convert to dict for sending over SSE
                    anomaly_dict = {
                        "id": anomaly.id,
                        "timestamp": anomaly.timestamp.isoformat(),
                        "param_value": anomaly.param_value,
                        "classification_type": anomaly.classification_type
                    }
                    
                    # Send the anomaly as an event with proper JSON serialization
                    yield {
                        "event": "anomaly",
                        "id": str(anomaly.id),
                        "data": json.dumps(anomaly_dict)
                    }
                except asyncio.TimeoutError:
                    # Send keepalive ping every 30 seconds to maintain connection
                    yield {
                        "event": "ping",
                        "id": "keepalive",
                        "data": json.dumps({"timestamp": datetime.now().isoformat()})
                    }
        except asyncio.CancelledError:
            # Client disconnected
            logger.info(f"Client {client_id} connection cancelled")
        except Exception as e:
            logger.error(f"Error in anomalies stream for client {client_id}: {str(e)}")
        finally:
            # Remove client queue when connection ends
            if queue in anomaly_clients:
                anomaly_clients.remove(queue)
            logger.info(f"Client {client_id} removed from anomalies stream")
    
    return EventSourceResponse(event_generator())

# Function to broadcast new anomaly parameters to all connected clients
async def broadcast_anomaly(anomaly):
    disconnected_clients = []
    
    for i, queue in enumerate(anomaly_clients):
        try:
            await queue.put(anomaly)
        except Exception as e:
            logger.error(f"Error broadcasting anomaly to client {i}: {str(e)}")
            disconnected_clients.append(queue)
    
    # Clean up disconnected clients
    for queue in disconnected_clients:
        if queue in anomaly_clients:
            anomaly_clients.remove(queue)