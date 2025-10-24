import logging
from pymongo.errors import OperationFailure # type: ignore

security_logger = logging.getLogger('security')

class MongoSecurity:
    @staticmethod
    def validate_mongo_connection(client):
        """Validate MongoDB connection and permissions"""
        try:
            # Test connection and basic read permission
            client.admin.command('ping')
            security_logger.info("MongoDB connection successful")
            return True
        except OperationFailure as e:
            security_logger.error(f"MongoDB permission error: {e}")
            return False