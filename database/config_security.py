import os

class SecurityConfig:
    @property
    def mongo_url(self):
        """Get MongoDB URL with existing credentials"""
        return os.getenv("MONGO_URL")
    
    @property
    def mysql_url(self):
        """Get MySQL URL with secure credentials"""
        return os.getenv("MYSQL_URL")
    
    @property
    def is_production(self):
        return os.getenv("ENVIRONMENT") == "production"
    
    def validate_environment(self):
        """Validate all required environment variables are set"""
        required_vars = ["JWT_SECRET", "ENCRYPTION_KEY", "MONGO_URL", "MYSQL_URL"]
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            raise ValueError(f"Missing environment variables: {missing}")