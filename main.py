# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from typing import Optional
import json
from datetime import datetime
import os
from fastapi.encoders import jsonable_encoder

from dotenv import load_dotenv

load_dotenv()

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
print( "MONGODB_URL: ", MONGODB_URL)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
app = FastAPI()

# MongoDB connection
client = AsyncIOMotorClient(MONGODB_URL)
db = client.session_db
sessions_collection = db.sessions
print("XXXXX sessions_collection: ", sessions_collection)

class SessionStage(BaseModel):
    stage: int
    data: dict
    
class Session(BaseModel):
    id: Optional[str]
    current_stage: int
    stages: dict
    created_at: datetime
    updated_at: datetime

@app.post("/api/sessions")
async def create_session():
    session = {
        "current_stage": 1,
        "stages": {
            "1": {},  # Empty data for stage 1
            "2": {},  # Empty data for stage 2
            "3": {}   # Empty data for stage 3
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await sessions_collection.insert_one(session)
    session["_id"] = str(result.inserted_id)  # Convert ObjectId to string

    # Use jsonable_encoder to ensure all fields are JSON serializable
    json_compatible_session_data = jsonable_encoder(session)
    print("XXXXX session: ", session)
    return json_compatible_session_data


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["id"] = str(session["_id"])
    del session["_id"]
    print("Session Id:", session)
    return session

@app.put("/api/sessions/{session_id}/stage/{stage}")
async def update_stage(session_id: str, stage: int, stage_data: SessionStage):
    if stage not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Invalid stage number")
        
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update stage data and current stage
    update_data = {
        f"stages.{stage}": stage_data.data,
        "current_stage": stage,
        "updated_at": datetime.utcnow()
    }
    
    await sessions_collection.update_one(
        {"_id": ObjectId(session_id)},
        {"$set": update_data}
    )
    
    return {"message": f"Stage {stage} updated successfully"}

@app.put("/api/sessions/{session_id}/move/{direction}")
async def move_stage(session_id: str, direction: str):
    if direction not in ["next", "previous"]:
        raise HTTPException(status_code=400, detail="Invalid direction")
        
    session = await sessions_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    current_stage = session["current_stage"]
    if direction == "next" and current_stage < 3:
        new_stage = current_stage + 1
    elif direction == "previous" and current_stage > 1:
        new_stage = current_stage - 1
    else:
        raise HTTPException(status_code=400, detail="Cannot move in that direction")
    
    await sessions_collection.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$set": {
                "current_stage": new_stage,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": f"Moved to stage {new_stage}"}