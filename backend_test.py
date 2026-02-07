#!/usr/bin/env python3
"""
Backend API Testing for Idolcode Dashboard APIs
Tests all backend endpoints comprehensively including:
- User Info API
- User Stats API  
- Idol Journey API
- User Solved Problems API
- Compare Users API
- Codeforces User Search API
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

def validate_user_info(user_info: Dict[str, Any]) -> List[str]:
    """Validate UserInfo response structure"""
    errors = []
    
    # Required field: handle
    if "handle" not in user_info or not isinstance(user_info["handle"], str):
        errors.append("Missing or invalid 'handle' field")
    
    # Optional fields with type validation
    optional_int_fields = ["rating", "maxRating", "contribution", "friendOfCount", "registrationTimeSeconds"]
    for field in optional_int_fields:
        if field in user_info and user_info[field] is not None:
            if not isinstance(user_info[field], int):
                errors.append(f"Field '{field}' should be int or null, got {type(user_info[field])}")
    
    optional_str_fields = ["rank", "maxRank", "avatar", "titlePhoto"]
    for field in optional_str_fields:
        if field in user_info and user_info[field] is not None:
            if not isinstance(user_info[field], str):
                errors.append(f"Field '{field}' should be string or null, got {type(user_info[field])}")
    
    return errors

def validate_user_stats(user_stats: Dict[str, Any]) -> List[str]:
    """Validate UserStats response structure"""
    errors = []
    
    # Required field: handle
    if "handle" not in user_stats or not isinstance(user_stats["handle"], str):
        errors.append("Missing or invalid 'handle' field")
    
    # Required int fields
    required_int_fields = ["problemsSolved", "contestsParticipated", "contestWins"]
    for field in required_int_fields:
        if field not in user_stats:
            errors.append(f"Missing required field '{field}'")
        elif not isinstance(user_stats[field], int):
            errors.append(f"Field '{field}' should be int, got {type(user_stats[field])}")
        elif user_stats[field] < 0:
            errors.append(f"Field '{field}' should not be negative, got {user_stats[field]}")
    
    # Optional fields
    optional_int_fields = ["rating", "maxRating"]
    for field in optional_int_fields:
        if field in user_stats and user_stats[field] is not None:
            if not isinstance(user_stats[field], int):
                errors.append(f"Field '{field}' should be int or null, got {type(user_stats[field])}")
    
    optional_str_fields = ["rank", "maxRank"]
    for field in optional_str_fields:
        if field in user_stats and user_stats[field] is not None:
            if not isinstance(user_stats[field], str):
                errors.append(f"Field '{field}' should be string or null, got {type(user_stats[field])}")
    
    return errors

def validate_idol_journey(journey: Dict[str, Any]) -> List[str]:
    """Validate IdolJourney response structure"""
    errors = []
    
    # Required fields
    if "problems" not in journey:
        errors.append("Missing 'problems' field")
    elif not isinstance(journey["problems"], list):
        errors.append(f"Field 'problems' should be list, got {type(journey['problems'])}")
    
    if "totalProblems" not in journey:
        errors.append("Missing 'totalProblems' field")
    elif not isinstance(journey["totalProblems"], int):
        errors.append(f"Field 'totalProblems' should be int, got {type(journey['totalProblems'])}")
    
    if "hasMore" not in journey:
        errors.append("Missing 'hasMore' field")
    elif not isinstance(journey["hasMore"], bool):
        errors.append(f"Field 'hasMore' should be bool, got {type(journey['hasMore'])}")
    
    # Validate problem structure
    if "problems" in journey and isinstance(journey["problems"], list):
        for i, problem in enumerate(journey["problems"]):
            if not isinstance(problem, dict):
                errors.append(f"Problem {i} should be dict, got {type(problem)}")
                continue
            
            # Required problem fields
            required_fields = ["problemId", "name", "index"]
            for field in required_fields:
                if field not in problem:
                    errors.append(f"Problem {i} missing '{field}' field")
                elif not isinstance(problem[field], str):
                    errors.append(f"Problem {i} field '{field}' should be string, got {type(problem[field])}")
            
            # Optional problem fields
            if "tags" in problem and not isinstance(problem["tags"], list):
                errors.append(f"Problem {i} field 'tags' should be list, got {type(problem['tags'])}")
    
    return errors

def validate_comparison_data(comparison: Dict[str, Any]) -> List[str]:
    """Validate ComparisonData response structure"""
    errors = []
    
    # Required fields
    if "user" not in comparison:
        errors.append("Missing 'user' field")
    elif not isinstance(comparison["user"], dict):
        errors.append(f"Field 'user' should be dict, got {type(comparison['user'])}")
    else:
        user_errors = validate_user_stats(comparison["user"])
        errors.extend([f"User stats: {err}" for err in user_errors])
    
    if "idol" not in comparison:
        errors.append("Missing 'idol' field")
    elif not isinstance(comparison["idol"], dict):
        errors.append(f"Field 'idol' should be dict, got {type(comparison['idol'])}")
    else:
        idol_errors = validate_user_stats(comparison["idol"])
        errors.extend([f"Idol stats: {err}" for err in idol_errors])
    
    if "progressPercent" not in comparison:
        errors.append("Missing 'progressPercent' field")
    elif not isinstance(comparison["progressPercent"], (int, float)):
        errors.append(f"Field 'progressPercent' should be number, got {type(comparison['progressPercent'])}")
    elif not (0 <= comparison["progressPercent"] <= 100):
        errors.append(f"Field 'progressPercent' should be 0-100, got {comparison['progressPercent']}")
    
    if "userAhead" not in comparison:
        errors.append("Missing 'userAhead' field")
    elif not isinstance(comparison["userAhead"], bool):
        errors.append(f"Field 'userAhead' should be bool, got {type(comparison['userAhead'])}")
    
    return errors

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

def run_user_info_tests():
    """Test User Info API endpoints"""
    print("\n" + "=" * 80)
    print("🔍 USER INFO API TESTING")
    print("=" * 80)
    
    test_results = []
    
    # Test Case 1: Valid handle - tourist
    print("\n📋 TEST CASE 1: Get user info for 'tourist'")
    result = test_api_endpoint("/user/tourist/info")
    test_results.append(("User info - tourist", result))
    
    if result["success"] and result["data"]:
        user_info = result["data"]
        print(f"   ✅ API call successful")
        print(f"   📊 Handle: {user_info.get('handle', 'N/A')}")
        print(f"   📊 Rating: {user_info.get('rating', 'N/A')}")
        print(f"   📊 Rank: {user_info.get('rank', 'N/A')}")
        print(f"   📊 Max Rating: {user_info.get('maxRating', 'N/A')}")
        print(f"   📊 Max Rank: {user_info.get('maxRank', 'N/A')}")
        print(f"   📊 Avatar: {'Present' if user_info.get('avatar') else 'N/A'}")
        
        # Validate structure
        errors = validate_user_info(user_info)
        if errors:
            print(f"   ❌ Validation errors: {errors}")
        else:
            print("   ✅ Response format valid")
    
    # Test Case 2: Valid handle - Errichto
    print("\n📋 TEST CASE 2: Get user info for 'Errichto'")
    result = test_api_endpoint("/user/Errichto/info")
    test_results.append(("User info - Errichto", result))
    
    if result["success"] and result["data"]:
        user_info = result["data"]
        print(f"   ✅ API call successful")
        print(f"   📊 Handle: {user_info.get('handle', 'N/A')}")
        print(f"   📊 Rating: {user_info.get('rating', 'N/A')}")
        print(f"   📊 Rank: {user_info.get('rank', 'N/A')}")
        
        # Validate structure
        errors = validate_user_info(user_info)
        if errors:
            print(f"   ❌ Validation errors: {errors}")
        else:
            print("   ✅ Response format valid")
    
    # Test Case 3: Invalid handle
    print("\n📋 TEST CASE 3: Get user info for invalid handle")
    result = test_api_endpoint("/user/nonexistent_user_12345/info")
    test_results.append(("User info - invalid", result))
    
    if result["success"]:
        print("   ❌ Expected 404 error for invalid user")
    elif result["status_code"] == 404:
        print("   ✅ Correctly returned 404 for invalid user")
    else:
        print(f"   ⚠️  Unexpected status code: {result['status_code']}")
    
    return test_results

def run_user_stats_tests():
    """Test User Stats API endpoints"""
    print("\n" + "=" * 80)
    print("📊 USER STATS API TESTING")
    print("=" * 80)
    
    test_results = []
    
    # Test Case 1: Valid handle - tourist
    print("\n📋 TEST CASE 1: Get user stats for 'tourist'")
    result = test_api_endpoint("/user/tourist/stats")
    test_results.append(("User stats - tourist", result))
    
    if result["success"] and result["data"]:
        stats = result["data"]
        print(f"   ✅ API call successful")
        print(f"   📊 Handle: {stats.get('handle', 'N/A')}")
        print(f"   📊 Problems Solved: {stats.get('problemsSolved', 'N/A')}")
        print(f"   📊 Contests Participated: {stats.get('contestsParticipated', 'N/A')}")
        print(f"   📊 Contest Wins: {stats.get('contestWins', 'N/A')}")
        print(f"   📊 Rating: {stats.get('rating', 'N/A')}")
        
        # Validate structure and reasonable values
        errors = validate_user_stats(stats)
        if errors:
            print(f"   ❌ Validation errors: {errors}")
        else:
            print("   ✅ Response format valid")
            
        # Check for reasonable values
        problems_solved = stats.get('problemsSolved', 0)
        contests = stats.get('contestsParticipated', 0)
        wins = stats.get('contestWins', 0)
        
        if problems_solved > 10000:
            print(f"   ⚠️  Very high problems solved: {problems_solved}")
        if contests > 1000:
            print(f"   ⚠️  Very high contests participated: {contests}")
        if wins > contests:
            print(f"   ❌ Contest wins ({wins}) cannot exceed contests participated ({contests})")
        else:
            print("   ✅ Stats values are reasonable")
    
    # Test Case 2: Valid handle - Errichto
    print("\n📋 TEST CASE 2: Get user stats for 'Errichto'")
    result = test_api_endpoint("/user/Errichto/stats")
    test_results.append(("User stats - Errichto", result))
    
    if result["success"] and result["data"]:
        stats = result["data"]
        print(f"   ✅ API call successful")
        print(f"   📊 Handle: {stats.get('handle', 'N/A')}")
        print(f"   📊 Problems Solved: {stats.get('problemsSolved', 'N/A')}")
        print(f"   📊 Contests Participated: {stats.get('contestsParticipated', 'N/A')}")
        print(f"   📊 Contest Wins: {stats.get('contestWins', 'N/A')}")
        
        # Validate structure
        errors = validate_user_stats(stats)
        if errors:
            print(f"   ❌ Validation errors: {errors}")
        else:
            print("   ✅ Response format valid")
    
    return test_results

def run_idol_journey_tests():
    """Test Idol Journey API endpoints"""
    print("\n" + "=" * 80)
    print("🚀 IDOL JOURNEY API TESTING")
    print("=" * 80)
    
    test_results = []
    
    # Test Case 1: Basic journey for tourist
    print("\n📋 TEST CASE 1: Get idol journey for 'tourist' (default pagination)")
    result = test_api_endpoint("/idol/tourist/journey")
    test_results.append(("Idol journey - tourist default", result))
    
    if result["success"] and result["data"]:
        journey = result["data"]
        print(f"   ✅ API call successful")
        print(f"   📊 Total Problems: {journey.get('totalProblems', 'N/A')}")
        print(f"   📊 Problems in Response: {len(journey.get('problems', []))}")
        print(f"   📊 Has More: {journey.get('hasMore', 'N/A')}")
        
        # Validate structure
        errors = validate_idol_journey(journey)
        if errors:
            print(f"   ❌ Validation errors: {errors}")
        else:
            print("   ✅ Response format valid")
            
        # Check first few problems
        problems = journey.get('problems', [])
        if problems:
            print(f"   📊 First problem: {problems[0].get('name', 'N/A')} (ID: {problems[0].get('problemId', 'N/A')})")
            if len(problems) > 1:
                print(f"   📊 Second problem: {problems[1].get('name', 'N/A')} (ID: {problems[1].get('problemId', 'N/A')})")
    
    # Test Case 2: Pagination test - offset=0, limit=10
    print("\n📋 TEST CASE 2: Get idol journey with pagination (offset=0, limit=10)")
    result = test_api_endpoint("/idol/tourist/journey", {"offset": 0, "limit": 10})
    test_results.append(("Idol journey - pagination 1", result))
    
    if result["success"] and result["data"]:
        journey = result["data"]
        print(f"   ✅ API call successful")
        problems = journey.get('problems', [])
        print(f"   📊 Problems returned: {len(problems)}")
        print(f"   📊 Has More: {journey.get('hasMore', 'N/A')}")
        
        if len(problems) <= 10:
            print("   ✅ Pagination limit respected")
        else:
            print(f"   ❌ Pagination limit not respected: got {len(problems)} > 10")
    
    # Test Case 3: Pagination test - offset=50, limit=50
    print("\n📋 TEST CASE 3: Get idol journey with pagination (offset=50, limit=50)")
    result = test_api_endpoint("/idol/tourist/journey", {"offset": 50, "limit": 50})
    test_results.append(("Idol journey - pagination 2", result))
    
    if result["success"] and result["data"]:
        journey = result["data"]
        print(f"   ✅ API call successful")
        problems = journey.get('problems', [])
        print(f"   📊 Problems returned: {len(problems)}")
        print(f"   📊 Has More: {journey.get('hasMore', 'N/A')}")
        
        if len(problems) <= 50:
            print("   ✅ Pagination limit respected")
        else:
            print(f"   ❌ Pagination limit not respected: got {len(problems)} > 50")
            
        # Validate problem structure
        if problems:
            problem = problems[0]
            required_fields = ["problemId", "name", "rating", "tags", "solvedAt", "ratingAtSolve", "wasContestSolve"]
            missing_fields = [field for field in required_fields if field not in problem]
            if missing_fields:
                print(f"   ❌ Missing problem fields: {missing_fields}")
            else:
                print("   ✅ Problem structure complete")
                print(f"   📊 Sample problem: {problem.get('name', 'N/A')} (Rating: {problem.get('rating', 'N/A')})")
    
    return test_results

def run_solved_problems_tests():
    """Test User Solved Problems API endpoints"""
    print("\n" + "=" * 80)
    print("✅ USER SOLVED PROBLEMS API TESTING")
    print("=" * 80)
    
    test_results = []
    
    # Test Case 1: Get solved problems for Errichto
    print("\n📋 TEST CASE 1: Get solved problems for 'Errichto'")
    result = test_api_endpoint("/user/Errichto/solved-problems")
    test_results.append(("Solved problems - Errichto", result))
    
    if result["success"] and result["data"]:
        data = result["data"]
        print(f"   ✅ API call successful")
        print(f"   📊 Handle: {data.get('handle', 'N/A')}")
        
        solved_problems = data.get('solvedProblems', [])
        print(f"   📊 Solved Problems Count: {len(solved_problems)}")
        
        if solved_problems:
            print(f"   📊 First few problems: {solved_problems[:5]}")
            
            # Validate problem ID format
            valid_format = True
            for problem_id in solved_problems[:10]:  # Check first 10
                if not isinstance(problem_id, str) or not problem_id:
                    print(f"   ❌ Invalid problem ID format: {problem_id}")
                    valid_format = False
                    break
            
            if valid_format:
                print("   ✅ Problem ID format valid")
        
        # Validate response structure
        if "handle" not in data or "solvedProblems" not in data:
            print("   ❌ Missing required fields in response")
        elif not isinstance(data["solvedProblems"], list):
            print("   ❌ solvedProblems should be a list")
        else:
            print("   ✅ Response structure valid")
    
    return test_results

def run_compare_users_tests():
    """Test Compare Users API endpoints"""
    print("\n" + "=" * 80)
    print("⚖️  COMPARE USERS API TESTING")
    print("=" * 80)
    
    test_results = []
    
    # Test Case 1: Compare Errichto to tourist
    print("\n📋 TEST CASE 1: Compare 'Errichto' to 'tourist'")
    result = test_api_endpoint("/compare/Errichto/tourist")
    test_results.append(("Compare users - Errichto vs tourist", result))
    
    if result["success"] and result["data"]:
        comparison = result["data"]
        print(f"   ✅ API call successful")
        
        user_stats = comparison.get('user', {})
        idol_stats = comparison.get('idol', {})
        
        print(f"   📊 User: {user_stats.get('handle', 'N/A')} (Rating: {user_stats.get('rating', 'N/A')})")
        print(f"   📊 Idol: {idol_stats.get('handle', 'N/A')} (Rating: {idol_stats.get('rating', 'N/A')})")
        print(f"   📊 Progress Percent: {comparison.get('progressPercent', 'N/A')}%")
        print(f"   📊 User Ahead: {comparison.get('userAhead', 'N/A')}")
        
        # Validate structure
        errors = validate_comparison_data(comparison)
        if errors:
            print(f"   ❌ Validation errors: {errors}")
        else:
            print("   ✅ Response format valid")
            
        # Validate progress percentage is reasonable
        progress = comparison.get('progressPercent', 0)
        if 0 <= progress <= 100:
            print("   ✅ Progress percentage is reasonable")
        else:
            print(f"   ❌ Progress percentage out of range: {progress}")
    
    return test_results

def run_comprehensive_dashboard_tests():
    """Run all Idolcode dashboard API tests"""
    print("=" * 80)
    print("🚀 IDOLCODE DASHBOARD API COMPREHENSIVE TESTING")
    print("=" * 80)
    
    all_results = []
    
    # Run all test suites
    all_results.extend(run_user_info_tests())
    all_results.extend(run_user_stats_tests())
    all_results.extend(run_idol_journey_tests())
    all_results.extend(run_solved_problems_tests())
    all_results.extend(run_compare_users_tests())
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in all_results:
        if result["success"]:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED - {result['error']}")
            failed += 1
    
    print(f"\n📈 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All dashboard API tests passed! Backend is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the API implementation.")
        return False
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

def run_comprehensive_dashboard_tests():
    """Run all Idolcode dashboard API tests"""
    print("=" * 80)
    print("🚀 IDOLCODE DASHBOARD API COMPREHENSIVE TESTING")
    print("=" * 80)
    
    all_results = []
    
    # Run all test suites
    all_results.extend(run_user_info_tests())
    all_results.extend(run_user_stats_tests())
    all_results.extend(run_idol_journey_tests())
    all_results.extend(run_solved_problems_tests())
    all_results.extend(run_compare_users_tests())
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in all_results:
        if result["success"]:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED - {result['error']}")
            failed += 1
    
    print(f"\n📈 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All dashboard API tests passed! Backend is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the API implementation.")
        return False

if __name__ == "__main__":
    # Run comprehensive dashboard tests
    print("Starting Idolcode Dashboard API Testing...")
    dashboard_success = run_comprehensive_dashboard_tests()
    
    print(f"\n🏁 OVERALL RESULT: {'SUCCESS' if dashboard_success else 'FAILED'}")
    sys.exit(0 if dashboard_success else 1)