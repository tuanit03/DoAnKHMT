#!/usr/bin/env python3
# api_test.py - Test script for the dashboard API endpoints

import requests
import time
import json
from datetime import datetime, timedelta
import sys

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

# Test result counters
tests_run = 0
tests_passed = 0
tests_failed = 0

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def run_test(name, endpoint, method="GET", params=None, expected_status=200, expected_type=list):
    """Run a test against an API endpoint and validate the response"""
    global tests_run, tests_passed, tests_failed
    tests_run += 1
    
    url = f"{BASE_URL}{endpoint}"
    print(f"\n[TEST {tests_run}] {name}")
    print(f"  URL: {method} {url}")
    
    if params:
        print(f"  Params: {params}")
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        # Add other methods if needed
        
        # Print response details
        print(f"  Status: {response.status_code}")
        print(f"  Time: {response.elapsed.total_seconds():.3f}s")
        
        # Check if the response is valid JSON
        try:
            data = response.json()
            is_json = True
        except json.JSONDecodeError:
            is_json = False
            data = response.text[:100] + "..." if len(response.text) > 100 else response.text
        
        # Validate status code
        if response.status_code != expected_status:
            print(f"  ERROR: Expected status {expected_status}, got {response.status_code}")
            tests_failed += 1
            return False
        
        # If we expect JSON, validate the type of the response
        if is_json and expected_type is not None:
            if expected_type is list and not isinstance(data, list):
                print(f"  ERROR: Expected list, got {type(data).__name__}")
                print(f"  Data: {data}")
                tests_failed += 1
                return False
            elif expected_type is dict and not isinstance(data, dict):
                print(f"  ERROR: Expected dict, got {type(data).__name__}")
                print(f"  Data: {data}")
                tests_failed += 1
                return False
        
        # Print response preview
        if is_json:
            if isinstance(data, list):
                print(f"  Response: List with {len(data)} items")
                if data:
                    print(f"  First item: {json.dumps(data[0], indent=2)[:200]}...")
            else:
                print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"  Response: {data}")
        
        print("  PASSED ✅")
        tests_passed += 1
        return True
        
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        tests_failed += 1
        return False

def test_health_endpoint():
    """Test the API health endpoint"""
    print_header("Testing Health Endpoint")
    run_test("Check API health", "/health", expected_type=dict)

def test_logs_api():
    """Test the logs API endpoints"""
    print_header("Testing Logs API")
    
    # Basic retrieval
    run_test("Get all logs", f"{API_PREFIX}/logs")
    
    # Filtered by log level
    levels = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
    for level in levels:
        run_test(f"Get {level} logs", f"{API_PREFIX}/logs", params={"log_level": level})
    
    # Pagination
    run_test("Paginated logs", f"{API_PREFIX}/logs", params={"skip": 5, "limit": 3})
    
    # Date range filtering
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    run_test(
        "Logs with date range",
        f"{API_PREFIX}/logs",
        params={
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )

def test_statistics_api():
    """Test the statistics API endpoints"""
    print_header("Testing Statistics API")
    
    # Classifications endpoint
    run_test("Get classifications", f"{API_PREFIX}/statistics/classifications")
    
    # Paginated classifications
    run_test(
        "Paginated classifications", 
        f"{API_PREFIX}/statistics/classifications", 
        params={"skip": 5, "limit": 3}
    )
    
    # Time series data
    run_test("Get time series data", f"{API_PREFIX}/statistics/time-series")
    
    # Time series with custom interval
    run_test(
        "Time series with custom interval", 
        f"{API_PREFIX}/statistics/time-series", 
        params={"interval_minutes": 15}
    )
    
    # Time series with custom hours
    run_test(
        "Time series with custom hours", 
        f"{API_PREFIX}/statistics/time-series", 
        params={"hours": 48}
    )
    
    # Summary statistics
    run_test("Get summary statistics", f"{API_PREFIX}/statistics/summary", expected_type=dict)
    
    # Summary with custom hours
    run_test(
        "Summary with custom hours", 
        f"{API_PREFIX}/statistics/summary", 
        params={"hours": 72},
        expected_type=dict
    )

def test_anomalies_api():
    """Test the anomalies API endpoints"""
    print_header("Testing Anomalies API")
    
    # Get all anomaly parameters
    run_test("Get all anomalies", f"{API_PREFIX}/anomalies")
    
    # Filter by classification type
    for classification_type in ["anomaly", "unidentified"]:
        run_test(
            f"Get {classification_type} parameters", 
            f"{API_PREFIX}/anomalies", 
            params={"classification_type": classification_type}
        )
    
    # Pagination
    run_test(
        "Paginated anomalies", 
        f"{API_PREFIX}/anomalies", 
        params={"skip": 5, "limit": 3}
    )
    
    # Recent anomalies
    run_test("Get recent anomalies", f"{API_PREFIX}/anomalies/recent")
    
    # Recent anomalies with custom parameters
    run_test(
        "Recent anomalies with custom parameters", 
        f"{API_PREFIX}/anomalies/recent", 
        params={"hours": 48, "limit": 15}
    )
    
    # Unidentified parameters
    run_test("Get unidentified parameters", f"{API_PREFIX}/anomalies/unidentified")
    
    # Unidentified with custom parameters
    run_test(
        "Unidentified with custom parameters", 
        f"{API_PREFIX}/anomalies/unidentified", 
        params={"hours": 48, "limit": 15}
    )

def print_summary():
    """Print a summary of the test results"""
    print_header("Test Summary")
    print(f"Tests run:    {tests_run}")
    print(f"Tests passed: {tests_passed} ✅")
    print(f"Tests failed: {tests_failed} ❌")
    print("")
    
    if tests_failed == 0:
        print("All tests passed! Your API is functioning correctly.")
    else:
        print(f"Some tests failed. Please check the output above for details.")
    
    print("=" * 80)
    return tests_failed

def test_sse_endpoints():
    """Test SSE endpoints by attempting to connect (but not waiting for events)"""
    global tests_run, tests_passed, tests_failed  # Add this line to fix the issue
    
    print_header("Testing SSE Endpoints")
    
    sse_endpoints = [
        (f"{API_PREFIX}/logs/stream", "logs stream"),
        (f"{API_PREFIX}/statistics/stream", "statistics stream"),
        (f"{API_PREFIX}/anomalies/stream", "anomalies stream")
    ]
    
    for url, name in sse_endpoints:
        tests_run += 1  # Increase test counter
        print(f"\nTesting {name} SSE connection:")
        try:
            # Just test that we can connect, don't wait for events
            response = requests.get(f"{BASE_URL}{url}", stream=True, headers={"Accept": "text/event-stream"}, timeout=2)
            if response.status_code == 200:
                print(f"  Successfully connected to {url}")
                print("  PASSED ✅")
                tests_passed += 1
            else:
                print(f"  Failed to connect: status code {response.status_code}")
                print("  FAILED ❌")
                tests_failed += 1
        except Exception as e:
            print(f"  Error connecting to SSE endpoint: {str(e)}")
            print("  FAILED ❌")
            tests_failed += 1
        finally:
            # Don't stay connected
            if 'response' in locals():
                response.close()

def main():
    """Run all API tests"""
    print("\nANOMALY DETECTION DASHBOARD API TEST\n")
    print(f"Testing API at: {BASE_URL}")
    
    try:
        # Test basic health endpoint first
        test_health_endpoint()
        
        # Test all API endpoints
        test_logs_api()
        test_statistics_api()
        test_anomalies_api()
        test_sse_endpoints()
        
        # Print summary
        failed_count = print_summary()
        
        # Return non-zero exit code if any tests failed
        return 1 if failed_count > 0 else 0
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user. Exiting...")
        return 1
    except Exception as e:
        print(f"\nError running tests: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())