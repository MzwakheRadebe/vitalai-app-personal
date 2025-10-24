import logging
from datetime import datetime

security_logger = logging.getLogger('security')

class DatabaseMonitor:
    @staticmethod
    def log_database_access(operation: str, collection: str, user: str = "system"):
        security_logger.info(
            f"DB_ACCESS - Operation: {operation} - Collection: {collection} - User: {user} - Time: {datetime.utcnow()}"
        )
    
    @staticmethod
    def log_unusual_activity(activity: str, details: str):
        security_logger.warning(
            f"UNUSUAL_ACTIVITY - {activity} - Details: {details} - Time: {datetime.utcnow()}"
        )