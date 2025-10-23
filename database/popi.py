# Backend/compliance/popi_enforcer.py
from faker import Faker # type: ignore
import logging

fake = Faker('en_ZA')  
logger = logging.getLogger('security')

class POPIEnforcer:
    @staticmethod
    def validate_no_pii(data: dict) -> bool:
        """Check if data contains potential PII"""
        pii_keywords = ['id_number', 'identity', 'passport', 'medical_aid', 'address']
        for key in data.keys():
            if any(pii in key.lower() for pii in pii_keywords):
                logger.warning(f"Potential PII detected in field: {key}")
                return False
        return True
    
    @staticmethod
    def generate_synthetic_patient():
        """Generate POPI-compliant synthetic patient data"""
        return {
            "patient_id": fake.uuid4(),
            "name": fake.name(),
            "phone": fake.phone_number()[:10],  
            "symptoms": fake.sentence(),
            "department": fake.random_element(['Emergency', 'Pharmacy', 'Dental']),
            "is_synthetic": True  # Always mark as synthetic
        }
    
    @staticmethod
    def sanitize_user_input(input_data: dict) -> dict:
        """Remove any potential PII from user input"""
        sanitized = input_data.copy()
        # Removing fields that might contain PII
        sanitized.pop('id_number', None)
        sanitized.pop('address', None)
        sanitized.pop('medical_details', None)
        return sanitized