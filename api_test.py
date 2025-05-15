import asyncio
import json
import requests
import signal
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000/api/v1"  # Adjust to your server URL
TIMEOUT = 10  # Timeout for requests in seconds
STREAM_TEST_DURATION = 15  # How long to test each streaming endpoint (in seconds)

class ApiTester:
    def __init__(self):
        self.session = requests.Session()
    
    def close(self):
        self.session.close()
    
    def test_all(self):
        """Run all API tests"""
        test_methods = [
            self.test_anomalies_endpoints,
            self.test_logs_endpoints,
            self.test_statistics_endpoints
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                logger.info(f"✅ {test_method.__name__} completed successfully")
            except Exception as e:
                logger.error(f"❌ {test_method.__name__} failed: {str(e)}")
    
    # === ANOMALIES ENDPOINTS ===
    def test_anomalies_endpoints(self):
        """Test all anomaly endpoints"""
        logger.info("Testing anomalies endpoints...")
        
        # Test basic anomalies endpoint
        logger.info("Testing GET /anomalies/")
        response = self.session.get(f"{BASE_URL}/anomalies/", timeout=TIMEOUT)
        self._check_response(response)
        
        # Test with filters
        params = {
            'skip': 0,
            'limit': 10,
            'classification_type': 'anomaly',
            'start_time': (datetime.now() - timedelta(days=7)).isoformat(),
            'end_time': datetime.now().isoformat()
        }
        logger.info("Testing GET /anomalies/ with filters")
        response = self.session.get(f"{BASE_URL}/anomalies/", params=params, timeout=TIMEOUT)
        self._check_response(response)
        
        # Test recent anomalies
        logger.info("Testing GET /anomalies/recent")
        response = self.session.get(f"{BASE_URL}/anomalies/recent", params={'hours': 48, 'limit': 5}, timeout=TIMEOUT)
        self._check_response(response)
        
        # Test unidentified anomalies
        logger.info("Testing GET /anomalies/unidentified")
        response = self.session.get(f"{BASE_URL}/anomalies/unidentified", params={'hours': 48, 'limit': 5}, timeout=TIMEOUT)
        self._check_response(response)
        
        # Note: Stream endpoints are tested separately
    
    # === LOGS ENDPOINTS ===
    def test_logs_endpoints(self):
        """Test all logs endpoints"""
        logger.info("Testing logs endpoints...")
        
        # Test basic logs endpoint
        logger.info("Testing GET /logs/")
        response = self.session.get(f"{BASE_URL}/logs/", timeout=TIMEOUT)
        self._check_response(response)
        
        # Test with filters
        params = {
            'skip': 0,
            'limit': 20,
            'log_level': 'ERROR',
            'start_time': (datetime.now() - timedelta(days=3)).isoformat(),
            'end_time': datetime.now().isoformat()
        }
        logger.info("Testing GET /logs/ with filters")
        response = self.session.get(f"{BASE_URL}/logs/", params=params, timeout=TIMEOUT)
        self._check_response(response)
    
    # === STATISTICS ENDPOINTS ===
    def test_statistics_endpoints(self):
        """Test all statistics endpoints"""
        logger.info("Testing statistics endpoints...")
        
        # Test classifications endpoint
        logger.info("Testing GET /statistics/classifications")
        response = self.session.get(f"{BASE_URL}/statistics/classifications", timeout=TIMEOUT)
        self._check_response(response)
        
        # Test with filters
        params = {
            'skip': 0,
            'limit': 15,
            'start_time': (datetime.now() - timedelta(days=5)).isoformat(),
            'end_time': datetime.now().isoformat()
        }
        logger.info("Testing GET /statistics/classifications with filters")
        response = self.session.get(f"{BASE_URL}/statistics/classifications", params=params, timeout=TIMEOUT)
        self._check_response(response)
        
        # Test time-series endpoint
        logger.info("Testing GET /statistics/time-series")
        response = self.session.get(f"{BASE_URL}/statistics/time-series", 
                                   params={'interval_minutes': 10, 'hours': 72}, 
                                   timeout=TIMEOUT)
        self._check_response(response)
        
        # Test summary endpoint
        logger.info("Testing GET /statistics/summary")
        response = self.session.get(f"{BASE_URL}/statistics/summary", 
                                   params={'hours': 48}, 
                                   timeout=TIMEOUT)
        self._check_response(response)
    
    def _check_response(self, response):
        """Check HTTP response and log results"""
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                logger.info(f"Received {len(data)} items")
            else:
                logger.info(f"Received data: {json.dumps(data)[:100]}...")
        else:
            logger.error(f"Request failed with status {response.status_code}: {response.text}")
            raise Exception(f"API request failed with status {response.status_code}")


def test_sse_endpoints():
    """Test SSE endpoints using curl (non-blocking)"""
    import subprocess
    import threading
    import time
    
    def run_curl_command(url, duration):
        logger.info(f"Testing SSE endpoint: {url}")
        # Run curl with a timeout to test SSE endpoint
        cmd = ["curl", "-N", url]
        try:
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for the specified duration
            time.sleep(duration)
            
            # Terminate the process
            process.terminate()
            process.wait(timeout=1)
            
            logger.info(f"Completed SSE test for {url}")
        except Exception as e:
            logger.error(f"Error testing SSE endpoint {url}: {str(e)}")
    
    # Test all SSE endpoints
    sse_endpoints = [
        f"{BASE_URL}/anomalies/stream",
        f"{BASE_URL}/logs/stream",
        f"{BASE_URL}/statistics/stream"
    ]
    
    threads = []
    for endpoint in sse_endpoints:
        thread = threading.Thread(target=run_curl_command, args=(endpoint, STREAM_TEST_DURATION))
        thread.daemon = True
        thread.start()
        threads.append(thread)
        time.sleep(1)  # Stagger the connections
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()


def main():
    """Main entry point"""
    tester = ApiTester()
    try:
        logger.info("Starting API tests")
        tester.test_all()
        
        # Test SSE endpoints separately using curl
        test_sse_endpoints()
        
        logger.info("API tests completed")
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
    finally:
        tester.close()

if __name__ == "__main__":
    main()