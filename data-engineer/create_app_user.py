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
        cursor.execute("CREATE USER IF NOT EXISTS 'vitalai_admin'@'localhost' IDENTIFIED BY 'B1tbyB1t.v1t@l.123'")
        cursor.execute("GRANT ALL PRIVILEGES ON vitalai_prod.* TO 'vitalai_admin'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        
        print("✅ VitalAI application user created successfully!")
        print("   Username: vitalai_admin")
        print("   Database: vitalai_prod")
        
        # Test the new user
        test_conn = mysql.connector.connect(
            host='localhost',
            user='vitalai_admin',
            password='B1tbyB1t.v1t@l.123',
            database='vitalai_prod'
        )
        print("✅ Application user connection test: PASSED")
        test_conn.close()
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")

if __name__ == "__main__":
    create_vitalai_user()