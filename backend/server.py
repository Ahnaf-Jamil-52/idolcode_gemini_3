from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import httpx
import asyncio
import re
from bs4 import BeautifulSoup

# Coach Engine imports
from models.coach_state import CoachStateModel, SignalRequest, SignalResponse, ChatRequest, ChatResponse, VoiceRequest, VoiceResponse
from services.coach_core.fusion import FusionEngine
from services.coach_core.responses import ResponseSelector
from services.coach_core.gemini_analyzer import GeminiCoachAnalyzer


ROOT_DIR = Path(__file__).parent
# Load .env.local first (local overrides), then .env as fallback
env_local = ROOT_DIR / '.env.local'
env_file = ROOT_DIR / '.env'
if env_local.exists():
    load_dotenv(env_local, override=True)
elif env_file.exists():
    load_dotenv(env_file)

# MongoDB connection
mongo_url = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url, tlsCAFile=certifi.where())
db = client[os.environ.get('DATABASE_NAME', 'idolcode')]

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

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

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
async def get_user_solved_problems(handle: str):
    """
    Get list of problem IDs that the user has solved
    """
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
            
            return {"handle": handle, "solvedProblems": list(solved_problems)}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user solved problems: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user solved problems")


@api_router.get("/compare/{user_handle}/{idol_handle}", response_model=ComparisonData)
async def compare_users(user_handle: str, idol_handle: str):
    """
    Compare user stats with idol stats
    """
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
        
        return ComparisonData(
            user=user_stats,
            idol=idol_stats,
            progressPercent=round(progress_percent, 1),
            userAhead=user_ahead
        )
        
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
                    
                    # Extract problem statement - get text from divs without class
                    statement_div = soup.select_one('.problem-statement')
                    if statement_div:
                        # Get the main statement text (usually in divs without specific classes)
                        for div in statement_div.find_all('div', recursive=False):
                            class_list = div.get('class', [])
                            if not class_list:
                                problem_statement += div.get_text(separator='\n').strip() + '\n\n'
                    
                    # Extract input specification
                    input_div = soup.select_one('.problem-statement .input-specification')
                    if input_div:
                        input_spec = input_div.get_text(separator='\n').replace('Input', '', 1).strip()
                    
                    # Extract output specification
                    output_div = soup.select_one('.problem-statement .output-specification')
                    if output_div:
                        output_spec = output_div.get_text(separator='\n').replace('Output', '', 1).strip()
                    
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
                        note = note_div.get_text(separator='\n').replace('Note', '', 1).strip()
                        
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


# ==================== COACH ENGINE ENDPOINTS ====================
# The FusionEngine instance - rehydrated per request
coach_engine = FusionEngine()
# Gemini analyzer for AI-powered responses (Phase 4)
gemini_analyzer = GeminiCoachAnalyzer()

@api_router.post("/coach/signal", response_model=SignalResponse)
async def process_coach_signal(request: SignalRequest):
    """
    Process a behavioral signal from the user.
    
    Signal types:
    - run_failure/test_failure: User's code failed a test
    - problem_solved: User solved a problem
    - problem_skipped: User skipped a problem
    - ghost_race_won/ghost_race_lost: Ghost race result
    - idle: User has been idle (value = minutes)
    - hint_requested: User asked for a hint
    - chat: User sent a chat message (include 'message' field)
    """
    collection = db.coach_sessions
    
    # 1. Fetch existing state from MongoDB
    state_doc = await collection.find_one({"user_handle": request.user_handle})
    
    if not state_doc:
        state_doc = CoachStateModel(user_handle=request.user_handle).model_dump()
    else:
        state_doc.pop("_id", None)
    
    # 2. Hydrate the Engine
    coach_engine.load_context(state_doc)
    
    # 3. Process the new signal
    result = coach_engine.process_signal(
        signal_type=request.signal_type,
        value=request.value,
        metadata=request.metadata,
        message=request.message
    )
    
    # 4. Export and persist new state
    new_state = coach_engine.export_context()
    new_state["user_handle"] = request.user_handle
    new_state["last_updated"] = datetime.now(timezone.utc)
    
    await collection.update_one(
        {"user_handle": request.user_handle},
        {"$set": new_state},
        upsert=True
    )
    
    # 5. Return response
    return SignalResponse(
        status="processed",
        new_burnout_score=result["burnout_score"],
        current_state=result["current_state"],
        intervention_level=result["intervention_level"],
        ghost_speed_modifier=result["ghost_speed_modifier"],
        is_masking=result["is_masking"],
        needs_attention=result["needs_attention"],
        coach_response=result["coach_response"],
        recommended_actions=result["recommended_actions"]
    )


@api_router.get("/coach/state/{user_handle}")
async def get_coach_state(user_handle: str):
    """Get current coach state for a user."""
    collection = db.coach_sessions
    state_doc = await collection.find_one({"user_handle": user_handle})
    
    if not state_doc:
        raise HTTPException(status_code=404, detail="No coach session found")
    
    state_doc.pop("_id", None)
    return state_doc


@api_router.delete("/coach/state/{user_handle}")
async def reset_coach_state(user_handle: str):
    """Reset/delete coach state for a user."""
    collection = db.coach_sessions
    result = await collection.delete_one({"user_handle": user_handle})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No coach session found")
    
    return {"status": "deleted", "user_handle": user_handle}


# Initialize response selector for generating coach replies
response_selector = ResponseSelector()

@api_router.post("/coach/chat", response_model=ChatResponse)
async def chat_with_coach(request: ChatRequest):
    """
    Send a chat message to the coach and get a response.
    
    Phase 4: Uses Gemini AI with problem context for intelligent responses.
    
    This endpoint:
    1. Fetches problem context if current_problem_id provided
    2. Processes the message for sentiment
    3. Generates AI-powered contextual response
    """
    collection = db.coach_sessions
    
    # 1. Fetch existing state from MongoDB
    state_doc = await collection.find_one({"user_handle": request.user_handle})
    
    if not state_doc:
        state_doc = CoachStateModel(user_handle=request.user_handle).model_dump()
    else:
        state_doc.pop("_id", None)
    
    # 2. Hydrate the Engine
    coach_engine.load_context(state_doc)
    
    # 3. Process the message (includes sentiment analysis)
    result = coach_engine.process_signal(
        signal_type="chat",
        value=0,
        metadata={},
        message=request.text
    )
    
    # 4. Fetch problem context if available (Phase 4: Context Injection)
    problem_context = None
    if request.current_problem_id:
        # Try to get problem from our scraped problems collection
        problem_context = await db.problems.find_one({"problemId": request.current_problem_id})
        if problem_context:
            problem_context.pop("_id", None)
            print(f"📚 Problem context loaded: {request.current_problem_id}")
        else:
            print(f"⚠️  Problem not found in cache: {request.current_problem_id}")
    
    # 5. Generate AI-powered response with context
    state = result.get("current_state", "NORMAL")
    score = result.get("burnout_score", 0.0)
    emotional_trend = coach_engine.export_context().get("emotional_trend", [])
    sentiment = emotional_trend[-1] if emotional_trend else "NEUTRAL"
    
    # Use Gemini for response generation
    reply = await gemini_analyzer.generate_chat_response(
        user_message=request.text,
        coach_state=state,
        sentiment=sentiment,
        burnout_score=score,
        problem_context=problem_context
    )
    
    # 6. Export and persist new state
    new_state = coach_engine.export_context()
    new_state["user_handle"] = request.user_handle
    new_state["last_updated"] = datetime.now(timezone.utc)
    
    await collection.update_one(
        {"user_handle": request.user_handle},
        {"$set": new_state},
        upsert=True
    )
    
    return ChatResponse(
        reply=reply,
        detected_sentiment=sentiment,
        burnout_score=score,
        intervention_level=result.get("intervention_level", "none")
    )


# ==================== VOICE INTERFACE ====================
@api_router.post("/coach/voice", response_model=VoiceResponse)
async def voice_query(request: VoiceRequest):
    """
    Process a voice recording via Gemini 1.5 Pro multimodal.

    Flow: Mic audio (Base64 webm) → Gemini → coaching response.
    """
    # 1. Fetch problem context if provided
    problem_context = None
    if request.problem_id:
        problem_context = await db.problems.find_one({"problemId": request.problem_id})
        if problem_context:
            problem_context.pop("_id", None)

    # 2. Generate voice response via Gemini multimodal
    reply = await gemini_analyzer.generate_voice_response(
        audio_base64=request.audio_data,
        code_context=request.code_context,
        problem_context=problem_context,
        audio_format=request.audio_format
    )

    # 3. Update burnout state from voice interaction
    collection = db.coach_sessions
    state_doc = await collection.find_one({"user_handle": request.user_handle})
    burnout = 0.0
    if state_doc:
        burnout = state_doc.get("burnout_score", 0.0)

    return VoiceResponse(
        reply=reply,
        detected_intent="voice_query",
        burnout_score=burnout
    )


# ==================== STATUS CHECKS ====================
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