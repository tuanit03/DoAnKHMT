import asyncio
import random
import logging
from datetime import datetime
from typing import Callable, List
import ipaddress

import config
from models import LogEntryCreate, ClassificationCreate, AnomalyParamCreate

logger = logging.getLogger(__name__)

# Log level distribution for mock data
LOG_LEVELS = ["INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_LEVEL_WEIGHTS = [0.7, 0.15, 0.1, 0.05]

# HDFS Components
HDFS_COMPONENTS = [
    "dfs.DataNode$PacketResponder",
    "dfs.FSNamesystem",
    "dfs.DataNode$DataXceiver",
    "dfs.DataBlockScanner",
    "namenode.NameNode",
    "dfs.DataNode"
]

# HDFS Log messages for each level
HDFS_LOG_MESSAGES = {
    "INFO": [
        "PacketResponder %d for block %s terminating",
        "BLOCK* NameSystem.addStoredBlock: blockMap updated: %s is added to %s size %d",
        "Receiving block %s src: %s dest: %s",
        "Verification succeeded for %s",
    ],
    "WARNING": [
        "Slow BlockReceiver write data to disk cost %dms",
    ],
    "ERROR": [
        "Exception in receiveBlock for %s",
    ],
    "CRITICAL": [
        "All datanodes are bad. Shutting down",
    ],
}

class MockDataGenerator:
    def __init__(self):
        self.running = False
        self.task = None
        self.log_callbacks = []
        self.classification_callbacks = []
        self.anomaly_param_callbacks = []
        
    def register_log_consumer(self, callback: Callable):
        """Register a callback for log messages"""
        self.log_callbacks.append(callback)
        
    def register_classification_consumer(self, callback: Callable):
        """Register a callback for classification messages"""
        self.classification_callbacks.append(callback)
        
    def register_anomaly_param_consumer(self, callback: Callable):
        """Register a callback for anomaly parameter messages"""
        self.anomaly_param_callbacks.append(callback)
        
    async def start(self):
        """Start generating mock data"""
        if self.running or not config.MOCK_DATA_ENABLED:
            return
            
        logger.info("Starting mock data generator")
        self.running = True
        self.task = asyncio.create_task(self._generate_data())
        
    async def stop(self):
        """Stop generating mock data"""
        if not self.running:
            return
            
        logger.info("Stopping mock data generator")
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
                
        self.task = None
        
    async def _generate_data(self):
        """Generate mock data at regular intervals"""
        try:
            while self.running:
                # Generate log entries
                await self._generate_log_entries()
                
                # Generate classification data
                await self._generate_classification_data()
                
                # Wait before generating more data
                await asyncio.sleep(config.MOCK_DATA_INTERVAL_SECONDS)
                
        except asyncio.CancelledError:
            logger.info("Mock data generation cancelled")
        except Exception as e:
            logger.error(f"Error in mock data generator: {str(e)}")
            
    async def _generate_log_entries(self):
        """Generate mock HDFS log entries"""
        # Generate 1-3 log entries per interval
        num_logs = random.randint(1, 3)
        
        for _ in range(num_logs):
            # Choose log level based on weights
            log_level = random.choices(LOG_LEVELS, weights=LOG_LEVEL_WEIGHTS)[0]
            
            # Select a message template for the chosen level
            message_template = random.choice(HDFS_LOG_MESSAGES[log_level])
            
            # Generate a random block ID - format blk_[10-19 digits]
            block_id = f"blk_{random.randint(1000000000, 9999999999999999999)}"
            if random.random() < 0.3:  # 30% chance for negative block ID
                block_id = f"blk_{-random.randint(1000000000, 9999999999999999999)}"
            
            # Generate random IP addresses (format: 10.x.y.z)
            src_ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
            dest_ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
            
            # Common ports for HDFS
            port = random.choice([50010, 50020])
            
            # Size is typically a multiple of 64MB (expressed in bytes)
            size = 64 * 1024 * 1024 * random.randint(1, 16)
            
            # Fill in template placeholders with random values
            message = message_template
            if "%s" in message:
                if "blockMap updated" in message:
                    ip_port = f"{src_ip}:{port}"
                    message = message.replace("%s", ip_port, 1)
                    message = message.replace("%s", block_id, 1)
                    message = message.replace("%d", str(size), 1)
                elif "Receiving block" in message:
                    message = message.replace("%s", block_id, 1)
                    message = message.replace("%s", f"{src_ip}:{port}", 1)
                    message = message.replace("%s", f"{dest_ip}:{port}", 1)
                elif "Verification succeeded" in message or "Exception in receiveBlock" in message:
                    message = message.replace("%s", block_id, 1)
                else:
                    message = message.replace("%s", block_id, 1)
            
            if "%d" in message:
                if "PacketResponder" in message:
                    message = message.replace("%d", str(random.randint(1, 100)), 1)
                    message = message.replace("%s", block_id, 1)
                elif "cost" in message:
                    message = message.replace("%d", str(random.randint(1000, 10000)), 1)
                else:
                    message = message.replace("%d", str(random.randint(1, 1000)), 1)
            
            # Format date and time according to HDFS standards
            now = datetime.now()
            date_str = now.strftime("%y%m%d")
            time_str = now.strftime("%H%M%S")
            
            # Generate random thread ID (1-999)
            thread_id = random.randint(1, 999)
            
            # Random HDFS component
            hdfs_component = random.choice(HDFS_COMPONENTS)
            
            # Create the formatted HDFS log message
            hdfs_log = f"{date_str} {time_str} [{thread_id}] {log_level} [{hdfs_component}]: {message}"
            
            log_entry = LogEntryCreate(
                message=hdfs_log,
                log_level=log_level,
            )
            
            # Notify callbacks
            for callback in self.log_callbacks:
                await callback(log_entry)
                
    async def _generate_classification_data(self):
        """Generate mock classification data"""
        # Generate classification counts
        # Most data should be normal, with occasional anomalies
        total_events = random.randint(50, 200)
        anomaly_percent = random.uniform(0.01, 0.1)  # 1-10% anomalies
        unidentified_percent = random.uniform(0.01, 0.05)  # 1-5% unidentified
        
        anomaly_count = int(total_events * anomaly_percent)
        unidentified_count = int(total_events * unidentified_percent)
        normal_count = total_events - anomaly_count - unidentified_count
        
        # Create classification object
        classification = ClassificationCreate(
            normal_count=normal_count,
            anomaly_count=anomaly_count,
            unidentified_count=unidentified_count
        )
        
        # Notify callbacks
        for callback in self.classification_callbacks:
            await callback(classification)
            
        # Generate anomaly parameters if there are anomalies
        if anomaly_count > 0:
            # Generate 1-3 anomaly parameters
            num_params = min(3, anomaly_count)
            
            for _ in range(num_params):
            # Generate a random parameter value (e.g., high CPU, network spike, etc.)
                # We'll use HDFS block ID in abnormal scenarios
                block_id = f"blk_{random.randint(1000000000, 9999999999999999999)}"
                if random.random() < 0.3:  # 30% chance for negative block ID
                    block_id = f"blk_{-random.randint(1000000000, 9999999999999999999)}"
                
                param_values = [
                    f"Corrupted block: {block_id}",
                    f"Missing replicas: {block_id}",
                    f"Block verification failed: {block_id}",
                    f"DataNode not responding for block: {block_id}",
                    f"Unexpected checksum for block: {block_id}",
                    f"Block under-replicated: {block_id}"
                ]
                
                anomaly_param = AnomalyParamCreate(
                    param_value=random.choice(param_values),
                    classification_type="anomaly"
                )
                
                # Call the anomaly parameter callbacks
                for callback in self.anomaly_param_callbacks:
                    await callback(anomaly_param)
                
        # Generate unidentified parameters if there are unidentified events
        if unidentified_count > 0:
            # Generate 1-3 unidentified parameters
            num_params = min(3, unidentified_count)
            
            for _ in range(num_params):
                # Generate a random parameter value
                block_id = f"blk_{random.randint(1000000000, 9999999999999999999)}"
                if random.random() < 0.3:  # 30% chance for negative block ID
                    block_id = f"blk_{-random.randint(1000000000, 9999999999999999999)}"
                
                param_values = [
                    f"Unknown block status: {block_id}",
                    f"Inconsistent block metadata: {block_id}",
                    f"Borderline replication factor: {block_id}",
                    f"Unusual access pattern: {block_id}",
                    f"Block state transition delayed: {block_id}"
                ]
                
                unidentified_param = AnomalyParamCreate(
                    param_value=random.choice(param_values),
                    classification_type="unidentified"
                )
                
                # Call the anomaly parameter callbacks
                for callback in self.anomaly_param_callbacks:
                    await callback(unidentified_param)