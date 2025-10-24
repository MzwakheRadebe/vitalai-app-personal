import datetime
import http
import os


class EnhancedHealthMonitor:
    def get_system_health(self):
        base_health = {
            "backend": "healthy",
            "mysql": "healthy", 
            "mongodb": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add AI service health
        ai_health = self.check_ai_service_health()
        base_health["ai_service"] = ai_health
        
        return base_health
    
    async def check_ai_service_health(self):
        """Check Person 3's AI service health"""
        try:
            async with http.AsyncClient() as client:
                response = await client.get(
                    f"{os.getenv('AI_SERVICE_URL')}/health",
                    timeout=5.0
                )
                return "healthy" if response.status_code == 200 else "unhealthy"
        except:
            return "unreachable"