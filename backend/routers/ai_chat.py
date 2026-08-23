from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

from backend.config import settings
from backend.routers.auth import get_current_robot
from backend.models.robot import Robot

router = APIRouter(prefix="/api/ai_chat", tags=["AI Expert"])

class AIChatRequest(BaseModel):
    message: str

class AIChatResponse(BaseModel):
    response: str

if settings.AI_API_KEY:
    genai.configure(api_key=settings.AI_API_KEY)
    model = genai.GenerativeModel('gemini-robotics-er-1.6-preview')
else:
    model = None

@router.post("", response_model=AIChatResponse)
def ask_expert(req: AIChatRequest, current_user: Robot = Depends(get_current_robot)):
    if not settings.AI_API_KEY or not model:
        return {"response": f"Hello {current_user.display_name}, your AI engine is ready. Please add your API key to the configuration to activate my neural network."}

    system_prompt = f"You are an advanced Robotics and AI Engineering assistant. The user you are talking to is named {current_user.display_name}. You must provide accurate, highly technical answers regarding C++, Python, Arduino, and Robotics. Address the user by their name naturally in the conversation."
    
    try:
        chat = model.start_chat(history=[
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": [f"Understood. I am ready to assist {current_user.display_name} with robotics engineering."]}
        ])
        
        response = chat.send_message(req.message)
        return {"response": response.text}
    except Exception as e:
        return {"response": f"Error communicating with neural network: {str(e)}"}
