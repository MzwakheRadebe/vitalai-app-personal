from fastapi import HTTPException, Request # type: ignore
import time

class MobileRateLimiter:
    def __init__(self):
        self.requests = {}
    
    def check_rate_limit(self, device_id: str, max_requests: int = 100):
        current_time = time.time()
        key = f"{device_id}_{int(current_time // 3600)}"
        
        if key not in self.requests:
            self.requests[key] = 0
        
        self.requests[key] += 1
        
        if self.requests[key] > max_requests:
            raise HTTPException(status_code=429, detail="Too many requests")