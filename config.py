# config.py - ENHANCED SECURITY CONFIG
import os
import re
import secrets
import hashlib
import time
from typing import Dict, List, Tuple, Optional, Any
from cryptography.fernet import Fernet
import bcrypt
from itsdangerous import URLSafeTimedSerializer
import hmac
import json

class SecurityConfig:
    # Critical - Set via environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_urlsafe(32))
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
    
    # Security settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))
    MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 16 * 1024 * 1024))
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 100))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', 3600))
    MODEL_STORAGE_PATH = os.environ.get('MODEL_STORAGE_PATH', './models/')
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=()'
    }
    
    # Allowed origins
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    
    # File upload restrictions
    ALLOWED_EXTENSIONS = {'csv', 'txt', 'json'}
    ALLOWED_MIME_TYPES = {'text/csv', 'text/plain', 'application/json'}
    
    # Input validation rules
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
        if not isinstance(user_input, str):
            return str(user_input)
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', user_input)
        return sanitized.strip()[:SecurityConfig.MAX_INPUT_LENGTH]
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in SecurityConfig.ALLOWED_EXTENSIONS
    
    @staticmethod
    def generate_csrf_token() -> str:
        return secrets.token_urlsafe(32)

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
        
        # Session timeout
        if time.time() - session_data['last_activity'] > SecurityConfig.SESSION_TIMEOUT:
            del self.active_sessions[session_id]
            return None
        
        session_data['last_activity'] = time.time()
        return session_data
    
    def destroy_session(self, session_id: str):
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]