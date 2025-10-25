import time
from fastapi import APIRouter, HTTPException # type: ignore
from auth.ai_auth import AIAuthManager # type: ignore
from monitoring.ai_monitor import AIMonitor # type: ignore
from services.ai_fallback import AIFallbackService # type: ignore
import httpx # type: ignore
import logging

router = APIRouter()
ai_auth = AIAuthManager()
ai_monitor = AIMonitor()
fallback_service = AIFallbackService()

chat_logger = logging.getLogger('chat')

@router.post("/api/chat")
async def chat_with_ai(prompt_data: dict):
    prompt = prompt_data.get("prompt", "")
    user_id = prompt_data.get("user_id", "anonymous")
    
    
    ai_auth.log_ai_request(prompt, user_id)
    
    try:
        
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ai_auth.ai_service_url}/chat",  
                json={"prompt": prompt},
                headers=ai_auth.get_ai_headers(),
                timeout=30.0  
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                ai_response = response.json()
                
                if ai_auth.validate_ai_response(ai_response):
                    ai_monitor.log_ai_call(True, response_time, "/chat")
                    
                    chat_logger.info(
                        f"AI_SUCCESS - User: {user_id} - ResponseTime: {response_time:.2f}s"
                    )
                    
                    return ai_response
                else:
                    raise HTTPException(status_code=502, detail="Invalid AI response format")
            else:
                raise HTTPException(status_code=response.status_code, detail="AI service error")
                
    except Exception as e:
        # Log the failure
        ai_monitor.log_ai_call(False, 0, "/chat")
        chat_logger.error(f"AI_SERVICE_ERROR - User: {user_id} - Error: {str(e)}")
        
        # Use fallback service
        return fallback_service.get_fallback_response(prompt)

@router.get("/api/ai-health")
async def ai_health_check():
    """Health check for Person 3's AI service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ai_auth.ai_service_url}/health",  
                headers=ai_auth.get_ai_headers(),
                timeout=10.0
            )
            
            return {
                "ai_service_status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "model": ai_auth.ai_model
            }
    except Exception as e:
        return {
            "ai_service_status": "unreachable",
            "error": str(e),
            "model": ai_auth.ai_model
        }