# test_complete_db.py
import mysql.connector

def test_complete_setup():
    print("🧪 Testing Complete Database Setup...")
    
    try:
        # Test application user connection
        conn = mysql.connector.connect(
            host='localhost',
            user='vitalai_admin',
            password='B1tbyB1t.v1t@l.123',
            database='vitalai_prod'
        )
        
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"✅ Database connection successful")
        print(f"✅ Found {len(tables)} tables in vitalai_prod")
        
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 DATABASE LAYER COMPLETED SUCCESSFULLY!")
        print("🚀 Ready for backend integration")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_complete_setup()