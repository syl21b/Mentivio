import os
import re
import secrets
import time
import json
from cryptography.fernet import Fernet
import bcrypt
from itsdangerous import URLSafeTimedSerializer
from typing import Dict, Optional, Tuple, Any


class SecurityConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_urlsafe(32))
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))
    MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 16 * 1024 * 1024))
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 100))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', 3600))

    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; "
                                   "script-src 'self' 'unsafe-inline' https://kit.fontawesome.com; "
                                   "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
                                   "img-src 'self' data: https:; "
                                   "font-src 'self' data: https: fonts.gstatic.com; "
                                   "connect-src 'self' http://localhost:5001 ws://localhost:5001;",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=()'
    }

    MAX_INPUT_LENGTH = 500
    MAX_RESPONSES = 50


class SecurityUtils:
    @staticmethod
    def generate_secure_token(length=32):
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def sanitize_input(user_input: str) -> str:
        """Sanitize user input with special handling for age"""
        if not isinstance(user_input, str):
            if isinstance(user_input, (int, float)):
                return str(user_input)
            return str(user_input)

        if user_input.isdigit():
            return user_input.strip()

        sanitized = re.sub(r'[<>"\']', '', user_input)
        return sanitized.strip()[:SecurityConfig.MAX_INPUT_LENGTH]

    @staticmethod
    def validate_patient_data(patient_info: Dict) -> Tuple[bool, str]:
        """Validate patient information for security"""
        try:
            name = patient_info.get('name', '').strip()
            if not name or len(name) > 100:
                return False, "Invalid patient name"

            number = patient_info.get('number', '').strip()
            if not re.match(r'^[a-zA-Z0-9\-_]+$', number):
                return False, "Invalid patient number format"

            age = patient_info.get('age')
            if age is not None:
                if isinstance(age, str):
                    age = age.strip()
                    if not age.isdigit():
                        return False, "Age must be a number between 12-100"
                    age = int(age)

                if not isinstance(age, int):
                    return False, "Age must be a number between 12-100"

                if age < 12 or age > 100:
                    return False, "Age must be between 12-100"

            gender = patient_info.get('gender', '').strip()
            if gender and gender not in ['Male', 'Female', 'Other', 'Prefer not to say', '']:
                return False, "Invalid gender selection"

            return True, "Valid"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def validate_patient_age(age_input) -> Tuple[bool, str]:
        """Specifically validate patient age - ONLY numbers allowed"""
        try:
            if age_input is None or age_input == '':
                return True, ""

            if isinstance(age_input, str):
                age_input = age_input.strip()
                if not age_input.isdigit():
                    return False, "Age must be typed as a number only (digits 0-9). Please enter a valid number like 25"
                age = int(age_input)
            elif isinstance(age_input, (int, float)):
                age = int(age_input)
            else:
                return False, "Age must be a valid number. Please enter only digits (0-9)"

            if age < 12:
                return False, "Age must be 12 or older"
            if age > 100:
                return False, "Age must be 100 or younger"

            return True, f"Valid age: {age}"
        except Exception as e:
            return False, f"Age validation error: {str(e)}"

    @staticmethod
    def validate_coded_responses(coded_responses: Dict) -> Tuple[bool, str]:
        """Validate coded responses format and values"""
        try:
            if not isinstance(coded_responses, dict):
                return False, "Responses must be a dictionary"

            allowed_codes = {
                'YN1', 'YN2', 'FR1', 'FR2', 'FR3', 'FR4',
                'CO1', 'CO2', 'CO3', 'CO4', 'CO5',
                'OP1', 'OP2', 'OP3', 'OP4', 'OP5',
                'SA1', 'SA2', 'SA3', 'SA4', 'SA5'
            }

            allowed_questions = {f'Q{i}' for i in range(1, 18)}

            for question, code in coded_responses.items():
                if question not in allowed_questions:
                    return False, f"Invalid question code: {question}"
                if code not in allowed_codes:
                    return False, f"Invalid response code: {code} for question {question}"

            if len(coded_responses) < 17:
                missing = allowed_questions - set(coded_responses.keys())
                return False, f"Missing responses for questions: {sorted(missing)}"

            return True, "Valid"
        except Exception as e:
            return False, f"Validation error: {str(e)}"


class EncryptionService:
    def __init__(self):
        self.fernet = Fernet(SecurityConfig.ENCRYPTION_KEY)

    def encrypt_data(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def encrypt_dict(self, data: Dict) -> str:
        return self.encrypt_data(json.dumps(data))

    def decrypt_dict(self, encrypted_data: str) -> Dict:
        return json.loads(self.decrypt_data(encrypted_data))


class RateLimiter:
    def __init__(self):
        self.requests = {}

    def is_rate_limited(self, identifier: str, max_requests: int, window: int) -> bool:
        now = time.time()
        window_start = now - window

        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]

        if len(self.requests.get(identifier, [])) >= max_requests:
            return True

        if identifier not in self.requests:
            self.requests[identifier] = []
        self.requests[identifier].append(now)

        return False


class AuthService:
    def __init__(self):
        self.serializer = URLSafeTimedSerializer(SecurityConfig.SECRET_KEY)
        self.active_sessions = {}

    def create_session(self, user_id: str, user_data: Dict) -> str:
        session_id = SecurityUtils.generate_secure_token()
        session_data = {
            'user_id': user_id,
            'user_data': user_data,
            'created_at': time.time(),
            'last_activity': time.time()
        }
        self.active_sessions[session_id] = session_data
        return session_id

    def validate_session(self, session_id: str) -> Optional[Dict]:
        if session_id not in self.active_sessions:
            return None

        session_data = self.active_sessions[session_id]

        if time.time() - session_data['last_activity'] > SecurityConfig.SESSION_TIMEOUT:
            del self.active_sessions[session_id]
            return None

        session_data['last_activity'] = time.time()
        return session_data

    def destroy_session(self, session_id: str):
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]


# Global security instances
encryption_service = EncryptionService()
rate_limiter = RateLimiter()
auth_service = AuthService()