# create_app_user.py
import mysql.connector

def create_vitalai_user():
    try:
        # Connect as root
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Vitalroot!123'
        )
        
        cursor = conn.cursor()
        
        # Create dedicated user for VitalAI
        cursor.execute("CREATE USER IF NOT EXISTS 'DB_USER_REDACTED'@'localhost' IDENTIFIED BY 'REDACTED_PASSWORD'")
        cursor.execute("GRANT ALL PRIVILEGES ON vitalai_prod.* TO 'DB_USER_REDACTED'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        
        print("✅ VitalAI application user created successfully!")
        print("   Username: DB_USER_REDACTED")
        print("   Database: vitalai_prod")
        
        # Test the new user
        test_conn = mysql.connector.connect(
            host='localhost',
            user='DB_USER_REDACTED',
            password='REDACTED_PASSWORD',
            database='vitalai_prod'
        )
        print("✅ Application user connection test: PASSED")
        test_conn.close()
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")

if __name__ == "__main__":
    create_vitalai_user()