from jose import JWTError, jwt # type: ignore
from datetime import datetime, timedelta
import os

class MobileJWTManager:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET")
        self.algorithm = "HS256"
    
    def create_mobile_token(self, device_id: str):
        payload = {
            'device_id': device_id,
            'exp': datetime.utcnow() + timedelta(days=30),
            'iat': datetime.utcnow(),
            'type': 'mobile'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)