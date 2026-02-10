from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import asyncio
import re
import hashlib
import secrets
from collections import Counter
from bs4 import BeautifulSoup
import json
from google import genai
from services.recommendation_engine import (
    build_recommendations,
    fetch_user_submissions,
    fetch_user_rating_history,
    fetch_user_info,
    analyze_user_profile,
    analyze_idol_profile
)


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
# Use .get() with defaults for local dev, production will override via env vars
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class CoderSuggestion(BaseModel):
    handle: str
    rating: Optional[int] = None
    rank: Optional[str] = None
    maxRating: Optional[int] = None
    maxRank: Optional[str] = None
    avatar: Optional[str] = None

class UserInfo(BaseModel):
    handle: str
    rating: Optional[int] = None
    rank: Optional[str] = None
    maxRating: Optional[int] = None
    maxRank: Optional[str] = None
    avatar: Optional[str] = None
    titlePhoto: Optional[str] = None
    contribution: Optional[int] = None
    friendOfCount: Optional[int] = None
    registrationTimeSeconds: Optional[int] = None

class UserStats(BaseModel):
    handle: str
    rating: Optional[int] = None
    rank: Optional[str] = None
    maxRating: Optional[int] = None
    maxRank: Optional[str] = None
    problemsSolved: int = 0
    contestsParticipated: int = 0
    contestWins: int = 0  # Times finished in top 10

class ProblemInfo(BaseModel):
    contestId: Optional[int] = None
    index: str = ""
    name: str = ""
    rating: Optional[int] = None
    tags: List[str] = []
    problemId: str = ""  # Format: contestId + index (e.g., "786A")
    solvedAt: Optional[int] = None  # Timestamp when solved
    ratingAtSolve: Optional[int] = None  # User's rating when they solved this
    wasContestSolve: bool = False  # If solved during a contest

class IdolJourney(BaseModel):
    problems: List[ProblemInfo] = []
    totalProblems: int = 0
    hasMore: bool = False

class ComparisonData(BaseModel):
    user: UserStats
    idol: UserStats
    progressPercent: float = 0.0
    userAhead: bool = False

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userHandle: str
    idolHandle: str
    solvedProblems: List[str] = []  # List of problemIds user has solved from idol's journey
    currentProgress: int = 0  # Index of last solved problem in journey
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProblemExample(BaseModel):
    input: str
    output: str


class ProblemContent(BaseModel):
    contestId: int
    index: str
    name: str
    timeLimit: str = ""
    memoryLimit: str = ""
    problemStatement: str = ""
    inputSpecification: str = ""
    outputSpecification: str = ""
    examples: List[ProblemExample] = []
    note: str = ""
    rating: Optional[int] = None
    tags: List[str] = []
    url: str = ""

class ProblemDetail(BaseModel):
    contestId: Optional[int] = None
    index: str
    name: str
    rating: Optional[int] = None
    tags: List[str] = []
    url: str
    examples: List[ProblemExample] = []
    timeLimit: Optional[str] = None
    memoryLimit: Optional[str] = None
    problemStatement: Optional[str] = None
    inputSpecification: Optional[str] = None
    outputSpecification: Optional[str] = None
    note: Optional[str] = None

# Smart Curriculum Models
class FailedSubmission(BaseModel):
    problemId: str
    tags: List[str] = []

class SmartCurriculumRequest(BaseModel):
    userHandle: str
    idolHandle: str
    userRating: int = 1200
    solvedProblems: List[str] = []
    failedSubmissions: List[FailedSubmission] = []

class ProblemRecommendation(BaseModel):
    problemId: str
    contestId: Optional[int] = None
    index: str
    name: str
    rating: Optional[int] = None
    tags: List[str] = []
    reason: str
    url: str

class SmartCurriculumResponse(BaseModel):
    recommendations: List[ProblemRecommendation] = []
    cached: bool = False
    generatedAt: datetime
    expiresAt: datetime


# ── New models for topic-aligned recommendations ──

class TopicRecommendation(BaseModel):
    problemId: str
    contestId: Optional[int] = None
    index: str = ""
    name: str = ""
    rating: Optional[int] = None
    tags: List[str] = []
    difficulty: str = ""  # Easy / Medium / Hard
    url: str = ""

class RecommendationResponse(BaseModel):
    recommendations: List[TopicRecommendation] = []
    description: str = ""
    userProfile: Optional[Dict[str, Any]] = None
    idolProfile: Optional[Dict[str, Any]] = None
    generatedAt: Optional[str] = None
    cached: bool = False

class ProblemAttempt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userHandle: str
    idolHandle: str
    problemId: str
    contestId: Optional[int] = None
    index: str = ""
    name: str = ""
    rating: Optional[int] = None
    tags: List[str] = []
    difficulty: str = ""
    status: str = "attempted"  # "solved" or "failed"
    attemptedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProblemAttemptCreate(BaseModel):
    userHandle: str
    idolHandle: str
    problemId: str
    contestId: Optional[int] = None
    index: str = ""
    name: str = ""
    rating: Optional[int] = None
    tags: List[str] = []
    difficulty: str = ""
    status: str = "attempted"


# Smart Curriculum Helper Functions
# In-memory cache for curriculum recommendations
curriculum_cache: Dict[str, Dict[str, Any]] = {}

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)


def create_candidate_pool(idol_submissions: List[Dict], user_rating: int, solved_problems: List[str], failed_tags: List[str]) -> List[Dict]:
    """
    Filter idol's submissions to create candidate pool.
    Rules:
    - Rating between user_rating and user_rating + 400
    - Exclude solved problems
    - Remove duplicates
    - Prefer problems with tags matching failed submissions
    - Return top 30 candidates
    """
    candidates = []
    seen_problems = set()
    
    for submission in idol_submissions:
        problem_id = submission.get('problemId', '')
        rating = submission.get('rating')
        tags = submission.get('tags', [])
        
        # Skip if already seen or solved
        if problem_id in seen_problems or problem_id in solved_problems:
            continue
        
        # Filter by rating window
        if rating and user_rating <= rating <= user_rating + 400:
            # Calculate tag overlap score
            tag_overlap = len(set(tags) & set(failed_tags))
            
            candidates.append({
                **submission,
                'tag_overlap_score': tag_overlap
            })
            seen_problems.add(problem_id)
    
    # Sort by tag overlap (descending) and rating (ascending)
    candidates.sort(key=lambda x: (-x['tag_overlap_score'], x.get('rating', 9999)))
    
    return candidates[:30]


def analyze_weakness_profile(failed_submissions: List[FailedSubmission]) -> List[str]:
    """
    Analyze failed submissions to identify weakness areas.
    Returns top 5 most failed tags.
    """
    tag_counts = {}
    
    for submission in failed_submissions:
        for tag in submission.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Sort by frequency and return top 5
    sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])
    return [tag for tag, _ in sorted_tags[:5]]


async def call_gemini_for_curriculum(candidate_pool: List[Dict], weakness_tags: List[str], user_rating: int, idol_handle: str) -> List[Dict]:
    """
    Call Gemini API to select top 5 problems with reasoning.
    Returns list of {problemId, reason} dicts.
    """
    if not gemini_client:
        # Fallback: simple algorithm
        return simple_curriculum_fallback(candidate_pool, weakness_tags)
    
    try:
        # Prepare candidate list for prompt
        candidate_list = []
        for i, candidate in enumerate(candidate_pool[:30], 1):
            candidate_list.append(
                f"{i}. {candidate.get('problemId')} - {candidate.get('name', 'Unknown')} "
                f"(Rating: {candidate.get('rating', 'N/A')}, Tags: {', '.join(candidate.get('tags', []))})"
            )
        
        candidates_text = "\n".join(candidate_list)
        weakness_text = ", ".join(weakness_tags) if weakness_tags else "No specific weaknesses identified"
        
        prompt = f"""You are a Competitive Programming Coach analyzing a student's learning path.

CONTEXT:
- Student's current rating: {user_rating}
- Student's weak areas: {weakness_text}
- Following idol: {idol_handle}

CANDIDATE PROBLEMS (from idol's history):
{candidates_text}

TASK:
Select the top 5 problems that will best help this student improve.
Prioritize problems that:
1. Address the student's weak areas ({weakness_text})
2. Are slightly challenging (rating +100 to +300 above student's rating)
3. Have similar patterns to areas where the student struggles

RESPONSE FORMAT (strict JSON):
[
  {{
    "problemId": "1100A",
    "reason": "This problem focuses on {weakness_tags[0] if weakness_tags else 'fundamental concepts'} which you need to strengthen"
  }}
]

Return ONLY a valid JSON array with exactly 5 problems, no other text or markdown."""

        # Call Gemini 2.0 Flash
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        
        # Parse JSON response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        recommendations = json.loads(response_text)
        
        # Validate and limit to 5
        if isinstance(recommendations, list):
            return recommendations[:5]
        else:
            raise ValueError("Invalid response format")
            
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        # Fallback to simple algorithm
        return simple_curriculum_fallback(candidate_pool, weakness_tags)


def simple_curriculum_fallback(candidate_pool: List[Dict], weakness_tags: List[str]) -> List[Dict]:
    """
    Fallback algorithm when Gemini is unavailable.
    Simple tag-based selection.
    """
    recommendations = []
    
    for candidate in candidate_pool[:5]:
        problem_id = candidate.get('problemId', '')
        tags = candidate.get('tags', [])
        rating = candidate.get('rating', 0)
        
        # Generate simple reason
        matching_tags = set(tags) & set(weakness_tags)
        if matching_tags:
            reason = f"Covers {', '.join(list(matching_tags)[:2])} which you need to practice"
        else:
            reason = f"Good practice problem at rating {rating}"
        
        recommendations.append({
            'problemId': problem_id,
            'reason': reason
        })
    
    return recommendations


def get_cached_curriculum(cache_key: str) -> Optional[Dict]:
    """Check if cached curriculum exists and is < 24 hours old."""
    if cache_key in curriculum_cache:
        cached_data = curriculum_cache[cache_key]
        age = datetime.now(timezone.utc) - cached_data['timestamp']
        
        if age.total_seconds() < 24 * 3600:  # 24 hours
            return cached_data
    
    return None


def cache_curriculum(cache_key: str, recommendations: List[ProblemRecommendation]):
    """Store curriculum recommendations with timestamp."""
    curriculum_cache[cache_key] = {
        'recommendations': recommendations,
        'timestamp': datetime.now(timezone.utc)
    }


# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "IdolCode API"}

@api_router.get("/health")
async def health():
    return {"status": "ok"}


# ── Auth Models ───────────────────────────────────────────────────────────

class AuthRegister(BaseModel):
    handle: str
    password: str

class AuthLogin(BaseModel):
    handle: str
    password: str

class IdolUpdate(BaseModel):
    handle: str
    idolHandle: str


def hash_password(password: str, salt: str = None) -> dict:
    """Hash password with SHA-256 + salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return {"hash": hashed, "salt": salt}


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password against stored hash."""
    return hashlib.sha256((salt + password).encode()).hexdigest() == stored_hash


# ── Auth Endpoints ────────────────────────────────────────────────────────

@api_router.post("/auth/register")
async def register_user(data: AuthRegister):
    """
    Register a new user with Codeforces handle + password.
    Validates handle against Codeforces API first.
    """
    handle = data.handle.strip()
    password = data.password

    if not handle:
        raise HTTPException(status_code=400, detail="Handle is required")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    # Check if user already exists
    existing = await db.users.find_one({"handle": handle.lower()})
    if existing:
        raise HTTPException(status_code=409, detail="User already registered. Please login instead.")

    # Validate handle against Codeforces
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"https://codeforces.com/api/user.info?handles={handle}"
            )
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Codeforces handle not found")
            data_resp = response.json()
            if data_resp.get("status") != "OK":
                raise HTTPException(status_code=404, detail="Codeforces handle not found")
            cf_user = data_resp["result"][0]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error validating Codeforces handle")

    # Hash password and store
    pw_data = hash_password(password)
    user_doc = {
        "handle": handle.lower(),
        "displayHandle": cf_user.get("handle", handle),
        "passwordHash": pw_data["hash"],
        "salt": pw_data["salt"],
        "rating": cf_user.get("rating"),
        "maxRating": cf_user.get("maxRating"),
        "avatar": cf_user.get("avatar"),
        "registeredAt": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user_doc)

    return {
        "success": True,
        "handle": cf_user.get("handle", handle),
        "rating": cf_user.get("rating"),
        "maxRating": cf_user.get("maxRating"),
        "avatar": cf_user.get("avatar"),
        "idol": None,
    }


@api_router.post("/auth/login")
async def login_user(data: AuthLogin):
    """
    Login with Codeforces handle + password.
    Verifies against stored credentials.
    """
    handle = data.handle.strip().lower()
    password = data.password

    if not handle or not password:
        raise HTTPException(status_code=400, detail="Handle and password are required")

    # Find user in DB
    user = await db.users.find_one({"handle": handle})
    if not user:
        raise HTTPException(status_code=401, detail="User not found. Please register first.")

    # Verify password
    if not verify_password(password, user["passwordHash"], user["salt"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Get saved idol handle
    saved_idol = user.get("idolHandle")

    # Fetch latest CF info
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"https://codeforces.com/api/user.info?handles={handle}"
            )
            if response.status_code == 200:
                data_resp = response.json()
                if data_resp.get("status") == "OK":
                    cf_user = data_resp["result"][0]
                    return {
                        "success": True,
                        "handle": cf_user.get("handle", handle),
                        "rating": cf_user.get("rating"),
                        "maxRating": cf_user.get("maxRating"),
                        "avatar": cf_user.get("avatar"),
                        "idol": saved_idol,
                    }
    except Exception:
        pass

    # Fallback: return stored info
    return {
        "success": True,
        "handle": user.get("displayHandle", handle),
        "rating": user.get("rating"),
        "maxRating": user.get("maxRating"),
        "avatar": user.get("avatar"),
        "idol": saved_idol,
    }


# ── Idol Sync Endpoints ──────────────────────────────────────────────────

@api_router.put("/auth/idol")
async def save_user_idol(data: IdolUpdate):
    """
    Save or update the user's selected idol in the database.
    Both frontend and extension call this after idol selection.
    """
    handle = data.handle.strip().lower()
    idol_handle = data.idolHandle.strip()

    if not handle or not idol_handle:
        raise HTTPException(status_code=400, detail="Handle and idolHandle are required")

    result = await db.users.update_one(
        {"handle": handle},
        {"$set": {"idolHandle": idol_handle, "idolUpdatedAt": datetime.now(timezone.utc).isoformat()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"success": True, "idol": idol_handle}


@api_router.get("/auth/idol/{user_handle}")
async def get_user_idol(user_handle: str):
    """
    Get the user's currently saved idol from the database.
    """
    handle = user_handle.strip().lower()
    user = await db.users.find_one({"handle": handle}, {"_id": 0, "idolHandle": 1})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"idol": user.get("idolHandle")}


# ── Dashboard Data Endpoint (All-in-one cached) ─────────────────────────

@api_router.get("/dashboard-data/{user_handle}")
async def get_dashboard_data(user_handle: str, refresh: bool = False, idol: Optional[str] = None):
    """
    Single endpoint that returns all dashboard data from MongoDB cache.
    If refresh=true, re-fetches everything from Codeforces API and updates cache.
    Clients should call this on page load (without refresh) and only use refresh=true
    when user explicitly clicks a Refresh button.
    Optional idol param overrides the DB-stored idol (useful when idol was just changed).
    """
    handle = user_handle.strip().lower()
    user_doc = await db.users.find_one({"handle": handle}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    idol_handle = idol.strip().lower() if idol else user_doc.get("idolHandle")
    if not idol_handle:
        return {"idol": None, "comparison": None, "recommendations": None, "skillComparison": None, "history": []}

    comparison = None
    recommendations_data = None
    skill_data = None
    history = []

    # --- Comparison ---
    try:
        comp_resp = await compare_users(handle, idol_handle, refresh=refresh)
        comparison = comp_resp.model_dump() if hasattr(comp_resp, 'model_dump') else comp_resp
    except Exception as e:
        logger.error(f"Dashboard comparison error: {e}")

    # --- Recommendations (already has 24h cache in its own endpoint) ---
    try:
        rec_resp = await get_recommendations(handle, idol_handle, refresh=refresh)
        recommendations_data = rec_resp.model_dump() if hasattr(rec_resp, 'model_dump') else rec_resp
    except Exception as e:
        logger.error(f"Dashboard recommendations error: {e}")

    # --- Skill Comparison ---
    try:
        skill_data = await get_skill_comparison(handle, idol_handle, topics=None, refresh=refresh)
    except Exception as e:
        logger.error(f"Dashboard skill comparison error: {e}")

    # --- Problem History (already DB-based) ---
    try:
        attempts = await db.problem_history.find(
            {"userHandle": handle}, {"_id": 0}
        ).sort("attemptedAt", -1).limit(50).to_list(50)
        history = attempts
    except Exception as e:
        logger.error(f"Dashboard history error: {e}")

    return {
        "idol": idol_handle,
        "comparison": comparison,
        "recommendations": recommendations_data,
        "skillComparison": skill_data,
        "history": history,
    }


# ── Code Testing Endpoint ─────────────────────────────────────────────────

class TestCodeRequest(BaseModel):
    code: str
    language: str  # python, javascript, cpp, java
    testCases: List[Dict[str, str]]  # [{input: "...", output: "..."}]

import subprocess
import tempfile

@api_router.post("/test-code")
async def test_code(data: TestCodeRequest):
    """
    Run user code against provided test cases using subprocess.
    Returns per-test results with pass/fail status.
    """
    code = data.code
    language = data.language
    test_cases = data.testCases

    if not code.strip():
        raise HTTPException(status_code=400, detail="No code provided")
    if not test_cases:
        raise HTTPException(status_code=400, detail="No test cases provided")

    results = []

    for i, tc in enumerate(test_cases):
        test_input = tc.get("input", "").strip()
        expected_output = tc.get("output", "").strip()

        try:
            actual_output = await _run_code(code, language, test_input, timeout=10)
            actual_output = actual_output.strip()

            # Compare outputs (normalize whitespace per line)
            expected_lines = [l.strip() for l in expected_output.splitlines() if l.strip()]
            actual_lines = [l.strip() for l in actual_output.splitlines() if l.strip()]
            passed = expected_lines == actual_lines

            results.append({
                "testCase": i + 1,
                "passed": passed,
                "input": test_input,
                "expected": expected_output,
                "actual": actual_output,
            })
        except TimeoutError:
            results.append({
                "testCase": i + 1,
                "passed": False,
                "input": test_input,
                "expected": expected_output,
                "actual": "⏰ Time Limit Exceeded (10s)",
            })
        except Exception as e:
            results.append({
                "testCase": i + 1,
                "passed": False,
                "input": test_input,
                "expected": expected_output,
                "actual": f"Runtime Error: {str(e)}",
            })

    all_passed = all(r["passed"] for r in results)
    return {"results": results, "allPassed": all_passed}


async def _run_code(code: str, language: str, stdin_input: str, timeout: int = 10) -> str:
    """Execute code in a subprocess and return stdout."""
    with tempfile.TemporaryDirectory() as tmpdir:
        if language == "python":
            filepath = os.path.join(tmpdir, "solution.py")
            with open(filepath, "w") as f:
                f.write(code)
            cmd = ["python3", filepath]

        elif language == "javascript":
            filepath = os.path.join(tmpdir, "solution.js")
            with open(filepath, "w") as f:
                f.write(code)
            cmd = ["node", filepath]

        elif language == "cpp":
            src = os.path.join(tmpdir, "solution.cpp")
            exe = os.path.join(tmpdir, "solution")
            with open(src, "w") as f:
                f.write(code)
            # Compile
            compile_proc = await asyncio.create_subprocess_exec(
                "g++", "-O2", "-o", exe, src,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, compile_err = await asyncio.wait_for(compile_proc.communicate(), timeout=15)
            if compile_proc.returncode != 0:
                raise Exception(f"Compilation Error:\n{compile_err.decode()}")
            cmd = [exe]

        elif language == "java":
            filepath = os.path.join(tmpdir, "Main.java")
            with open(filepath, "w") as f:
                f.write(code)
            # Compile
            compile_proc = await asyncio.create_subprocess_exec(
                "javac", filepath,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, compile_err = await asyncio.wait_for(compile_proc.communicate(), timeout=15)
            if compile_proc.returncode != 0:
                raise Exception(f"Compilation Error:\n{compile_err.decode()}")
            cmd = ["java", "-cp", tmpdir, "Main"]

        else:
            raise Exception(f"Unsupported language: {language}")

        # Run
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=stdin_input.encode()),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise TimeoutError("Time Limit Exceeded")

        if proc.returncode != 0:
            err_msg = stderr.decode().strip()
            raise Exception(err_msg or "Runtime error (non-zero exit code)")

        return stdout.decode()


# ── Duck Chat Endpoint ─────────────────────────────────────────────────────

class DuckChatRequest(BaseModel):
    message: str
    problemStatement: Optional[str] = None
    problemTitle: Optional[str] = None
    code: Optional[str] = None
    language: Optional[str] = None
    idolHandle: Optional[str] = None
    chatHistory: Optional[List[Dict[str, str]]] = None  # [{role, content}]


@api_router.post("/duck-chat")
async def duck_chat(data: DuckChatRequest):
    """
    AI-powered Duck Chat using Gemini.
    Provides contextual hints based on the problem, code, and idol's style.
    """
    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini API not configured")

    # Build system context
    system_parts = [
        "You are DuckBot 🦆, a friendly and encouraging competitive programming coach.",
        "You help users solve Codeforces problems by giving hints, explaining concepts, and guiding their thinking.",
        "IMPORTANT: Never give the full solution directly. Instead, provide hints, point out issues, suggest approaches, and explain relevant algorithms.",
        "Keep responses concise (2-4 sentences max) unless the user asks for a detailed explanation.",
        "Use emoji sparingly to stay friendly. Reference the problem context when relevant.",
    ]

    if data.idolHandle:
        system_parts.append(
            f"The user is learning from competitive programmer '{data.idolHandle}'. "
            f"When relevant, mention techniques or approaches that top competitive programmers like {data.idolHandle} commonly use."
        )

    if data.problemTitle and data.problemStatement:
        system_parts.append(f"\n--- CURRENT PROBLEM ---\nTitle: {data.problemTitle}\n{data.problemStatement[:3000]}")

    if data.code and data.code.strip():
        system_parts.append(f"\n--- USER'S CURRENT CODE ({data.language or 'unknown'}) ---\n{data.code[:2000]}")

    system_prompt = "\n".join(system_parts)

    # Build conversation
    contents = []
    if data.chatHistory:
        for msg in data.chatHistory[-10:]:  # Keep last 10 messages for context
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

    # Add the new user message
    contents.append({"role": "user", "parts": [{"text": data.message}]})

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.7,
                "max_output_tokens": 500,
            },
        )

        reply = response.text.strip() if response.text else "Quack! 🦆 I'm having trouble thinking right now. Try again!"
        return {"reply": reply}

    except Exception as e:
        logging.error(f"Gemini duck-chat error: {e}")
        return {"reply": "Quack! 🦆 Something went wrong. Please try again in a moment."}


# ── Skill Comparison Endpoint ──────────────────────────────────────────────

@api_router.get("/skill-comparison/{user_handle}/{idol_handle}")
async def get_skill_comparison(
    user_handle: str,
    idol_handle: str,
    topics: Optional[str] = Query(None, description="Comma-separated custom topics to focus on"),
    refresh: bool = False,
):
    """
    Compare user skills with idol's skills *at a similar rank*.
    Caches in MongoDB. Use refresh=true to force re-fetch from Codeforces.
    """
    cache_key = f"{user_handle.lower()}_{idol_handle.lower()}"
    custom_topic_list = [t.strip() for t in topics.split(",")] if topics else []

    # Check MongoDB cache (only for non-custom requests)
    if not refresh and not custom_topic_list:
        try:
            cached = await db.skill_comparison_cache.find_one({"cacheKey": cache_key}, {"_id": 0})
            if cached and cached.get("cachedAt"):
                age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(cached["cachedAt"])).total_seconds() / 3600
                if age_hours < 24:
                    return {
                        "stats": cached.get("stats", []),
                        "weakestTopics": cached.get("weakestTopics", []),
                        "userRating": cached.get("userRating", 0),
                        "idolRatingAtComparison": cached.get("idolRatingAtComparison", 0),
                        "allTopics": cached.get("allTopics", []),
                    }
        except Exception:
            pass

    # 1. Fetch data
    try:
        user_info = await fetch_user_info(user_handle)
        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_rating = user_info.get("rating", 0)
        # If user has no rating (unrated), assume 800 (newbie base)
        if not user_rating:
            user_rating = 800

        user_subs = await fetch_user_submissions(user_handle)
        idol_subs = await fetch_user_submissions(idol_handle)
        idol_history = await fetch_user_rating_history(idol_handle)

    except Exception as e:
        logger.error(f"Error fetching data for comparison: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch verification data")

    # 2. Analyze profiles
    user_profile = analyze_user_profile(user_subs)
    idol_profile = analyze_idol_profile(idol_subs, idol_history)

    user_solved_ids = user_profile["solved_problem_ids"]
    user_tags = user_profile["solved_by_tag"]

    # 3. Use idol's FULL Codeforces history for comparison
    # This gives complete data and avoids None idolRatingAtSolve issues
    idol_all_tags = Counter()
    for p in idol_profile["solved_problems"]:
        for t in p.get("tags", []):
            idol_all_tags[t] += 1

    # 4. Build Comparison Stats
    # Identify relevant topics (top 20 most common in idol's full history)
    top_idol_tags = [t for t, _ in idol_all_tags.most_common(20)]
    # Also include user's top tags if not in that list
    top_user_tags = [t for t, _ in Counter(user_tags).most_common(10)]
    all_relevant_tags = list(dict.fromkeys(top_idol_tags + top_user_tags))  # preserve order, dedupe

    comparison_stats = []
    for tag in all_relevant_tags:
        u_val = user_tags.get(tag, 0)
        i_val = idol_all_tags.get(tag, 0)

        # We only care if at least one side has meaningful data
        if i_val < 2 and u_val < 2:
            continue

        comparison_stats.append({
            "topic": tag,
            "user": u_val,
            "idol": i_val,
            "gap": i_val - u_val
        })

    # Sort by Gap descending (biggest weakness first)
    comparison_stats.sort(key=lambda x: x["gap"], reverse=True)

    # 5. Identify Weakest Topics & Recommendations
    weakest_topics = []
    seen_topics = set()  # prevent duplicate topic entries
    
    # Filter for positive gaps where idol has much more experience
    candidate_topics = [s for s in comparison_stats if s["gap"] > 2]
    
    # If not enough gaps, just pick top idol topics user hasn't touched much
    if len(candidate_topics) < 3:
        candidate_topics = comparison_stats[:5]

    for item in candidate_topics:
        if len(weakest_topics) >= 3:
            break
        topic = item["topic"]
        if topic in seen_topics:
            continue
        seen_topics.add(topic)
        
        # Find 3 problems from Idol's history for this topic:
        # - Not solved by user
        # - Tagged with this topic
        # - Rating is challenging but doable (UserRating - 100 to UserRating + 400)
        # - If idol solved it around that rank, even better.
        
        candidates = []
        for p in idol_profile["solved_problems"]:
            if p["problemId"] in user_solved_ids:
                continue
            if topic not in p.get("tags", []):
                continue
            
            p_rating = p.get("rating")
            if not p_rating: 
                continue

            # Difficulty window:
            if (user_rating - 200) <= p_rating <= (user_rating + 500):
                candidates.append(p)

        # Sort candidates by rating (easier first) to build confidence
        candidates.sort(key=lambda x: x["rating"])
        
        # Pick top 3 unique problems
        problems = []
        seen_pids = set()
        for p in candidates:
            if p["problemId"] not in seen_pids:
                problems.append({
                    "name": p["name"],
                    "rating": p["rating"],
                    "url": f"https://codeforces.com/contest/{p['contestId']}/problem/{p['index']}",
                    "contestId": p["contestId"],
                    "index": p["index"]
                })
                seen_pids.add(p["problemId"])
            if len(problems) >= 3:
                break
        
        if problems:
            weakest_topics.append({
                "topic": topic,
                "gap": item["gap"],
                "problems": problems
            })

    # 6. If custom topics were requested, override weakest_topics with those specific topics
    custom_topic_list = [t.strip() for t in topics.split(",")] if topics else []
    if custom_topic_list:
        weakest_topics = []
        for topic_name in custom_topic_list[:3]:
            # Find gap info from comparison_stats
            stat_item = next((s for s in comparison_stats if s["topic"] == topic_name), None)
            gap_val = stat_item["gap"] if stat_item else 0

            candidates = []
            for p in idol_profile["solved_problems"]:
                if p["problemId"] in user_solved_ids:
                    continue
                if topic_name not in p.get("tags", []):
                    continue
                p_rating = p.get("rating")
                if not p_rating:
                    continue
                if (user_rating - 200) <= p_rating <= (user_rating + 500):
                    candidates.append(p)

            candidates.sort(key=lambda x: x["rating"])
            problems = []
            seen_pids = set()
            for p in candidates:
                if p["problemId"] not in seen_pids:
                    problems.append({
                        "name": p["name"],
                        "rating": p["rating"],
                        "url": f"https://codeforces.com/contest/{p['contestId']}/problem/{p['index']}",
                        "contestId": p["contestId"],
                        "index": p["index"]
                    })
                    seen_pids.add(p["problemId"])
                if len(problems) >= 3:
                    break

            if problems:
                weakest_topics.append({
                    "topic": topic_name,
                    "gap": gap_val,
                    "problems": problems
                })

    # 7. Build full list of all known Codeforces problem tags for the Customize overlay
    ALL_CF_TAGS = sorted([
        "2-sat", "binary search", "bitmasks", "brute force", "chinese remainder theorem",
        "combinatorics", "constructive algorithms", "data structures", "dfs and similar",
        "divide and conquer", "dp", "dsu", "expression parsing", "fft", "flows",
        "games", "geometry", "graph matchings", "graphs", "greedy", "hashing",
        "implementation", "interactive", "math", "matrices", "meet-in-the-middle",
        "number theory", "probabilities", "schedules", "shortest paths",
        "sortings", "string suffix structures", "strings", "ternary search",
        "trees", "two pointers",
    ])

    result = {
        "stats": comparison_stats,  # Full list for visualization
        "weakestTopics": weakest_topics,  # Top 3 with recommendations
        "userRating": user_rating,
        "idolRatingAtComparison": user_rating,  # Now comparing against full history
        "allTopics": ALL_CF_TAGS,  # For customize overlay
    }

    # Save to MongoDB cache (only for default non-custom requests)
    if not custom_topic_list:
        try:
            await db.skill_comparison_cache.update_one(
                {"cacheKey": cache_key},
                {"$set": {**result, "cacheKey": cache_key, "cachedAt": datetime.now(timezone.utc).isoformat()}},
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Failed to cache skill comparison: {e}")

    return result


@api_router.get("/coders/search", response_model=List[CoderSuggestion])
async def search_coders(query: str, limit: int = 5):
    """
    Search for Codeforces users by handle
    """
    if not query or len(query.strip()) < 2:
        return []
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Search for users whose handle starts with the query
            response = await client.get(
                f"https://codeforces.com/api/user.info?handles={query}"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    users = data.get("result", [])
                    suggestions = []
                    for user in users[:limit]:
                        suggestions.append(CoderSuggestion(
                            handle=user.get("handle", ""),
                            rating=user.get("rating"),
                            rank=user.get("rank"),
                            maxRating=user.get("maxRating"),
                            maxRank=user.get("maxRank"),
                            avatar=user.get("avatar", "")
                        ))
                    return suggestions
            
            # If exact match fails, try to get popular users
            # Fallback: return some popular coders that match the query
            popular_coders = [
                "tourist", "Benq", "Petr", "Radewoosh", "mnbvmar",
                "scott_wu", "ksun48", "Errichto", "jiangly", "Um_nik"
            ]
            
            matching = [h for h in popular_coders if query.lower() in h.lower()]
            if matching:
                handles_str = ";".join(matching[:limit])
                response = await client.get(
                    f"https://codeforces.com/api/user.info?handles={handles_str}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "OK":
                        users = data.get("result", [])
                        suggestions = []
                        for user in users:
                            suggestions.append(CoderSuggestion(
                                handle=user.get("handle", ""),
                                rating=user.get("rating"),
                                rank=user.get("rank"),
                                maxRating=user.get("maxRating"),
                                maxRank=user.get("maxRank"),
                                avatar=user.get("avatar", "")
                            ))
                        return suggestions
            
            return []
            
    except Exception as e:
        logger.error(f"Error searching coders: {str(e)}")
        # Return empty list instead of raising exception for better UX
        return []


@api_router.get("/user/{handle}/info", response_model=UserInfo)
async def get_user_info(handle: str):
    """
    Get detailed user info from Codeforces
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(
                f"https://codeforces.com/api/user.info?handles={handle}"
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK" and data.get("result"):
                    user = data["result"][0]
                    return UserInfo(
                        handle=user.get("handle", ""),
                        rating=user.get("rating"),
                        rank=user.get("rank"),
                        maxRating=user.get("maxRating"),
                        maxRank=user.get("maxRank"),
                        avatar=user.get("avatar"),
                        titlePhoto=user.get("titlePhoto"),
                        contribution=user.get("contribution"),
                        friendOfCount=user.get("friendOfCount"),
                        registrationTimeSeconds=user.get("registrationTimeSeconds")
                    )
            
            raise HTTPException(status_code=404, detail=f"User {handle} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user info: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user info")


@api_router.get("/user/{handle}/stats", response_model=UserStats)
async def get_user_stats(handle: str):
    """
    Get comprehensive user stats including problems solved, contests, wins
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            # Fetch user info
            info_response = await http_client.get(
                f"https://codeforces.com/api/user.info?handles={handle}"
            )
            
            user_info = {}
            if info_response.status_code == 200:
                data = info_response.json()
                if data.get("status") == "OK" and data.get("result"):
                    user_info = data["result"][0]
            
            if not user_info:
                raise HTTPException(status_code=404, detail=f"User {handle} not found")
            
            # Fetch user submissions to count problems solved
            status_response = await http_client.get(
                f"https://codeforces.com/api/user.status?handle={handle}"
            )
            
            problems_solved = set()
            if status_response.status_code == 200:
                data = status_response.json()
                if data.get("status") == "OK":
                    for submission in data.get("result", []):
                        if submission.get("verdict") == "OK":
                            problem = submission.get("problem", {})
                            contest_id = problem.get("contestId", "")
                            index = problem.get("index", "")
                            if contest_id and index:
                                problems_solved.add(f"{contest_id}{index}")
            
            # Fetch rating history to count contests and wins
            rating_response = await http_client.get(
                f"https://codeforces.com/api/user.rating?handle={handle}"
            )
            
            contests_participated = 0
            contest_wins = 0
            if rating_response.status_code == 200:
                data = rating_response.json()
                if data.get("status") == "OK":
                    contests = data.get("result", [])
                    contests_participated = len(contests)
                    # Count wins (top 10 finishes)
                    for contest in contests:
                        if contest.get("rank", 999) <= 10:
                            contest_wins += 1
            
            return UserStats(
                handle=user_info.get("handle", ""),
                rating=user_info.get("rating"),
                rank=user_info.get("rank"),
                maxRating=user_info.get("maxRating"),
                maxRank=user_info.get("maxRank"),
                problemsSolved=len(problems_solved),
                contestsParticipated=contests_participated,
                contestWins=contest_wins
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user stats")


@api_router.get("/idol/{handle}/journey", response_model=IdolJourney)
async def get_idol_journey(
    handle: str, 
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """
    Get the problem solving journey of an idol - problems in chronological order
    """
    try:
        async with httpx.AsyncClient(timeout=20.0) as http_client:
            # Fetch user submissions
            status_response = await http_client.get(
                f"https://codeforces.com/api/user.status?handle={handle}"
            )
            
            if status_response.status_code != 200:
                raise HTTPException(status_code=404, detail=f"Could not fetch submissions for {handle}")
            
            data = status_response.json()
            if data.get("status") != "OK":
                raise HTTPException(status_code=404, detail=f"User {handle} not found")
            
            # Fetch rating history to get rating at time of solve
            rating_response = await http_client.get(
                f"https://codeforces.com/api/user.rating?handle={handle}"
            )
            
            rating_history = []
            if rating_response.status_code == 200:
                rating_data = rating_response.json()
                if rating_data.get("status") == "OK":
                    rating_history = rating_data.get("result", [])
            
            # Build a function to get rating at a specific time
            def get_rating_at_time(timestamp):
                rating = None
                for contest in rating_history:
                    if contest.get("ratingUpdateTimeSeconds", 0) <= timestamp:
                        rating = contest.get("newRating")
                    else:
                        break
                return rating
            
            # Process submissions - keep only first successful submission for each problem
            submissions = data.get("result", [])
            # Sort by time (oldest first)
            submissions.sort(key=lambda x: x.get("creationTimeSeconds", 0))
            
            seen_problems = set()
            problems = []
            
            for submission in submissions:
                if submission.get("verdict") != "OK":
                    continue
                    
                problem = submission.get("problem", {})
                contest_id = problem.get("contestId")
                index = problem.get("index", "")
                
                if not contest_id or not index:
                    continue
                
                problem_id = f"{contest_id}{index}"
                
                if problem_id in seen_problems:
                    continue
                
                seen_problems.add(problem_id)
                solved_time = submission.get("creationTimeSeconds", 0)
                
                # Check if it was solved during a contest
                was_contest = submission.get("author", {}).get("participantType") in ["CONTESTANT", "VIRTUAL"]
                
                problems.append(ProblemInfo(
                    contestId=contest_id,
                    index=index,
                    name=problem.get("name", ""),
                    rating=problem.get("rating"),
                    tags=problem.get("tags", []),
                    problemId=problem_id,
                    solvedAt=solved_time,
                    ratingAtSolve=get_rating_at_time(solved_time),
                    wasContestSolve=was_contest
                ))
            
            total_problems = len(problems)
            
            # Apply pagination
            paginated_problems = problems[offset:offset + limit]
            has_more = (offset + limit) < total_problems
            
            return IdolJourney(
                problems=paginated_problems,
                totalProblems=total_problems,
                hasMore=has_more
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching idol journey: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching idol journey")


@api_router.get("/user/{handle}/solved-problems")
async def get_user_solved_problems(handle: str, refresh: bool = False):
    """
    Get list of problem IDs that the user has solved.
    Caches in MongoDB. Use refresh=true to force re-fetch from Codeforces.
    """
    cache_key = handle.lower()

    # Check cache first
    if not refresh:
        try:
            cached = await db.solved_problems_cache.find_one({"handle": cache_key}, {"_id": 0})
            if cached and cached.get("cachedAt"):
                age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(cached["cachedAt"])).total_seconds() / 3600
                if age_hours < 24:
                    return {"handle": handle, "solvedProblems": cached.get("solvedProblems", [])}
        except Exception:
            pass

    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            response = await http_client.get(
                f"https://codeforces.com/api/user.status?handle={handle}"
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail=f"Could not fetch submissions for {handle}")
            
            data = response.json()
            if data.get("status") != "OK":
                raise HTTPException(status_code=404, detail=f"User {handle} not found")
            
            solved_problems = set()
            for submission in data.get("result", []):
                if submission.get("verdict") == "OK":
                    problem = submission.get("problem", {})
                    contest_id = problem.get("contestId", "")
                    index = problem.get("index", "")
                    if contest_id and index:
                        solved_problems.add(f"{contest_id}{index}")

            solved_list = list(solved_problems)

            # Save to cache
            try:
                await db.solved_problems_cache.update_one(
                    {"handle": cache_key},
                    {"$set": {"handle": cache_key, "solvedProblems": solved_list, "cachedAt": datetime.now(timezone.utc).isoformat()}},
                    upsert=True,
                )
            except Exception as e:
                logger.error(f"Failed to cache solved problems: {e}")

            return {"handle": handle, "solvedProblems": solved_list}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user solved problems: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user solved problems")


@api_router.post("/smart-curriculum", response_model=SmartCurriculumResponse)
async def generate_smart_curriculum(request: SmartCurriculumRequest):
    """
    Generate AI-powered problem recommendations using Gemini API.
    Returns top 5 problems from idol's history tailored to user's weaknesses.
    """
    try:
        # Create cache key
        cache_key = f"{request.userHandle}_{request.idolHandle}"
        
        # Check cache first
        cached = get_cached_curriculum(cache_key)
        if cached:
            logger.info(f"Returning cached curriculum for {cache_key}")
            return SmartCurriculumResponse(
                recommendations=cached['recommendations'],
                cached=True,
                generatedAt=cached['timestamp'],
                expiresAt=cached['timestamp'] + timedelta(hours=24)
            )
        
        # Fetch idol's submission history
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            response = await http_client.get(
                f"https://codeforces.com/api/user.status?handle={request.idolHandle}&from=1&count=1000"
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail=f"Could not fetch submissions for {request.idolHandle}")
            
            data = response.json()
            if data.get("status") != "OK":
                raise HTTPException(status_code=404, detail=f"Idol {request.idolHandle} not found")
            
            # Extract solved problems from idol's history
            idol_submissions = []
            seen_problems = set()
            
            for submission in data.get("result", []):
                if submission.get("verdict") == "OK":
                    problem = submission.get("problem", {})
                    contest_id = problem.get("contestId")
                    index = problem.get("index", "")
                    
                    if not contest_id or not index:
                        continue
                    
                    problem_id = f"{contest_id}{index}"
                    
                    if problem_id in seen_problems:
                        continue
                    
                    seen_problems.add(problem_id)
                    
                    idol_submissions.append({
                        'problemId': problem_id,
                        'contestId': contest_id,
                        'index': index,
                        'name': problem.get("name", ""),
                        'rating': problem.get("rating"),
                        'tags': problem.get("tags", [])
                    })
        
        # Analyze user's weakness profile
        weakness_tags = analyze_weakness_profile(request.failedSubmissions)
        
        # Create candidate pool
        candidate_pool = create_candidate_pool(
            idol_submissions,
            request.userRating,
            request.solvedProblems,
            weakness_tags
        )
        
        if not candidate_pool:
            # No suitable problems found
            return SmartCurriculumResponse(
                recommendations=[],
                cached=False,
                generatedAt=datetime.now(timezone.utc),
                expiresAt=datetime.now(timezone.utc) + timedelta(hours=24)
            )
        
        # Call Gemini for smart recommendations
        gemini_recommendations = await call_gemini_for_curriculum(
            candidate_pool,
            weakness_tags,
            request.userRating,
            request.idolHandle
        )
        
        # Build full recommendation objects
        recommendations = []
        for rec in gemini_recommendations:
            problem_id = rec.get('problemId', '')
            
            # Find the full problem data from candidate pool
            problem_data = next(
                (p for p in candidate_pool if p.get('problemId') == problem_id),
                None
            )
            
            if problem_data:
                recommendations.append(ProblemRecommendation(
                    problemId=problem_id,
                    contestId=problem_data.get('contestId'),
                    index=problem_data.get('index', ''),
                    name=problem_data.get('name', ''),
                    rating=problem_data.get('rating'),
                    tags=problem_data.get('tags', []),
                    reason=rec.get('reason', 'Recommended by your coach'),
                    url=f"https://codeforces.com/problemset/problem/{problem_data.get('contestId')}/{problem_data.get('index')}"
                ))
        
        # Cache the results
        cache_curriculum(cache_key, recommendations)
        
        now = datetime.now(timezone.utc)
        return SmartCurriculumResponse(
            recommendations=recommendations,
            cached=False,
            generatedAt=now,
            expiresAt=now + timedelta(hours=24)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating smart curriculum: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating smart curriculum: {str(e)}")


@api_router.get("/compare/{user_handle}/{idol_handle}", response_model=ComparisonData)
async def compare_users(user_handle: str, idol_handle: str, refresh: bool = False):
    """
    Compare user stats with idol stats.
    Caches in MongoDB. Use refresh=true to force re-fetch from Codeforces.
    """
    cache_key = f"{user_handle.lower()}_{idol_handle.lower()}"

    # Check MongoDB cache first (unless refresh requested)
    if not refresh:
        try:
            cached = await db.comparison_cache.find_one({"cacheKey": cache_key}, {"_id": 0})
            if cached and cached.get("cachedAt"):
                age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(cached["cachedAt"])).total_seconds() / 3600
                if age_hours < 24:
                    return ComparisonData(
                        user=UserStats(**cached["user"]),
                        idol=UserStats(**cached["idol"]),
                        progressPercent=cached["progressPercent"],
                        userAhead=cached["userAhead"],
                    )
        except Exception:
            pass  # cache miss, fetch fresh

    try:
        # Fetch both user stats in parallel
        user_stats_task = get_user_stats(user_handle)
        idol_stats_task = get_user_stats(idol_handle)
        
        user_stats, idol_stats = await asyncio.gather(
            user_stats_task, idol_stats_task
        )
        
        # Calculate progress percentage based on problems solved
        idol_problems = idol_stats.problemsSolved or 1
        user_problems = user_stats.problemsSolved or 0
        
        progress_percent = min(100, (user_problems / idol_problems) * 100)
        user_ahead = (user_stats.rating or 0) >= (idol_stats.rating or 0)

        result = ComparisonData(
            user=user_stats,
            idol=idol_stats,
            progressPercent=round(progress_percent, 1),
            userAhead=user_ahead
        )

        # Save to MongoDB cache
        try:
            await db.comparison_cache.update_one(
                {"cacheKey": cache_key},
                {"$set": {
                    "cacheKey": cache_key,
                    "user": user_stats.model_dump(),
                    "idol": idol_stats.model_dump(),
                    "progressPercent": result.progressPercent,
                    "userAhead": result.userAhead,
                    "cachedAt": datetime.now(timezone.utc).isoformat(),
                }},
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Failed to cache comparison: {e}")

        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing users: {str(e)}")
        raise HTTPException(status_code=500, detail="Error comparing users")


@api_router.get("/problem/{contest_id}/{problem_index}", response_model=ProblemContent)
async def get_problem_content(contest_id: int, problem_index: str):
    """
    Fetch problem content from Codeforces API and parse additional details
    """
    try:
        url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_index}"
        
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as http_client:
            # First, get problem metadata from API
            api_response = await http_client.get(
                f"https://codeforces.com/api/problemset.problems"
            )
            
            problem_data = None
            if api_response.status_code == 200:
                api_data = api_response.json()
                if api_data.get("status") == "OK":
                    problems = api_data.get("result", {}).get("problems", [])
                    for p in problems:
                        if p.get("contestId") == contest_id and p.get("index") == problem_index:
                            problem_data = p
                            break
            
            if not problem_data:
                raise HTTPException(status_code=404, detail=f"Problem not found: {contest_id}{problem_index}")
            
            name = problem_data.get("name", "")
            rating = problem_data.get("rating")
            tags = problem_data.get("tags", [])
            
            # Try to fetch problem statement from Codeforces website
            problem_statement = ""
            input_spec = ""
            output_spec = ""
            examples = []
            note = ""
            time_limit = "2 seconds"  # Default
            memory_limit = "256 megabytes"  # Default
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://codeforces.com/',
            }
            
            try:
                response = await http_client.get(url, headers=headers)
                
                if response.status_code == 200:
                    html = response.text
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract time and memory limits
                    time_elem = soup.select_one('.problem-statement .time-limit')
                    memory_elem = soup.select_one('.problem-statement .memory-limit')
                    if time_elem:
                        time_limit = time_elem.get_text().replace('time limit per test', '').strip()
                    if memory_elem:
                        memory_limit = memory_elem.get_text().replace('memory limit per test', '').strip()
                    
                    def extract_text_with_latex(element):
                        """Extract text preserving LaTeX notation from Codeforces HTML.
                        Converts tex-span, tex-font-style-bf/it, and $$$ delimiters to KaTeX format."""
                        if element is None:
                            return ""
                        
                        import copy
                        el = copy.copy(element)
                        
                        # Process the HTML string directly for $$$...$$$
                        html_str = str(el)
                        # Codeforces uses $$$ as LaTeX delimiters
                        html_str = html_str.replace('$$$', '$')
                        
                        # Re-parse the modified HTML
                        from bs4 import BeautifulSoup as BS
                        el = BS(html_str, 'html.parser')
                        
                        # Convert <br/> to newlines
                        for br in el.find_all('br'):
                            br.replace_with('\n')
                        
                        # Convert <p> tags to text with spacing
                        for p in el.find_all('p'):
                            p.insert_before('\n')
                            p.insert_after('\n')
                        
                        # Convert <li> to bullet points
                        for li in el.find_all('li'):
                            li.insert_before('\n• ')
                        
                        # Get text (LaTeX $...$ delimiters are preserved as text)
                        text = el.get_text()
                        
                        # Clean up excessive whitespace but preserve newlines
                        lines = text.split('\n')
                        cleaned_lines = []
                        for line in lines:
                            cleaned = ' '.join(line.split())
                            if cleaned:
                                cleaned_lines.append(cleaned)
                            elif cleaned_lines and cleaned_lines[-1] != '':
                                cleaned_lines.append('')
                        
                        return '\n'.join(cleaned_lines).strip()

                    # Extract problem statement - get text from divs without class
                    statement_div = soup.select_one('.problem-statement')
                    if statement_div:
                        # Get the main statement text (usually in divs without specific classes)
                        for div in statement_div.find_all('div', recursive=False):
                            class_list = div.get('class', [])
                            if not class_list:
                                problem_statement += extract_text_with_latex(div) + '\n\n'
                    
                    # Extract input specification
                    input_div = soup.select_one('.problem-statement .input-specification')
                    if input_div:
                        text = extract_text_with_latex(input_div)
                        input_spec = text.replace('Input', '', 1).strip()
                    
                    # Extract output specification
                    output_div = soup.select_one('.problem-statement .output-specification')
                    if output_div:
                        text = extract_text_with_latex(output_div)
                        output_spec = text.replace('Output', '', 1).strip()
                    
                    # Extract examples
                    sample_tests = soup.select_one('.problem-statement .sample-tests')
                    if sample_tests:
                        inputs = sample_tests.select('.input pre')
                        outputs = sample_tests.select('.output pre')
                        for inp, out in zip(inputs, outputs):
                            inp_text = inp.get_text(separator='\n').strip()
                            out_text = out.get_text(separator='\n').strip()
                            examples.append(ProblemExample(input=inp_text, output=out_text))
                    
                    # Extract note
                    note_div = soup.select_one('.problem-statement .note')
                    if note_div:
                        note = extract_text_with_latex(note_div).replace('Note', '', 1).strip()
                        
            except Exception as parse_error:
                logger.warning(f"Could not parse problem page: {parse_error}")
                # Use fallback placeholder content
                problem_statement = f"Problem {contest_id}{problem_index}: {name}\n\nPlease visit Codeforces to see the full problem statement."
            
            return ProblemContent(
                contestId=contest_id,
                index=problem_index,
                name=name,
                timeLimit=time_limit,
                memoryLimit=memory_limit,
                problemStatement=problem_statement.strip() if problem_statement.strip() else f"Problem {contest_id}{problem_index}: {name}\n\nVisit Codeforces for full statement.",
                inputSpecification=input_spec,
                outputSpecification=output_spec,
                examples=examples,
                note=note,
                rating=rating,
                tags=tags,
                url=url
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching problem content: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching problem content")


# Session management endpoints

# ── NEW: Topic-Aligned Recommendation Endpoint ──────────────────────────

@api_router.get("/recommendations/{user_handle}/{idol_handle}", response_model=RecommendationResponse)
async def get_recommendations(user_handle: str, idol_handle: str, refresh: bool = False):
    """
    Get 3 topic-aligned problem recommendations (easy, medium, hard).
    Analyzes user weaknesses & idol strengths, stores in MongoDB, returns from cache if fresh.
    """
    try:
        # Check MongoDB cache first (unless refresh requested)
        if not refresh:
            cached = await db.recommended_problems.find_one(
                {"userHandle": user_handle, "idolHandle": idol_handle},
                {"_id": 0}
            )
            if cached:
                generated_at = cached.get("generatedAt", "")
                if generated_at:
                    try:
                        gen_time = datetime.fromisoformat(generated_at)
                        age_hours = (datetime.now(timezone.utc) - gen_time).total_seconds() / 3600
                        if age_hours < 24:
                            return RecommendationResponse(
                                recommendations=[
                                    TopicRecommendation(**r) for r in cached.get("recommendations", [])
                                ],
                                description=cached.get("description", ""),
                                userProfile=cached.get("userProfile"),
                                idolProfile=cached.get("idolProfile"),
                                generatedAt=generated_at,
                                cached=True,
                            )
                    except Exception:
                        pass  # stale or invalid, regenerate

        # Build fresh recommendations
        result = await build_recommendations(
            user_handle=user_handle,
            idol_handle=idol_handle,
            gemini_client=gemini_client,
            db=db,
        )

        return RecommendationResponse(
            recommendations=[
                TopicRecommendation(**r) for r in result.get("recommendations", [])
            ],
            description=result.get("description", ""),
            userProfile=result.get("userProfile"),
            idolProfile=result.get("idolProfile"),
            generatedAt=result.get("generatedAt"),
            cached=False,
        )

    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


# ── Check Codeforces Submissions ────────────────────────────────────────


@api_router.get("/check-submissions/{user_handle}")
async def check_codeforces_submissions(user_handle: str, problem_ids: str = ""):
    """
    Check if the user has recently solved specific problems on Codeforces.
    problem_ids: comma-separated list of problem IDs (e.g., "1984C2,2183D1,2077A")
    Returns dict mapping problemId -> { solved: bool, verdict: str }
    """
    try:
        target_ids = set(pid.strip() for pid in problem_ids.split(",") if pid.strip())

        async with httpx.AsyncClient(timeout=15.0) as http_client:
            response = await http_client.get(
                f"https://codeforces.com/api/user.status?handle={user_handle}&from=1&count=30"
            )

            if response.status_code != 200:
                raise HTTPException(status_code=404, detail=f"Could not fetch submissions for {user_handle}")

            data = response.json()
            if data.get("status") != "OK":
                raise HTTPException(status_code=404, detail=f"User {user_handle} not found")

            results = {}
            for submission in data.get("result", []):
                problem = submission.get("problem", {})
                contest_id = problem.get("contestId")
                index = problem.get("index", "")
                if not contest_id or not index:
                    continue

                problem_id = f"{contest_id}{index}"
                verdict = submission.get("verdict", "")

                # Only check problems we care about
                if target_ids and problem_id not in target_ids:
                    continue

                # Mark as solved if verdict is OK
                if problem_id not in results or verdict == "OK":
                    results[problem_id] = {
                        "solved": verdict == "OK",
                        "verdict": verdict,
                    }

        return {"submissions": results}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking submissions: {e}")
        raise HTTPException(status_code=500, detail="Error checking Codeforces submissions")


# ── NEW: Problem History Endpoints ──────────────────────────────────────

@api_router.get("/problem-history/{user_handle}")
async def get_problem_history(user_handle: str, limit: int = 50):
    """
    Get the user's problem attempt history (solved/failed) from this platform.
    Sorted by most recent first.
    """
    try:
        attempts = await db.problem_history.find(
            {"userHandle": user_handle},
            {"_id": 0}
        ).sort("attemptedAt", -1).limit(limit).to_list(limit)
        return {"history": attempts}
    except Exception as e:
        logger.error(f"Error fetching problem history: {e}")
        raise HTTPException(status_code=500, detail="Error fetching problem history")


@api_router.post("/problem-history")
async def record_problem_attempt(attempt: ProblemAttemptCreate):
    """
    Record or update a problem attempt (solved or failed) in the user's history.
    Uses upsert on (userHandle, problemId) so only one entry exists per problem.
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        existing = await db.problem_history.find_one(
            {"userHandle": attempt.userHandle, "problemId": attempt.problemId},
            {"_id": 0}
        )

        if existing:
            # Update existing record with new status and timestamp
            await db.problem_history.update_one(
                {"userHandle": attempt.userHandle, "problemId": attempt.problemId},
                {"$set": {"status": attempt.status, "attemptedAt": now}}
            )
            return {"success": True, "id": existing.get("id", "")}
        else:
            doc = ProblemAttempt(
                userHandle=attempt.userHandle,
                idolHandle=attempt.idolHandle,
                problemId=attempt.problemId,
                contestId=attempt.contestId,
                index=attempt.index,
                name=attempt.name,
                rating=attempt.rating,
                tags=attempt.tags,
                difficulty=attempt.difficulty,
                status=attempt.status,
            )
            await db.problem_history.insert_one(doc.model_dump())
            return {"success": True, "id": doc.id}
    except Exception as e:
        logger.error(f"Error recording problem attempt: {e}")
        raise HTTPException(status_code=500, detail="Error recording problem attempt")


@api_router.put("/problem-history/{attempt_id}/status")
async def update_attempt_status(attempt_id: str, status: str):
    """
    Update the status of a problem attempt (e.g., from 'attempted' to 'solved' or 'failed').
    """
    if status not in ("solved", "failed", "attempted"):
        raise HTTPException(status_code=400, detail="Status must be 'solved', 'failed', or 'attempted'")
    try:
        result = await db.problem_history.update_one(
            {"id": attempt_id},
            {"$set": {"status": status}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Attempt not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating attempt status: {e}")
        raise HTTPException(status_code=500, detail="Error updating attempt status")


@api_router.post("/session")
async def create_session(user_handle: str, idol_handle: str):
    """
    Create or update a user session
    """
    try:
        # Check if session exists
        existing = await db.sessions.find_one({
            "userHandle": user_handle,
            "idolHandle": idol_handle
        }, {"_id": 0})
        
        if existing:
            return existing
        
        # Create new session
        session = UserSession(
            userHandle=user_handle,
            idolHandle=idol_handle
        )
        
        doc = session.model_dump()
        doc['createdAt'] = doc['createdAt'].isoformat()
        doc['updatedAt'] = doc['updatedAt'].isoformat()
        
        await db.sessions.insert_one(doc)
        return session.model_dump()
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating session")


@api_router.get("/session/{user_handle}/{idol_handle}")
async def get_session(user_handle: str, idol_handle: str):
    """
    Get session data
    """
    session = await db.sessions.find_one({
        "userHandle": user_handle,
        "idolHandle": idol_handle
    }, {"_id": 0})
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@api_router.put("/session/{user_handle}/{idol_handle}/mark-solved")
async def mark_problem_solved(user_handle: str, idol_handle: str, problem_id: str):
    """
    Mark a problem as solved in the user's journey
    """
    try:
        result = await db.sessions.update_one(
            {"userHandle": user_handle, "idolHandle": idol_handle},
            {
                "$addToSet": {"solvedProblems": problem_id},
                "$set": {"updatedAt": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"success": True, "problemId": problem_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking problem solved: {str(e)}")
        raise HTTPException(status_code=500, detail="Error marking problem solved")


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return")
):
    # Exclude MongoDB's _id field from the query results with pagination
    # Sort by timestamp descending (newest first)
    status_checks = await db.status_checks.find(
        {}, 
        {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()