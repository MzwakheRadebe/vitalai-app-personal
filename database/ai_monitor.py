import logging
import time
from datetime import datetime

ai_logger = logging.getLogger('ai_service')

class AIMonitor:
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
    
    def log_ai_call(self, success: bool, response_time: float, endpoint: str):
        """Monitor AI service performance and reliability"""
        self.request_count += 1
        
        if not success:
            self.error_count += 1
        
        ai_logger.info(
            f"AI_CALL - Endpoint: {endpoint} - Success: {success} - "
            f"ResponseTime: {response_time:.2f}s - "
            f"ErrorRate: {(self.error_count/self.request_count)*100:.1f}%"
        )
    
    def get_health_status(self) -> dict:
        """Get AI service health metrics"""
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate_percent": error_rate,
            "service_status": "healthy" if error_rate < 10 else "degraded"
        }