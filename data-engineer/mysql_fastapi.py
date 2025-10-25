# data-engineer/mysql_fastapi.py - UPDATED TO HANDLE FULL_NAME
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from contextlib import contextmanager

from config import DB_CONFIG, API_CONFIG

app = FastAPI(title=\"VitalAI Production API\", version=\"2.0.0\")

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
    except Error as e:
        print(f\"Database connection error: {e}\")
        raise HTTPException(status_code=500, detail=f\"Database connection failed: {e}\")
    finally:
        if conn and conn.is_connected():
            conn.close()

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    age: int
    gender: str
    contact_number: str
    language_preference: str = \"English\"
    id_number: Optional[str] = None
    passport_number: Optional[str] = None
    file_number: Optional[str] = None

@app.get(\"/\")
async def root():
    return {\"message\": \"VitalAI Production API with MySQL\", \"status\": \"running\", \"database\": \"MySQL\"}

@app.post(\"/patients/\")
async def create_patient(patient: PatientCreate):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            # Check which columns exist in the table
            cursor.execute(\"DESCRIBE patients\")
            existing_columns = [col[0] for col in cursor.fetchall()]
            
            # Build dynamic SQL based on available columns
            if 'full_name' in existing_columns:
                # If full_name column exists, we need to provide a value
                if all(col in existing_columns for col in ['id_number', 'passport_number', 'file_number']):
                    # All new columns exist including full_name
                    sql = '''
                        INSERT INTO patients (first_name, last_name, full_name, age, gender, contact_number, language_preference, id_number, passport_number, file_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    '''
                    full_name = f\"{patient.first_name} {patient.last_name}\"
                    values = (
                        patient.first_name, patient.last_name, full_name, patient.age, patient.gender,
                        patient.contact_number, patient.language_preference,
                        patient.id_number, patient.passport_number, patient.file_number
                    )
                else:
                    # Only basic columns exist including full_name
                    sql = '''
                        INSERT INTO patients (first_name, last_name, full_name, age, gender, contact_number, language_preference)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    '''
                    full_name = f\"{patient.first_name} {patient.last_name}\"
                    values = (
                        patient.first_name, patient.last_name, full_name, patient.age, patient.gender,
                        patient.contact_number, patient.language_preference
                    )
            else:
                # full_name column doesn't exist
                if all(col in existing_columns for col in ['id_number', 'passport_number', 'file_number']):
                    # All new columns exist except full_name
                    sql = '''
                        INSERT INTO patients (first_name, last_name, age, gender, contact_number, language_preference, id_number, passport_number, file_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    '''
                    values = (
                        patient.first_name, patient.last_name, patient.age, patient.gender,
                        patient.contact_number, patient.language_preference,
                        patient.id_number, patient.passport_number, patient.file_number
                    )
                else:
                    # Only basic columns exist (no full_name, no new columns)
                    sql = '''
                        INSERT INTO patients (first_name, last_name, age, gender, contact_number, language_preference)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    '''
                    values = (
                        patient.first_name, patient.last_name, patient.age, patient.gender,
                        patient.contact_number, patient.language_preference
                    )
            
            cursor.execute(sql, values)
            patient_id = cursor.lastrowid
            conn.commit()
            
            return {
                \"message\": \"Patient created successfully in MySQL\",
                \"patient_id\": patient_id,
                \"patient_name\": f\"{patient.first_name} {patient.last_name}\",
                \"database\": \"MySQL\"
            }
            
        except Error as e:
            conn.rollback()
            print(f\"Database error: {e}\")
            raise HTTPException(status_code=500, detail=f\"Database error: {e}\")

if __name__ == \"__main__\":
    import uvicorn
    print(\"🚀 Starting VitalAI Production API with MySQL...\")
    uvicorn.run(app, host=API_CONFIG['host'], port=API_CONFIG['port'])
