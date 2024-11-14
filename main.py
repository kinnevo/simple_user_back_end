# main.py
# Backend Structure (FastAPI)
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone 
from jose import JWTError, jwt
from pydantic import BaseModel
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
print( "MONGODB_URL: ", MONGODB_URL)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str

# FastAPI app setup
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your Nuxt app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
client = AsyncIOMotorClient(MONGODB_URL)
db = client.DLE
users_collection = db.Users
print("XXXXX users_collection: ", users_collection)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user(username: str):
    print("username: ", username)
    user = await users_collection.find_one({"username": username})
    print("YYY user: ", user)
    return user

async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    print("XXXXX user: ", user["username"])
    if not user:
        print("No user")
        return False
    if not verify_password(password, user["password"]):
        print("No password")
        return False
    return user

async def register_user(username: str, password: str):
    # Hash the password
    hashed_password = pwd_context.hash(password)
    
    # Check if user already exists
    if await users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="username already registered")
    
    # Create user document
    user = {
        "username": username,
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc)
    }
    
    # Insert into database
    result = await users_collection.insert_one(user)
    
    return {"id": str(result.inserted_id), "username": username}

# Routes
@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print("Debug message", file=sys.stderr)  # This will show up in red in VS Code's debug console
    user = await authenticate_user(form_data.username, form_data.password)
    print("LOGIN: ", user)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user["username"]}
    )
    
    return {"token": access_token, "token_type": "bearer"}

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user: UserCreate):
    return await register_user(user.username, user.password)