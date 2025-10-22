# setup_mysql.py
import mysql.connector
from mysql.connector import Error

def setup_production_database():
    try:
        # Connect to MySQL (you'll need to install MySQL server or use cloud)
        connection = mysql.connector.connect(
            host='localhost',  # or your cloud MySQL host
            user='vitalai_admin',
            password='B1tbyB1t.v1t@l.123',
            database='vitalai_prod'
        )
        
        if connection.is_connected():
            print("✅ Connected to MySQL database")
            
            cursor = connection.cursor()
            
            # Create all tables
            tables_sql = [
                """
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    age INT,
                    gender ENUM('Male','Female','Other'),
                    contact_number VARBINARY(255),
                    language_preference VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS symptoms (
                    symptom_id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_id INT NOT NULL,
                    symptom_description TEXT,
                    severity_level ENUM('Low','Moderate','High') DEFAULT 'Low',
                    date_reported DATE,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
                    INDEX idx_symptom_patient (patient_id)
                )
                """,
                # Add all other tables from your schema...
            ]
            
            for sql in tables_sql:
                cursor.execute(sql)
            
            connection.commit()
            print("✅ Production database tables created")
            
    except Error as e:
        print(f"❌ Database error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    setup_production_database()