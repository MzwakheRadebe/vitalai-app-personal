# mysql_fastapi.py - Updated FastAPI with MySQL
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
from contextlib import contextmanager

app = FastAPI(title="VitalAI Production API", version="2.0.0")

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'vitalai_admin',
    'password':'B1tbyB1t.v1t@l.123',
    'database': 'vitalai_prod',
    'charset': 'utf8mb4'
}

@contextmanager
def get_db_connection():
    """Database connection context manager"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
    except Error as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")
    finally:
        if conn and conn.is_connected():
            conn.close()

# Pydantic models (same as before)
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    age: int
    gender: str
    contact_number: str
    language_preference: str = "English"
    id_number: Optional[str] = None
    passport_number: Optional[str] = None
    file_number: Optional[str] = None

class ChatMessage(BaseModel):
    patient_id: Optional[int] = None
    user_message: str

class SymptomReport(BaseModel):
    patient_id: int
    symptom_description: str
    severity_level: str = "Moderate"

class AppointmentRequest(BaseModel):
    patient_id: int
    department: str
    appointment_date: str
    appointment_time: str

# Updated API Endpoints with MySQL
@app.get("/")
async def root():
    return {"message": "VitalAI Production API with MySQL", "status": "running", "database": "MySQL"}

@app.post("/patients/")
async def create_patient(patient: PatientCreate):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO patients (first_name, last_name, age, gender, contact_number, language_preference, id_number, passport_number, file_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (patient.first_name, patient.last_name, patient.age, patient.gender, patient.contact_number, patient.language_preference, patient.id_number, patient.passport_number, patient.file_number))

            patient_id = cursor.lastrowid
            conn.commit()

            return {
                "message": "Patient created successfully in MySQL",
                "patient_id": patient_id,
                "patient_name": f"{patient.first_name} {patient.last_name}",
                "database": "MySQL"
            }
        except Error as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.post("/chat/")
async def chat_with_bot(chat: ChatMessage):
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        try:
            # Simple chatbot logic (will be replaced with AI)
            user_message = chat.user_message.lower()

            if "appointment" in user_message:
                response = "I can help you schedule an appointment. What department do you need?"
                department = "General Medicine"
            elif "symptom" in user_message or "pain" in user_message:
                response = "I can help with symptom assessment. Please describe your symptoms."
                department = "Triage"
            else:
                response = "I'm here to help with appointments, symptoms, and hospital information."
                department = "General Medicine"

            # Log to MySQL
            cursor.execute('''
                INSERT INTO chat_sessions (patient_id, user_message, bot_response, department_suggested)
                VALUES (%s, %s, %s, %s)
            ''', (chat.patient_id, chat.user_message, response, department))

            session_id = cursor.lastrowid
            conn.commit()

            return {
                "session_id": session_id,
                "bot_response": response,
                "suggested_department": department,
                "timestamp": datetime.now().isoformat(),
                "database": "MySQL"
            }
        except Error as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.post("/symptoms/")
async def report_symptoms(symptoms: SymptomReport):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO symptoms (patient_id, symptom_description, severity_level, date_reported)
                VALUES (%s, %s, %s, %s)
            ''', (symptoms.patient_id, symptoms.symptom_description, symptoms.severity_level, datetime.now().date()))

            conn.commit()

            # Enhanced triage logic
            department = "General Medicine"
            if symptoms.severity_level == "High":
                department = "Emergency"
            elif "heart" in symptoms.symptom_description.lower():
                department = "Cardiology"
            elif "child" in symptoms.symptom_description.lower():
                department = "Pediatrics"

            return {
                "message": "Symptoms recorded in MySQL database",
                "suggested_department": department,
                "severity": symptoms.severity_level,
                "database": "MySQL"
            }
        except Error as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute('SELECT * FROM patients WHERE patient_id = %s', (patient_id,))
            patient = cursor.fetchone()

            if patient is None:
                raise HTTPException(status_code=404, detail="Patient not found")

            return patient
        except Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/analytics/overview")
async def get_analytics():
    """New endpoint for data analytics"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        try:
            # Patient statistics
            cursor.execute("SELECT COUNT(*) as total_patients FROM patients")
            patient_count = cursor.fetchone()['total_patients']

            # Symptom statistics
            cursor.execute("SELECT severity_level, COUNT(*) as count FROM symptoms GROUP BY severity_level")
            symptom_stats = cursor.fetchall()

            # Chat statistics
            cursor.execute("SELECT COUNT(*) as total_chats FROM chat_sessions")
            chat_count = cursor.fetchone()['total_chats']

            return {
                "patient_count": patient_count,
                "symptom_statistics": symptom_stats,
                "chat_count": chat_count,
                "database": "MySQL"
            }
        except Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting VitalAI Production API with MySQL...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
