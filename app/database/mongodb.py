# app/database/mongodb.py
import sys
import os
# Add the root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pymongo import MongoClient
from config import MONGO_CONFIG

def test_connection():
    try:
        # Connect to MongoDB Atlas using config.py
        client = MongoClient(MONGO_CONFIG['connection_string'], serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print('✅ Connected to MongoDB Atlas: vitalai-healthcare')
        
        db = client[MONGO_CONFIG['database']]
        print(f"✅ Database: {MONGO_CONFIG['database']}")
        
        # List collections to verify
        collections = db.list_collection_names()
        print(f"✅ Available collections: {collections}")
        
        return True
        
    except Exception as e:
        print(f'❌ MongoDB connection error: {e}')
        print(f"💡 Connection string used: {MONGO_CONFIG['connection_string'][:50]}...")
        return False

if __name__ == '__main__':
    test_connection()
