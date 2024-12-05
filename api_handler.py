from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import openai
from datetime import datetime
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from config.database import get_database

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Create router
router = APIRouter(prefix="/api/chat", tags=["chat"])

# Models
class ChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None
    model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4000
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    error: bool = False
    usage: Dict[str, Any]
    created_at: datetime

# ChatGPT handler
async def get_chatgpt_response(
    message: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = "gpt-4",
    temperature: Optional[float] = 0.7,
    max_tokens: Optional[int] = 4000
) -> Dict[str, Any]:
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        response = openai.chat.completions.create(
            model=model or "gpt-4",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Check if we have a valid response
        if not response.choices or len(response.choices) == 0:
            return {
                "response": "Error: No response generated",
                "error": True,
                "usage": {},
                "created_at": datetime.now()
            }
            
        return {
            "response": response.choices[0].message.content,
            "error": False,
            "usage": response.usage,
            "created_at": datetime.now()
        }
        
    except openai.APIError as e:
        return {
            "response": f"OpenAI API Error: {str(e)}",
            "error": True,
            "usage": {},
            "created_at": datetime.now()
        }
    except Exception as e:
        return {
            "response": f"Unexpected error: {str(e)}",
            "error": True,
            "usage": {},
            "created_at": datetime.now()
        }

# Routes
@router.post("/completion", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    db2 = Depends(get_database)  # Remove type hint for db
):
    """
    Handle chat completion requests with configurable parameters.
    """
    print("request",request)

    try:
        system_prompt = request.system_prompt
        prompt_doc = await db2.prompts.find_one({"name": "Técnica Persona"})
        if prompt_doc:
            system_prompt = prompt_doc.get("prompt")

        response = await get_chatgpt_response(
            message=request.message,
            system_prompt=system_prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        print(response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_available_models():
    """
    Get available ChatGPT models.
    """
    try:
        models = openai.models.list()
        return [model.id for model in models.data if "gpt" in model.id.lower()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 