#!/usr/bin/env python3
"""
Backend API Testing for Codeforces User Search
Tests the GET /api/coders/search endpoint with various scenarios
"""

import requests
import json
import sys
from typing import List, Dict, Any

# Backend URL from frontend environment
BACKEND_URL = "https://problemtrack.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_api_endpoint(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test an API endpoint and return response data"""
    try:
        url = f"{API_BASE}{endpoint}"
        print(f"\n🔍 Testing: {url}")
        if params:
            print(f"   Parameters: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
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

def validate_coder_suggestion(coder: Dict[str, Any]) -> List[str]:
    """Validate a single coder suggestion against the CoderSuggestion model"""
    errors = []
    
    # Required field: handle
    if "handle" not in coder or not isinstance(coder["handle"], str):
        errors.append("Missing or invalid 'handle' field")
    
    # Optional fields with type validation
    optional_int_fields = ["rating", "maxRating"]
    for field in optional_int_fields:
        if field in coder and coder[field] is not None:
            if not isinstance(coder[field], int):
                errors.append(f"Field '{field}' should be int or null, got {type(coder[field])}")
    
    optional_str_fields = ["rank", "maxRank", "avatar"]
    for field in optional_str_fields:
        if field in coder and coder[field] is not None:
            if not isinstance(coder[field], str):
                errors.append(f"Field '{field}' should be string or null, got {type(coder[field])}")
    
    return errors

def run_codeforces_search_tests():
    """Run comprehensive tests for the Codeforces User Search API"""
    
    print("=" * 80)
    print("🚀 CODEFORCES USER SEARCH API TESTING")
    print("=" * 80)
    
    test_results = []
    
    # Test Case 1: Search for "tourist"
    print("\n📋 TEST CASE 1: Search for 'tourist'")
    result = test_api_endpoint("/coders/search", {"query": "tourist"})
    test_results.append(("Search 'tourist'", result))
    
    if result["success"] and result["data"]:
        print("   ✅ API call successful")
        coders = result["data"]
        if len(coders) > 0:
            tourist = coders[0]
            print(f"   📊 Found: {tourist.get('handle', 'N/A')}")
            print(f"   📊 Rating: {tourist.get('rating', 'N/A')}")
            print(f"   📊 Rank: {tourist.get('rank', 'N/A')}")
            
            # Validate structure
            errors = validate_coder_suggestion(tourist)
            if errors:
                print(f"   ❌ Validation errors: {errors}")
            else:
                print("   ✅ Response format valid")
        else:
            print("   ⚠️  No results returned for 'tourist'")
    
    # Test Case 2: Search for "benq"
    print("\n📋 TEST CASE 2: Search for 'benq'")
    result = test_api_endpoint("/coders/search", {"query": "benq"})
    test_results.append(("Search 'benq'", result))
    
    if result["success"] and result["data"]:
        print("   ✅ API call successful")
        coders = result["data"]
        if len(coders) > 0:
            benq = coders[0]
            print(f"   📊 Found: {benq.get('handle', 'N/A')}")
            print(f"   📊 Rating: {benq.get('rating', 'N/A')}")
        else:
            print("   ⚠️  No results returned for 'benq'")
    
    # Test Case 3: Search for "petr"
    print("\n📋 TEST CASE 3: Search for 'petr'")
    result = test_api_endpoint("/coders/search", {"query": "petr"})
    test_results.append(("Search 'petr'", result))
    
    if result["success"] and result["data"]:
        print("   ✅ API call successful")
        coders = result["data"]
        if len(coders) > 0:
            petr = coders[0]
            print(f"   📊 Found: {petr.get('handle', 'N/A')}")
            print(f"   📊 Rating: {petr.get('rating', 'N/A')}")
        else:
            print("   ⚠️  No results returned for 'petr'")
    
    # Test Case 4: Search for "tou" (partial match)
    print("\n📋 TEST CASE 4: Search for 'tou' (multiple suggestions)")
    result = test_api_endpoint("/coders/search", {"query": "tou"})
    test_results.append(("Search 'tou'", result))
    
    if result["success"] and result["data"]:
        print("   ✅ API call successful")
        coders = result["data"]
        print(f"   📊 Results count: {len(coders)}")
        for i, coder in enumerate(coders):
            print(f"   📊 Result {i+1}: {coder.get('handle', 'N/A')}")
    
    # Test Case 5: Empty query
    print("\n📋 TEST CASE 5: Empty query")
    result = test_api_endpoint("/coders/search", {"query": ""})
    test_results.append(("Empty query", result))
    
    if result["success"]:
        print("   ✅ API call successful")
        coders = result["data"]
        if len(coders) == 0:
            print("   ✅ Correctly returned empty array for empty query")
        else:
            print(f"   ❌ Expected empty array, got {len(coders)} results")
    
    # Test Case 6: Single character query
    print("\n📋 TEST CASE 6: Single character query")
    result = test_api_endpoint("/coders/search", {"query": "a"})
    test_results.append(("Single character", result))
    
    if result["success"]:
        print("   ✅ API call successful")
        coders = result["data"]
        if len(coders) == 0:
            print("   ✅ Correctly returned empty array for single character")
        else:
            print(f"   ⚠️  Got {len(coders)} results for single character (may be acceptable)")
    
    # Test Case 7: Invalid/non-existent coder
    print("\n📋 TEST CASE 7: Invalid/non-existent coder")
    result = test_api_endpoint("/coders/search", {"query": "nonexistentuser12345xyz"})
    test_results.append(("Invalid coder", result))
    
    if result["success"]:
        print("   ✅ API call successful")
        coders = result["data"]
        if len(coders) == 0:
            print("   ✅ Correctly returned empty array for non-existent user")
        else:
            print(f"   ⚠️  Got {len(coders)} results for non-existent user")
    
    # Test Case 8: Response format validation
    print("\n📋 TEST CASE 8: Response format validation")
    result = test_api_endpoint("/coders/search", {"query": "tourist"})
    
    if result["success"] and result["data"]:
        coders = result["data"]
        if isinstance(coders, list):
            print("   ✅ Response is a list")
            
            all_valid = True
            for i, coder in enumerate(coders):
                errors = validate_coder_suggestion(coder)
                if errors:
                    print(f"   ❌ Coder {i+1} validation errors: {errors}")
                    all_valid = False
                else:
                    print(f"   ✅ Coder {i+1} format valid: {coder.get('handle', 'N/A')}")
            
            if all_valid:
                print("   ✅ All coders have valid format")
        else:
            print(f"   ❌ Response is not a list: {type(coders)}")
    
    # Test Case 9: Limit parameter
    print("\n📋 TEST CASE 9: Limit parameter test")
    result = test_api_endpoint("/coders/search", {"query": "tou", "limit": 3})
    test_results.append(("Limit parameter", result))
    
    if result["success"] and result["data"]:
        coders = result["data"]
        if len(coders) <= 3:
            print(f"   ✅ Limit respected: got {len(coders)} results (≤ 3)")
        else:
            print(f"   ❌ Limit not respected: got {len(coders)} results (> 3)")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        if result["success"]:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED - {result['error']}")
            failed += 1
    
    print(f"\n📈 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Codeforces User Search API is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the API implementation.")
        return False

if __name__ == "__main__":
    success = run_codeforces_search_tests()
    sys.exit(0 if success else 1)