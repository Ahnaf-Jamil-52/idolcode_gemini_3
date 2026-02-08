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
from datetime import datetime, timezone
import httpx
import asyncio


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