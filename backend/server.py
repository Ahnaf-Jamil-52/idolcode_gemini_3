from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import httpx
import asyncio


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
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