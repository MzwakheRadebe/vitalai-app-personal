import logging
from compliance.popi_enforcer import POPIEnforcer # type: ignore

fallback_logger = logging.getLogger('ai_fallback')

class AIFallbackService:
    def __init__(self):
        self.popi_enforcer = POPIEnforcer()
    
    def get_fallback_response(self, prompt: str, department: str = "general"):
        """Provide fallback responses when AI service is unavailable"""
        fallback_responses = {
            "emergency": "Based on your symptoms, please proceed to the Emergency Department immediately.",
            "pharmacy": "For medication inquiries, please visit the Pharmacy during operating hours.",
            "general": "Thank you for your message. Our healthcare team will assist you shortly.",
            "appointment": "To schedule an appointment, please provide your preferred date and time."
        }
        
        response = fallback_responses.get(department.lower(), fallback_responses["general"])
        
        fallback_logger.warning(
            f"FALLBACK_USED - Prompt: {prompt[:50]}... - Department: {department} - "
            f"Response: {response}"
        )
        
        return {
            "reply": response,
            "is_fallback": True,
            "suggested_department": department
        }