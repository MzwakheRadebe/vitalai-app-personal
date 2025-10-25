import os

class SecurityConfig:
    @property
    def mongo_url(self):
        """Get MongoDB URL with existing credentials"""
        return os.getenv("mongodb+srv://DB_USER_REDACTED:REDACTED_PASSWORD@MONGO_HOST_REDACTED/vitalai_analytics")
    
    @property
    def mysql_url(self):
        """Get MySQL URL with secure credentials"""
        return os.getenv("mysql://DB_USER_REDACTED:REDACTED_PASSWORD@localhost:3306/vitalai_prod")
    
    @property
    def is_production(self):
        return os.getenv("ENVIRONMENT") == "production"
    
    def validate_environment(self):
        """Validate all required environment variables are set"""
        required_vars = ["JWT_SECRET", "ENCRYPTION_KEY", "mongodb+srv://DB_USER_REDACTED:REDACTED_PASSWORD@MONGO_HOST_REDACTED/vitalai_analytics", "mysql://DB_USER_REDACTED:REDACTED_PASSWORD@localhost:3306/vitalai_prod"]
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:

            raise ValueError(f"Missing environment variables: {missing}")
