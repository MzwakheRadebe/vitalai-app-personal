"""
Seeded doctor accounts — one per department.

These are created automatically at startup if they don't exist.
Each doctor logs in with their email and DOCTOR_PASSWORD.
"""

DOCTORS = [
    {"email": "dr.nkosi@vitalai.demo",     "name": "Dr. Thabo Nkosi",          "department": "General Practice"},
    {"email": "dr.dlamini@vitalai.demo",   "name": "Dr. Sarah Dlamini",         "department": "Pediatrics"},
    {"email": "dr.molefe@vitalai.demo",    "name": "Dr. James Molefe",          "department": "Emergency"},
    {"email": "dr.khumalo@vitalai.demo",   "name": "Dr. Zanele Khumalo",        "department": "Cardiology"},
    {"email": "dr.pillay@vitalai.demo",    "name": "Dr. Priya Pillay",          "department": "Dermatology"},
    {"email": "dr.vanderberg@vitalai.demo","name": "Dr. Michael van der Berg",  "department": "Orthopedics"},
    {"email": "dr.dube@vitalai.demo",      "name": "Dr. Lindiwe Dube",          "department": "Dental"},
]

# Default password for all seeded doctor accounts.
# Doctors should change this after first login (future feature).
DOCTOR_PASSWORD = "Doctor2024!"

# Fast lookup: email → doctor record
DOCTOR_BY_EMAIL: dict = {d["email"]: d for d in DOCTORS}
