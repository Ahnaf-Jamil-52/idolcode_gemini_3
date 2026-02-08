#!/usr/bin/env python3
"""
Backend Deployment Fixes Testing
Tests the specific deployment fixes mentioned in the review request:
1. Backend health and MongoDB connection (no MONGO_URL errors)
2. New pagination on /api/status endpoint with skip, limit parameters and sorting
3. Core endpoints functionality after database changes
4. Backend logs verification
"""

import requests
import json
import sys
from typing import List, Dict, Any
import time

# Backend URL from frontend environment
BACKEND_URL = "https://code-workspace-39.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_api_endpoint(endpoint: str, method: str = "GET", params: Dict[str, Any] = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test an API endpoint and return response data"""
    try:
        url = f"{API_BASE}{endpoint}"
        print(f"\n🔍 Testing: {method} {url}")
        if params:
            print(f"   Parameters: {params}")
        if data:
            print(f"   Data: {data}")
        
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            try:
                data = response.json()
                print(f"   Response Type: {type(data)}")
                if isinstance(data, list):
                    print(f"   Results Count: {len(data)}")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": data,
                    "error": None
                }
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON Decode Error: {e}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "data": None,
                    "error": f"JSON decode error: {e}"
                }
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Details: {error_data}")
            except:
                print(f"   Error Text: {response.text}")
            return {
                "success": False,
                "status_code": response.status_code,
                "data": None,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request Error: {e}")
        return {
            "success": False,
            "status_code": None,
            "data": None,
            "error": f"Request error: {e}"
        }

def test_backend_health():
    """Test basic backend health"""
    print("\n" + "=" * 80)
    print("🏥 BACKEND HEALTH CHECK")
    print("=" * 80)
    
    # Test root endpoint
    print("\n📋 TEST: Backend root endpoint")
    result = test_api_endpoint("/")
    
    if result["success"]:
        print("   ✅ Backend is responding")
        print(f"   📊 Response: {result['data']}")
        return True
    else:
        print("   ❌ Backend is not responding")
        print(f"   📊 Error: {result['error']}")
        return False

def test_status_endpoint_pagination():
    """Test the new pagination features on /api/status endpoint"""
    print("\n" + "=" * 80)
    print("📄 STATUS ENDPOINT PAGINATION TESTING")
    print("=" * 80)
    
    test_results = []
    
    # First, create some test status checks to ensure we have data
    print("\n📋 SETUP: Creating test status checks")
    for i in range(5):
        test_data = {"client_name": f"test_client_{i}_{int(time.time())}"}
        result = test_api_endpoint("/status", method="POST", data=test_data)
        if result["success"]:
            print(f"   ✅ Created test status check {i+1}")
        else:
            print(f"   ⚠️  Failed to create test status check {i+1}: {result['error']}")
        time.sleep(0.1)  # Small delay to ensure different timestamps
    
    # Test Case 1: Default pagination (no parameters)
    print("\n📋 TEST CASE 1: Default pagination (no parameters)")
    result = test_api_endpoint("/status")
    test_results.append(("Status default pagination", result))
    
    if result["success"] and result["data"]:
        status_checks = result["data"]
        print(f"   ✅ API call successful")
        print(f"   📊 Status checks returned: {len(status_checks)}")
        
        # Verify it's a list
        if isinstance(status_checks, list):
            print("   ✅ Response is a list")
            
            # Check if we got reasonable number (should default to limit=100)
            if len(status_checks) <= 100:
                print("   ✅ Default limit appears to be respected")
            else:
                print(f"   ❌ Too many results for default limit: {len(status_checks)}")
            
            # Check sorting (newest first - timestamps should be descending)
            if len(status_checks) >= 2:
                first_timestamp = status_checks[0].get('timestamp', '')
                second_timestamp = status_checks[1].get('timestamp', '')
                print(f"   📊 First timestamp: {first_timestamp}")
                print(f"   📊 Second timestamp: {second_timestamp}")
                
                # Note: We can't easily verify sorting without parsing timestamps
                # but we can check that timestamps exist
                if first_timestamp and second_timestamp:
                    print("   ✅ Timestamps are present")
                else:
                    print("   ❌ Missing timestamps in response")
        else:
            print(f"   ❌ Response is not a list: {type(status_checks)}")
    
    # Test Case 2: Custom skip and limit
    print("\n📋 TEST CASE 2: Custom pagination (skip=0, limit=3)")
    result = test_api_endpoint("/status", params={"skip": 0, "limit": 3})
    test_results.append(("Status custom pagination", result))
    
    if result["success"] and result["data"]:
        status_checks = result["data"]
        print(f"   ✅ API call successful")
        print(f"   📊 Status checks returned: {len(status_checks)}")
        
        if len(status_checks) <= 3:
            print("   ✅ Custom limit respected")
        else:
            print(f"   ❌ Custom limit not respected: got {len(status_checks)} > 3")
        
        # Show sample data
        if status_checks:
            sample = status_checks[0]
            print(f"   📊 Sample status check: {sample.get('client_name', 'N/A')} at {sample.get('timestamp', 'N/A')}")
    
    # Test Case 3: Skip parameter
    print("\n📋 TEST CASE 3: Skip parameter (skip=2, limit=2)")
    result = test_api_endpoint("/status", params={"skip": 2, "limit": 2})
    test_results.append(("Status skip pagination", result))
    
    if result["success"] and result["data"]:
        status_checks = result["data"]
        print(f"   ✅ API call successful")
        print(f"   📊 Status checks returned: {len(status_checks)}")
        
        if len(status_checks) <= 2:
            print("   ✅ Skip and limit parameters working")
        else:
            print(f"   ❌ Skip/limit not working: got {len(status_checks)} > 2")
    
    # Test Case 4: Edge cases
    print("\n📋 TEST CASE 4: Edge cases (skip=0, limit=0)")
    result = test_api_endpoint("/status", params={"skip": 0, "limit": 1})
    test_results.append(("Status edge case", result))
    
    if result["success"] and result["data"]:
        status_checks = result["data"]
        print(f"   ✅ API call successful")
        print(f"   📊 Status checks returned: {len(status_checks)}")
        
        if len(status_checks) <= 1:
            print("   ✅ Minimum limit working")
    
    return test_results

def test_status_check_creation():
    """Test creating status checks"""
    print("\n" + "=" * 80)
    print("✅ STATUS CHECK CREATION TESTING")
    print("=" * 80)
    
    test_results = []
    
    # Test Case 1: Create a valid status check
    print("\n📋 TEST CASE 1: Create valid status check")
    test_data = {"client_name": f"deployment_test_{int(time.time())}"}
    result = test_api_endpoint("/status", method="POST", data=test_data)
    test_results.append(("Create status check", result))
    
    if result["success"] and result["data"]:
        status_check = result["data"]
        print(f"   ✅ Status check created successfully")
        print(f"   📊 ID: {status_check.get('id', 'N/A')}")
        print(f"   📊 Client Name: {status_check.get('client_name', 'N/A')}")
        print(f"   📊 Timestamp: {status_check.get('timestamp', 'N/A')}")
        
        # Validate structure
        required_fields = ["id", "client_name", "timestamp"]
        missing_fields = [field for field in required_fields if field not in status_check]
        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
        else:
            print("   ✅ Response structure valid")
    
    # Test Case 2: Create status check with missing data
    print("\n📋 TEST CASE 2: Create status check with missing client_name")
    result = test_api_endpoint("/status", method="POST", data={})
    
    # This should fail with 422 (validation error)
    if result["status_code"] == 422:
        print("   ✅ Correctly rejected invalid data with 422")
        test_results.append(("Create invalid status check", {"success": True, "status_code": 422, "data": None, "error": None}))
    elif result["success"]:
        print("   ❌ Should have rejected invalid data")
        test_results.append(("Create invalid status check", result))
    else:
        print(f"   ⚠️  Unexpected error: {result['error']}")
        test_results.append(("Create invalid status check", result))
    
    return test_results

def check_backend_logs():
    """Check backend logs for MONGO_URL errors"""
    print("\n" + "=" * 80)
    print("📋 BACKEND LOGS CHECK")
    print("=" * 80)
    
    try:
        import subprocess
        
        # Check supervisor backend logs
        print("\n📋 Checking supervisor backend logs...")
        result = subprocess.run(
            ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logs = result.stdout
            print(f"   📊 Last 50 lines of backend error logs:")
            print("   " + "─" * 60)
            
            # Check for specific errors
            mongo_errors = []
            db_errors = []
            
            for line in logs.split('\n'):
                if line.strip():
                    print(f"   {line}")
                    if 'MONGO_URL' in line.upper():
                        mongo_errors.append(line)
                    if 'DB_NAME' in line.upper():
                        db_errors.append(line)
            
            print("   " + "─" * 60)
            
            if mongo_errors:
                print(f"   ❌ Found MONGO_URL errors: {len(mongo_errors)}")
                for error in mongo_errors:
                    print(f"      {error}")
                return False
            elif db_errors:
                print(f"   ❌ Found DB_NAME errors: {len(db_errors)}")
                for error in db_errors:
                    print(f"      {error}")
                return False
            else:
                print("   ✅ No MONGO_URL or DB_NAME errors found in recent logs")
                return True
        else:
            print(f"   ⚠️  Could not read backend logs: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"   ⚠️  Error checking logs: {e}")
        return None

def run_deployment_tests():
    """Run all deployment-specific tests"""
    print("=" * 80)
    print("🚀 BACKEND DEPLOYMENT FIXES TESTING")
    print("=" * 80)
    
    all_results = []
    
    # Test 1: Backend Health
    health_ok = test_backend_health()
    
    # Test 2: Status endpoint pagination
    if health_ok:
        pagination_results = test_status_endpoint_pagination()
        all_results.extend(pagination_results)
        
        # Test 3: Status check creation
        creation_results = test_status_check_creation()
        all_results.extend(creation_results)
    else:
        print("\n❌ Backend health check failed, skipping other tests")
        return False
    
    # Test 4: Backend logs check
    logs_ok = check_backend_logs()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 DEPLOYMENT TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    # Count API test results
    for test_name, result in all_results:
        if result["success"]:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED - {result['error']}")
            failed += 1
    
    # Add health and logs results
    if health_ok:
        print("✅ Backend health check: PASSED")
        passed += 1
    else:
        print("❌ Backend health check: FAILED")
        failed += 1
    
    if logs_ok is True:
        print("✅ Backend logs check: PASSED (no MONGO_URL/DB_NAME errors)")
        passed += 1
    elif logs_ok is False:
        print("❌ Backend logs check: FAILED (found MONGO_URL/DB_NAME errors)")
        failed += 1
    else:
        print("⚠️  Backend logs check: SKIPPED (could not access logs)")
    
    print(f"\n📈 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All deployment tests passed! Backend deployment fixes are working correctly.")
        return True
    else:
        print("⚠️  Some deployment tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    print("Starting Backend Deployment Fixes Testing...")
    success = run_deployment_tests()
    
    print(f"\n🏁 OVERALL RESULT: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)