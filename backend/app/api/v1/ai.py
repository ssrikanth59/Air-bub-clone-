import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from app.core.config import settings

router = APIRouter()

class ChatMessage(BaseModel):
    role: str # 'user' or 'assistant' or 'system'
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_grok(request: ChatRequest):
    if not settings.XAI_API_KEY:
        # If API key is not supplied, provide an informative simulated database confirmation response
        user_msg = request.messages[-1].content.lower()
        
        # Strictly conformant database response fallbacks
        if "beachfront" in user_msg or "beach" in user_msg:
          fallback = "Showing 3 beachfront stays."
        elif "300" in user_msg or "budget" in user_msg:
          fallback = "Showing 5 stays under $300."
        elif "tokyo" in user_msg:
          fallback = "Showing 1 loft in Tokyo."
        elif "goa" in user_msg:
          fallback = "Showing 2 stays in Goa."
        else:
          fallback = "No matching properties found."
          
        return ChatResponse(response=fallback)

    # Determine endpoint and model based on the key prefix
    is_groq = settings.XAI_API_KEY.startswith("gsk_")
    url = "https://api.groq.com/openai/v1/chat/completions" if is_groq else "https://api.xai.com/v1/chat/completions"
    model = "llama-3.3-70b-versatile" if is_groq else "grok-beta"

    headers = {
        "Authorization": f"Bearer {settings.XAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Strict search-engine system context prompt
    system_prompt = {
        "role": "system",
        "content": (
            "You are a strict property database search engine. You are NOT a general assistant. "
            "Your only task is to confirm matching properties from our database. "
            "We have stays in: Tokyo (Japan), Paris (France), Aspen (United States), Santorini (Greece), "
            "Kyoto (Japan), Malibu (United States), Rome (Italy), New York (United States), Sydney (Australia), Cairo (Egypt). "
            "We also dynamically seed new stays for real worldwide cities if searched (like Goa, Delhi, Mumbai, Kerala). "
            "Do NOT recommend general tourism, do NOT list random cities, and do NOT make conversational small talk. "
            "Never say things like 'India has a lot to offer', 'Here are popular places', or 'You may like...'. "
            "Keep your responses extremely short, direct, and factual. "
            "Examples of correct responses: "
            "- 'Showing 3 beachfront stays in Malibu.' "
            "- 'Showing 1 loft in Tokyo.' "
            "- 'Showing 2 cabins in Aspen under $300.' "
            "- 'No matching stays found.' "
        )
    }

    messages = [system_prompt] + [
        {"role": m.role, "content": m.content} for m in request.messages
    ]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2  # Keep temperature low for maximum consistency and deterministic output
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload, headers=headers)
            if res.status_code != 200:
                # Return informative error from LLM gateway
                raise HTTPException(
                    status_code=res.status_code,
                    detail=f"AI gateway error ({model}): {res.text}"
                )
            
            data = res.json()
            completion_text = data["choices"][0]["message"]["content"]
            return ChatResponse(response=completion_text)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to communicate with AI completions endpoint: {str(e)}"
        )
