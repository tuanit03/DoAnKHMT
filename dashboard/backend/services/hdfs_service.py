import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class HDFSLogService:
    @staticmethod
    def parse_hdfs_log(message: str) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[str], Optional[str]]:
        """
        Parse HDFS log format and extract components
        Format: "YYMMDD HHMMSS [Thread ID] INFO [HDFS Component]: [Detailed message]"
        
        Returns:
            Tuple of (hdfs_date, hdfs_time, thread_id, hdfs_component, block_id)
        """
        try:
            # Split message into parts
            hdfs_parts = message.split(" ", 5)
            
            if len(hdfs_parts) >= 6:
                hdfs_date = hdfs_parts[0]  # YYMMDD
                hdfs_time = hdfs_parts[1]  # HHMMSS
                
                # Extract thread ID from [Thread ID]
                thread_part = hdfs_parts[2]
                thread_id = None
                if thread_part.startswith('[') and thread_part.endswith(']'):
                    thread_id = int(thread_part[1:-1])
                
                # Extract HDFS Component from [Component]
                component_part = hdfs_parts[4]
                hdfs_component = None
                if component_part.startswith('[') and component_part.endswith(']:'):
                    hdfs_component = component_part[1:-2]
                
                # Extract block ID if present using regex
                block_matches = re.findall(r'blk_[-]?\d{10,19}', message)
                block_id = block_matches[0] if block_matches else None
                
                return hdfs_date, hdfs_time, thread_id, hdfs_component, block_id
        except Exception as e:
            logger.warning(f"Failed to parse HDFS log format: {str(e)}")
        
        return None, None, None, None, None
    
    @staticmethod
    async def get_hdfs_block_stats(
        db: AsyncSession,
        limit: int = 100,
        min_logs: int = 1,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get statistics about HDFS blocks from logs
        """
        # Calculate time range if not provided
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        # Query for block statistics
        query = text("""
            SELECT 
                block_id,
                COUNT(*) as log_count,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen,
                array_agg(DISTINCT log_level) as log_levels,
                array_agg(DISTINCT hdfs_component) as components
            FROM 
                log_entries
            WHERE 
                block_id IS NOT NULL
                AND timestamp BETWEEN :start_time AND :end_time
            GROUP BY 
                block_id
            HAVING 
                COUNT(*) >= :min_logs
            ORDER BY 
                log_count DESC
            LIMIT :limit
        """)
        
        result = await db.execute(
            query, 
            {"start_time": start_time, "end_time": end_time, "min_logs": min_logs, "limit": limit}
        )
        rows = result.fetchall()
        
        # Convert to dictionary format and ensure we always return a list
        blocks = [
            {
                "block_id": row[0],
                "log_count": row[1],
                "first_seen": row[2],
                "last_seen": row[3],
                "log_levels": row[4] if row[4] else [],
                "components": row[5] if row[5] else []
            } for row in rows
        ]
        
        return blocks
    
    @staticmethod
    async def get_component_activity(
        db: AsyncSession, 
        hours: int = 24,
        components: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Get activity counts by HDFS component over the specified time period
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        query = text("""
            SELECT 
                hdfs_component,
                COUNT(*) as log_count
            FROM 
                log_entries
            WHERE 
                hdfs_component IS NOT NULL
                AND timestamp BETWEEN :start_time AND :end_time
                AND (:components_filter::boolean = FALSE OR hdfs_component = ANY(:components))
            GROUP BY 
                hdfs_component
            ORDER BY 
                log_count DESC
        """)
        
        components_filter = components is not None and len(components) > 0
        
        result = await db.execute(
            query, 
            {
                "start_time": start_time, 
                "end_time": end_time,
                "components_filter": components_filter,
                "components": components or []
            }
        )
        rows = result.fetchall()
        
        # Convert to dictionary
        return {row[0]: row[1] for row in rows}
