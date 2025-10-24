# complete_database_setup.py
import mysql.connector

def setup_complete_database():
    print("🚀 Setting up complete VitalAI database...")

    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='vitalai_admin',
            password='B1tbyB1t.v1t@l.123',
            database='vitalai_prod'
        )

        cursor = conn.cursor()

        # Drop and recreate all tables to ensure consistency
        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS patients (
                patient_id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                id_number CHAR(13) UNIQUE,
                passport_number CHAR(13) UNIQUE,
                file_number CHAR(10) UNIQUE,
                age INT,
                gender ENUM('Male','Female','Other'),
                contact_number VARCHAR(255),
                language_preference VARCHAR(50) DEFAULT 'English',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_patient_name (first_name, last_name),
                INDEX idx_id_number (id_number),
                INDEX idx_passport (passport_number),
                INDEX idx_file_number (file_number)
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
                INDEX idx_symptom_patient (patient_id),
                INDEX idx_severity (severity_level)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT,
                user_message TEXT,
                bot_response TEXT,
                department_suggested VARCHAR(100),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE SET NULL,
                INDEX idx_chat_timestamp (timestamp)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT NOT NULL,
                department VARCHAR(100),
                appointment_date DATE,
                appointment_time TIME,
                status ENUM('Scheduled','Cancelled','Completed','No-Show') DEFAULT 'Scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
                INDEX idx_appointment_date (appointment_date),
                INDEX idx_appointment_status (status)
            )
            """
        ]

        for sql in tables_sql:
            try:
                cursor.execute(sql)
                print("✅ Table created/verified")
            except Exception as e:
                print(f"⚠️ Table creation note: {e}")

        conn.commit()

        # Verify all tables exist
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"\n📊 Database now has {len(tables)} tables:")
        for table in tables:
            print(f"   ✅ {table[0]}")

        cursor.close()
        conn.close()

        print("\n🎉 VITALAI DATABASE COMPLETELY READY!")

    except Exception as e:
        print(f"❌ Database setup failed: {e}")

if __name__ == "__main__":
    setup_complete_database()
