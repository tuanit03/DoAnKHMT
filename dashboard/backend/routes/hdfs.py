from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import LogEntryResponse
from services.hdfs_service import HDFSLogService
from services.db_service import DBService

# Create a new router for HDFS-specific endpoints
router = APIRouter(prefix="/hdfs", tags=["hdfs"])

@router.get("/blocks", response_model=List[Dict[str, Any]])
async def get_hdfs_blocks(
    hours: Optional[int] = Query(24, description="Number of hours to look back"),
    min_logs: Optional[int] = Query(1, description="Minimum number of logs per block"),
    limit: Optional[int] = Query(100, description="Maximum number of blocks to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about HDFS blocks from logs
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    blocks = await HDFSLogService.get_hdfs_block_stats(
        db, 
        limit=limit,
        min_logs=min_logs,
        start_time=start_time,
        end_time=end_time
    )
    
    return blocks

@router.get("/components", response_model=Dict[str, int])
async def get_component_activity(
    hours: Optional[int] = Query(24, description="Number of hours to look back"),
    components: Optional[List[str]] = Query(None, description="Filter by specific components"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity counts by HDFS component over the specified time period
    """
    activity = await HDFSLogService.get_component_activity(
        db,
        hours=hours,
        components=components
    )
    
    return activity

@router.get("/logs/{block_id}", response_model=List[LogEntryResponse])
async def get_logs_by_block_id(
    block_id: str,
    limit: Optional[int] = Query(100, description="Maximum number of logs to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get logs for a specific HDFS block ID
    """
    if not block_id.startswith("blk_"):
        raise HTTPException(status_code=400, detail="Invalid block ID format")
        
    # Get logs with the specified block ID
    query = f"block_id = '{block_id}'"
    logs = await DBService.get_log_entries(
        db,
        filter_query=query,
        limit=limit
    )
    
    return logs

@router.get("/blocks", response_model=List[Dict[str, Any]])
async def get_hdfs_blocks(
    limit: int = 100,
    min_logs: int = 1,
    hours: Optional[int] = 24,
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about HDFS blocks from logs
    """
    # Calculate time range based on hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours) if hours else None
    
    blocks = await HDFSLogService.get_hdfs_block_stats(
        db=db, 
        limit=limit, 
        min_logs=min_logs,
        start_time=start_time,
        end_time=end_time
    )
    
    return blocks

@router.get("/components", response_model=Dict[str, int])
async def get_component_activity(
    hours: int = 24,
    components: List[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity counts by HDFS component
    """
    activity = await HDFSLogService.get_component_activity(
        db=db,
        hours=hours,
        components=components
    )
    
    return activity

@router.get("/logs/{block_id}", response_model=List[LogEntryResponse])
async def get_logs_by_block(
    block_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all logs related to a specific HDFS block
    """
    from sqlalchemy import select, desc
    from models import LogEntry
    
    query = (
        select(LogEntry)
        .where(LogEntry.block_id == block_id)
        .order_by(desc(LogEntry.timestamp))
        .limit(limit)
    )
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    if not logs:
        raise HTTPException(status_code=404, detail=f"No logs found for block ID {block_id}")
    
    return logs
