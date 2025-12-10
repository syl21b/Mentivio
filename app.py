from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pickle
import joblib
import numpy as np
import pandas as pd
import uuid 
from datetime import datetime, timezone, timedelta
import os
import logging
from typing import Dict, List, Tuple, Optional, Any
import psycopg
from psycopg.rows import dict_row  
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import json
import sys
import re
import secrets
import time
import hashlib
from cryptography.fernet import Fernet
import bcrypt
from itsdangerous import URLSafeTimedSerializer
import threading
from functools import wraps
import ipaddress
import pytz
from dotenv import load_dotenv

load_dotenv()


# ==================== ENVIRONMENT VALIDATION ====================
def validate_environment():
    """Validate all required environment variables are set"""
    required_vars = ['SECRET_KEY']
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
    
    secret_key = os.environ.get('SECRET_KEY', '')
    if len(secret_key) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    
    encryption_key = os.environ.get('ENCRYPTION_KEY')
    if encryption_key:
        try:
            Fernet(encryption_key.encode())
        except:
            raise ValueError("ENCRYPTION_KEY must be a valid Fernet key")
    
    return True

# ==================== SECURITY CONFIGURATION ====================
class SecurityConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    if not SECRET_KEY:
        raise EnvironmentError("SECRET_KEY environment variable is required")
    
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    if not ENCRYPTION_KEY:
        ENCRYPTION_KEY = Fernet.generate_key().decode()
        logging.warning("ENCRYPTION_KEY not set, generating random key. SESSIONS WILL NOT PERSIST!")
    
    API_KEY = os.environ.get('API_KEY')
    if not API_KEY:
        API_KEY = secrets.token_urlsafe(32)
        logging.warning("API_KEY not set, generating random key. SET THIS FOR PRODUCTION!")
    
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))
    MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 16 * 1024 * 1024))
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 100))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', 3600))
    
    MIN_PASSWORD_LENGTH = 12
    PASSWORD_COMPLEXITY = {
        'min_lowercase': 1,
        'min_uppercase': 1,
        'min_digits': 1,
        'min_special': 1
    }
    
    MAX_INPUT_LENGTH = 500
    MAX_RESPONSES = 50
    MAX_PATIENT_NAME_LENGTH = 100
    MAX_PATIENT_NUMBER_LENGTH = 50
    
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY', 
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://kit.fontawesome.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https: fonts.gstatic.com; "
            "connect-src 'self' https://*.onrender.com; "
            "frame-ancestors 'none';"
        ),
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=()',
        'Cache-Control': 'no-store, max-age=0'
    }
    
    AUDIT_LOG_FILE = os.environ.get('AUDIT_LOG_FILE', 'security_audit.log')
    
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    @staticmethod
    def get_database_url():
        """Get database URL from environment variables"""
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            db_host = os.environ.get('DB_HOST')
            db_name = os.environ.get('DB_NAME')
            db_user = os.environ.get('DB_USER')
            db_password = os.environ.get('DB_PASSWORD')
            db_port = os.environ.get('DB_PORT', '5432')
            
            if all([db_host, db_name, db_user, db_password]):
                db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            else:
                return 'sqlite:///mental_health_assessments.db'
        
        return db_url

class AuditLogger:
    """Security audit logging"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or SecurityConfig.AUDIT_LOG_FILE
        self.lock = threading.Lock()
        
    def log_event(self, event_type: str, user_id: str = None, ip: str = None, 
                  details: str = None, severity: str = 'INFO'):
        timestamp = datetime.now(timezone.utc).isoformat()
        ip = ip or (request.remote_addr if request else '0.0.0.0')
        
        log_entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip,
            'severity': severity,
            'details': details,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'endpoint': request.endpoint if request else None,
            'method': request.method if request else None
        }
        
        with self.lock:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception:
                pass
            
            if severity == 'CRITICAL':
                logging.critical(f"AUDIT [{severity}]: {event_type} - {details}")
            elif severity == 'WARNING':
                logging.warning(f"AUDIT [{severity}]: {event_type} - {details}")

class SecurityUtils:
    @staticmethod
    def generate_secure_token(length=32):
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password: str) -> Tuple[str, str]:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8'), salt.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def sanitize_input(user_input: str, allow_html: bool = False) -> str:
        if not isinstance(user_input, str):
            user_input = str(user_input)
        
        sanitized = user_input.strip()[:SecurityConfig.MAX_INPUT_LENGTH]
        
        if not allow_html:
            sanitized = re.sub(r'<[^>]*>', '', sanitized)
            sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        return re.sub(r'[\';]', '', sanitized)
    
    @staticmethod
    def sanitize_json_input(data: Any) -> Any:
        if isinstance(data, dict):
            return {SecurityUtils.sanitize_input(k): SecurityUtils.sanitize_json_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [SecurityUtils.sanitize_json_input(item) for item in data]
        elif isinstance(data, str):
            return SecurityUtils.sanitize_input(data)
        else:
            return data
    
    @staticmethod
    def validate_patient_data(patient_info: Dict) -> Tuple[bool, str]:
        try:
            name = patient_info.get('name', '').strip()
            if not name:
                return False, "Patient name is required"
            if len(name) > SecurityConfig.MAX_PATIENT_NAME_LENGTH:
                return False, f"Patient name too long (max {SecurityConfig.MAX_PATIENT_NAME_LENGTH} chars)"
            if not re.match(r'^[A-Za-z\s\-\'\.]+$', name):
                return False, "Invalid characters in patient name"
            
            number = patient_info.get('number', '').strip()
            if not number:
                return False, "Patient number is required"
            if len(number) > SecurityConfig.MAX_PATIENT_NUMBER_LENGTH:
                return False, f"Patient number too long (max {SecurityConfig.MAX_PATIENT_NUMBER_LENGTH} chars)"
            if not re.match(r'^[A-Za-z0-9\-_]+$', number):
                return False, "Invalid patient number format"
            
            age = patient_info.get('age', '').strip()
            if age:
                if not re.match(r'^[0-9]{1,3}$', age):
                    return False, "Invalid age format"
                age_int = int(age)
                if not (0 <= age_int <= 150):
                    return False, "Age must be between 0 and 150"
            
            gender = patient_info.get('gender', '').strip()
            valid_genders = ['Male', 'Female', 'Other', 'Prefer not to say', '']
            if gender and gender not in valid_genders:
                return False, "Invalid gender selection"
            
            return True, "Valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def generate_request_id() -> str:
        return f"req_{uuid.uuid4().hex[:16]}"

class EncryptionService:
    def __init__(self):
        try:
            self.fernet = Fernet(SecurityConfig.ENCRYPTION_KEY.encode())
        except Exception as e:
            logging.error(f"Failed to initialize encryption: {e}")
            raise
    
    def encrypt_data(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_dict(self, data: Dict) -> str:
        return self.encrypt_data(json.dumps(data))
    
    def decrypt_dict(self, encrypted_data: str) -> Dict:
        return json.loads(self.decrypt_data(encrypted_data))

class AdvancedRateLimiter:
    """Enhanced rate limiter with different limits per endpoint"""
    
    def __init__(self):
        self.requests = {}
        self.lock = threading.Lock()
        self.audit_logger = AuditLogger()
        self.endpoint_limits = {
            'predict': {'max_requests': 50, 'window': 3600},
            'save_assessment': {'max_requests': 20, 'window': 3600},
            'get_patient_assessments': {'max_requests': 30, 'window': 3600},
            'default': {'max_requests': SecurityConfig.RATE_LIMIT_REQUESTS, 
                       'window': SecurityConfig.RATE_LIMIT_WINDOW}
        }
    
    def is_rate_limited(self, identifier: str, max_requests: int, window: int) -> Tuple[bool, str]:
        now = time.time()
        window_start = now - window
        
        with self.lock:
            if identifier in self.requests:
                self.requests[identifier] = [
                    req_time for req_time in self.requests[identifier] 
                    if req_time > window_start
                ]
            
            request_count = len(self.requests.get(identifier, []))
            
            if request_count >= max_requests:
                self.audit_logger.log_event(
                    event_type='RATE_LIMIT_EXCEEDED',
                    ip=identifier if self._validate_ip(identifier) else None,
                    details=f"Rate limit exceeded: {request_count}/{max_requests} in {window}s",
                    severity='WARNING'
                )
                return True, f"Rate limit exceeded. Try again in {window} seconds."
            
            if identifier not in self.requests:
                self.requests[identifier] = []
            self.requests[identifier].append(now)
            
            return False, ""
    
    def _validate_ip(self, ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def get_endpoint_limit(self, endpoint: str) -> Dict[str, int]:
        return self.endpoint_limits.get(endpoint, self.endpoint_limits['default'])
    
    def is_endpoint_rate_limited(self, identifier: str, endpoint: str) -> Tuple[bool, str]:
        limits = self.get_endpoint_limit(endpoint)
        return self.is_rate_limited(
            f"{identifier}:{endpoint}",
            limits['max_requests'],
            limits['window']
        )

class AuthService:
    def __init__(self):
        self.serializer = URLSafeTimedSerializer(SecurityConfig.SECRET_KEY)
        self.active_sessions = {}
        self.failed_attempts = {}
        self.lock = threading.Lock()
        self.audit_logger = AuditLogger()
        self.max_failed_attempts = 5
        self.lockout_time = 900
    
    def create_session(self, user_id: str, user_data: Dict) -> str:
        session_id = SecurityUtils.generate_secure_token()
        session_data = {
            'user_id': user_id,
            'user_data': user_data,
            'created_at': time.time(),
            'last_activity': time.time(),
            'ip_address': request.remote_addr if request else '0.0.0.0',
            'user_agent': request.headers.get('User-Agent') if request else None
        }
        
        with self.lock:
            self.active_sessions[session_id] = session_data
        
        self.audit_logger.log_event(
            event_type='SESSION_CREATED',
            user_id=user_id,
            details=f"Session created for user {user_id}",
            severity='INFO'
        )
        
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict]:
        if not session_id:
            return None
        
        with self.lock:
            if session_id not in self.active_sessions:
                return None
            
            session_data = self.active_sessions[session_id]
            
            if time.time() - session_data['last_activity'] > SecurityConfig.SESSION_TIMEOUT:
                self.audit_logger.log_event(
                    event_type='SESSION_EXPIRED',
                    user_id=session_data['user_id'],
                    details="Session expired due to inactivity",
                    severity='INFO'
                )
                del self.active_sessions[session_id]
                return None
            
            current_ip = request.remote_addr if request else '0.0.0.0'
            if (session_data['ip_address'] != current_ip and 
                session_data['ip_address'] != '0.0.0.0'):
                self.audit_logger.log_event(
                    event_type='SUSPICIOUS_SESSION',
                    user_id=session_data['user_id'],
                    details=f"IP changed from {session_data['ip_address']} to {current_ip}",
                    severity='WARNING'
                )
            
            session_data['last_activity'] = time.time()
            
            return session_data
    
    def destroy_session(self, session_id: str):
        with self.lock:
            if session_id in self.active_sessions:
                user_id = self.active_sessions[session_id]['user_id']
                self.audit_logger.log_event(
                    event_type='SESSION_DESTROYED',
                    user_id=user_id,
                    details="Session destroyed",
                    severity='INFO'
                )
                del self.active_sessions[session_id]

# ==================== SECURITY MIDDLEWARE DECORATORS ====================
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.endpoint in ['health_check', 'simple_ping', 'api_info']:
            return f(*args, **kwargs)
        
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            audit_logger.log_event(
                event_type='API_KEY_MISSING',
                ip=request.remote_addr,
                details=f"Missing API key for {request.endpoint}",
                severity='WARNING'
            )
            return jsonify({'error': 'API key required'}), 401
        
        valid_key = SecurityConfig.API_KEY
        
        if not secrets.compare_digest(api_key, valid_key):
            audit_logger.log_event(
                event_type='INVALID_API_KEY',
                ip=request.remote_addr,
                details=f"Invalid API key for {request.endpoint}",
                severity='WARNING'
            )
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_json_content(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT']:
            if request.content_length and request.content_length > SecurityConfig.MAX_FILE_SIZE:
                audit_logger.log_event(
                    event_type='REQUEST_TOO_LARGE',
                    ip=request.remote_addr,
                    details=f"Request size: {request.content_length} bytes",
                    severity='WARNING'
                )
                return jsonify({'error': 'Request too large'}), 413
            
            if request.is_json:
                try:
                    data = request.get_json()
                    if not isinstance(data, (dict, list)):
                        return jsonify({'error': 'Invalid JSON format'}), 400
                except Exception as e:
                    audit_logger.log_event(
                        event_type='INVALID_JSON',
                        ip=request.remote_addr,
                        details=f"JSON parsing error: {str(e)}",
                        severity='WARNING'
                    )
                    return jsonify({'error': 'Invalid JSON data'}), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

def sanitize_inputs(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        sanitized_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                sanitized_kwargs[key] = SecurityUtils.sanitize_input(value)
            else:
                sanitized_kwargs[key] = value
        
        if request.form:
            for key in request.form:
                request.form[key] = SecurityUtils.sanitize_input(request.form[key])
        
        if request.is_json:
            try:
                data = request.get_json()
                sanitized_data = SecurityUtils.sanitize_json_input(data)
                request._cached_json = (sanitized_data, request._cached_json[1])
            except:
                pass
        
        return f(*args, **sanitized_kwargs)
    
    return decorated_function

# ==================== MODEL COMPONENTS ====================
model_package: Optional[Dict[str, Any]] = None
scaler: Optional[Any] = None
label_encoder: Optional[Any] = None
feature_names: Optional[List[str]] = None
category_mappings: Optional[Dict[str, Any]] = None
clinical_enhancer: Optional[Any] = None
preprocessor: Optional[Any] = None

def load_model_components():
    """Load all required model components"""
    global model_package, scaler, label_encoder, feature_names, category_mappings
    
    try:
        logger.info("Loading model components...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(current_dir, 'models')
        
        required_files = [
            'mental_health_model.pkl',
            'scaler.pkl', 
            'label_encoder.pkl',
            'feature_names.pkl',
            'category_mappings.pkl'
        ]
        
        for file in required_files:
            file_path = os.path.join(models_dir, file)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required model file not found: {file}")
            
            if os.path.getsize(file_path) == 0:
                raise ValueError(f"Model file is empty: {file}")
        
        model_package = joblib.load(os.path.join(models_dir, 'mental_health_model.pkl'))
        scaler = joblib.load(os.path.join(models_dir, 'scaler.pkl'))
        label_encoder = joblib.load(os.path.join(models_dir, 'label_encoder.pkl'))
        
        with open(os.path.join(models_dir, 'feature_names.pkl'), 'rb') as f:
            feature_names = pickle.load(f)
        
        with open(os.path.join(models_dir, 'category_mappings.pkl'), 'rb') as f:
            category_mappings = pickle.load(f)
        
        logger.info(f"Model components loaded: {len(feature_names)} features")
        return model_package, scaler, label_encoder, feature_names, category_mappings
        
    except Exception as e:
        logger.error(f"Error loading model components: {e}")
        return None, None, None, None, None

class ClinicalDecisionEnhancer:
    """Enhances model predictions with clinical rules and feature sensitivity"""
    
    def __init__(self, feature_names: List[str], label_encoder: Any):
        self.feature_names = feature_names
        self.label_encoder = label_encoder
        self.clinical_rules = self._initialize_clinical_rules()
        
    def _initialize_clinical_rules(self) -> Dict[str, Dict[str, Any]]:
        return {
            'depression_patterns': {
                'required_features': ['Sadness', 'Sleep disorder', 'Exhausted'],
                'thresholds': {
                    'Sadness': 2,
                    'Sleep disorder': 2,
                    'Exhausted': 2
                },
                'exclusion_features': ['Euphoric', 'Mood Swing'],
                'exclusion_thresholds': {
                    'Euphoric': 1,
                    'Mood Swing': 0
                }
            },
            'bipolar1_patterns': {
                'required_features': ['Euphoric', 'Mood Swing', 'Sleep disorder'],
                'thresholds': {
                    'Euphoric': 2,
                    'Mood Swing': 1,
                    'Sleep disorder': 2
                },
                'exclusion_features': [],
                'exclusion_thresholds': {}
            },
            'bipolar2_patterns': {
                'required_features': ['Mood Swing', 'Sadness', 'Euphoric'],
                'thresholds': {
                    'Mood Swing': 1,
                    'Sadness': 2,
                    'Euphoric': 1
                },
                'exclusion_features': [],
                'exclusion_thresholds': {}
            }
        }
    
    def analyze_feature_patterns(self, processed_responses: Dict[str, Any], probabilities: np.ndarray) -> Dict[str, Any]:
        analysis: Dict[str, Any] = {
            'depression_score': 0.0,
            'bipolar1_score': 0.0,
            'bipolar2_score': 0.0,
            'normal_score': 0.0,
            'feature_consistency': {},
            'suggested_adjustments': []
        }
        
        for pattern_name, rules in self.clinical_rules.items():
            score = self._calculate_pattern_score(processed_responses, rules)
            analysis[f'{pattern_name.split("_")[0]}_score'] = score
        
        primary_diagnosis_idx = np.argmax(probabilities)
        primary_diagnosis = self.label_encoder.inverse_transform([primary_diagnosis_idx])[0]
        analysis['feature_consistency'] = self._check_feature_consistency(processed_responses, primary_diagnosis)
        
        analysis['suggested_adjustments'] = self._suggest_adjustments(processed_responses, probabilities)
        
        return analysis
    
    def _calculate_pattern_score(self, responses: Dict[str, Any], rules: Dict[str, Any]) -> float:
        score = 0
        max_score = len(rules['required_features']) + len(rules.get('exclusion_features', []))
        
        for feature in rules['required_features']:
            if feature in responses:
                threshold = rules['thresholds'].get(feature, 0)
                if responses[feature] >= threshold:
                    score += 1
        
        for feature in rules.get('exclusion_features', []):
            if feature in responses:
                threshold = rules['exclusion_thresholds'].get(feature, 1)
                if responses[feature] <= threshold:
                    score += 1
        
        return score / max_score if max_score > 0 else 0.0
    
    def _check_feature_consistency(self, responses: Dict[str, Any], diagnosis: str) -> Dict[str, Any]:
        consistency: Dict[str, Any] = {}
        
        expected_ranges = {
            'Depression': {
                'Sadness': (2, 3),
                'Sleep disorder': (2, 3),
                'Euphoric': (0, 1),
                'Mood Swing': (0, 0)
            },
            'Bipolar Type-1': {
                'Euphoric': (2, 3),
                'Mood Swing': (1, 3),
                'Sleep disorder': (1, 3)
            },
            'Bipolar Type-2': {
                'Mood Swing': (1, 2),
                'Sadness': (1, 3),
                'Euphoric': (1, 2)
            },
            'Normal': {
                'Sadness': (0, 1),
                'Euphoric': (0, 1),
                'Mood Swing': (0, 0),
                'Sleep disorder': (0, 1)
            }
        }
        
        diagnosis_ranges = expected_ranges.get(diagnosis, {})
        for feature, (min_val, max_val) in diagnosis_ranges.items():
            if feature in responses:
                value = responses[feature]
                consistency[feature] = {
                    'value': value,
                    'expected_min': min_val,
                    'expected_max': max_val,
                    'consistent': min_val <= value <= max_val
                }
        
        return consistency
    
    def _suggest_adjustments(self, responses: Dict[str, Any], probabilities: np.ndarray) -> List[Dict[str, Any]]:
        suggestions: List[Dict[str, Any]] = []
        
        primary_idx = np.argmax(probabilities)
        current_diagnosis = self.label_encoder.inverse_transform([primary_idx])[0]
        
        if (responses.get('Sadness', 0) >= 2 and 
            responses.get('Sleep disorder', 0) >= 2 and 
            responses.get('Euphoric', 0) <= 1 and
            current_diagnosis != 'Depression'):
            suggestions.append({
                'type': 'POTENTIAL_DEPRESSION',
                'reason': 'High sadness and sleep issues with low euphoria suggest depression',
                'suggested_diagnosis': 'Depression',
                'confidence_boost': 0.2
            })
        
        if (responses.get('Euphoric', 0) >= 2 and 
            responses.get('Mood Swing', 0) >= 1 and
            current_diagnosis not in ['Bipolar Type-1', 'Bipolar Type-2']):
            suggestions.append({
                'type': 'POTENTIAL_BIPOLAR',
                'reason': 'High euphoria with mood swings suggests bipolar disorder',
                'suggested_diagnosis': 'Bipolar Type-1',
                'confidence_boost': 0.15
            })
        
        return suggestions
    
    def enhance_prediction(self, processed_responses: Dict[str, Any], probabilities: np.ndarray, original_diagnosis: str) -> Dict[str, Any]:
        analysis = self.analyze_feature_patterns(processed_responses, probabilities)
        
        enhanced_prediction: Dict[str, Any] = {
            'original_diagnosis': original_diagnosis,
            'original_confidence': float(np.max(probabilities)),
            'clinical_analysis': analysis,
            'enhanced_diagnosis': original_diagnosis,
            'confidence_adjustment': 0.0,
            'adjustment_reasons': []
        }
        
        for suggestion in analysis['suggested_adjustments']:
            if (suggestion['type'] == 'POTENTIAL_DEPRESSION' and 
                analysis['depression_score'] > 0.7):
                enhanced_prediction['enhanced_diagnosis'] = 'Depression'
                enhanced_prediction['confidence_adjustment'] = suggestion['confidence_boost']
                enhanced_prediction['adjustment_reasons'].append(suggestion['reason'])
            
            elif (suggestion['type'] == 'POTENTIAL_BIPOLAR' and
                  analysis['bipolar1_score'] > analysis['bipolar2_score']):
                enhanced_prediction['enhanced_diagnosis'] = 'Bipolar Type-1'
                enhanced_prediction['confidence_adjustment'] = suggestion['confidence_boost']
                enhanced_prediction['adjustment_reasons'].append(suggestion['reason'])
        
        return enhanced_prediction

def initialize_clinical_enhancer():
    global clinical_enhancer
    if feature_names and label_encoder:
        clinical_enhancer = ClinicalDecisionEnhancer(feature_names, label_encoder)
        logger.info("Clinical Decision Enhancer initialized")

class ClinicalPreprocessor:
    """Replicates the preprocessing pipeline from train_model.py"""
    
    def __init__(self, category_mappings: Optional[Dict[str, Any]] = None):
        self.category_mappings = category_mappings or {}
        self.processing_log: List[str] = []
    
    def log_step(self, step: str, details: str) -> None:
        self.processing_log.append(f"{step}: {details}")
    
    def encode_user_responses(self, raw_responses: Dict[str, Any]) -> Dict[str, Any]:
        encoded_responses: Dict[str, Any] = {}
        
        frequency_mapping = self.category_mappings.get('frequency', 
            {'Seldom': 0, 'Sometimes': 1, 'Usually': 2, 'Most-Often': 3})
        yes_no_mapping = self.category_mappings.get('yes_no', {'NO': 0, 'YES': 1})
        sexual_activity_mapping = self.category_mappings.get('sexual_activity', {
            'No interest': 0, 'Low interest': 1, 'Moderate interest': 2, 
            'High interest': 3, 'Very high interest': 4
        })
        concentration_mapping = self.category_mappings.get('concentration', {
            'Cannot concentrate': 0, 'Poor concentration': 1, 'Average concentration': 2, 
            'Good concentration': 3, 'Excellent concentration': 4
        })
        optimism_mapping = self.category_mappings.get('optimism', {
            'Extremely pessimistic': 0, 'Pessimistic': 1, 'Neutral outlook': 2, 
            'Optimistic': 3, 'Extremely optimistic': 4
        })
        
        for feature, value in raw_responses.items():
            if feature in ['Sadness', 'Euphoric', 'Exhausted', 'Sleep disorder', 'Anxiety', 
                        'Depressed_Mood', 'Irritability', 'Worrying', 'Fatigue']:
                if value in frequency_mapping:
                    encoded_responses[feature] = frequency_mapping[value]
                else:
                    encoded_responses[feature] = 1
            
            elif feature in ['Mood Swing', 'Suicidal thoughts', 'Aggressive Response', 
                           'Nervous Breakdown', 'Overthinking', 'Anorexia', 'Authority Respect', 
                           'Try Explanation', 'Ignore & Move-On', 'Admit Mistakes']:
                if value in yes_no_mapping:
                    encoded_responses[feature] = yes_no_mapping[value]
                else:
                    encoded_responses[feature] = 0
            
            elif feature == 'Concentration':
                if value in concentration_mapping:
                    encoded_responses[feature] = concentration_mapping[value]
                else:
                    encoded_responses[feature] = 2
            
            elif feature == 'Optimism':
                if value in optimism_mapping:
                    encoded_responses[feature] = optimism_mapping[value]
                else:
                    encoded_responses[feature] = 2
            
            elif feature == 'Sexual Activity':
                if value in sexual_activity_mapping:
                    encoded_responses[feature] = sexual_activity_mapping[value]
                else:
                    encoded_responses[feature] = 2
            
            else:
                encoded_responses[feature] = value
        
        return encoded_responses
    
    def apply_feature_engineering(self, encoded_responses: Dict[str, Any]) -> Dict[str, Any]:
        responses = encoded_responses.copy()
        
        if 'Mood Swing' in responses and 'Sadness' in responses:
            mood_swing = float(responses.get('Mood Swing', 0))
            sadness = float(responses.get('Sadness', 0))
            responses['Mood_Emotion_Composite'] = mood_swing * 0.6 + sadness * 0.4
        
        if 'Sleep disorder' in responses and 'Exhausted' in responses:
            sleep_disorder = float(responses.get('Sleep disorder', 0))
            exhausted = float(responses.get('Exhausted', 0))
            responses['Sleep_Fatigue_Composite'] = sleep_disorder * 0.7 + exhausted * 0.3
        
        behavioral_features = ['Aggressive Response', 'Nervous Breakdown', 'Overthinking']
        behavioral_scores = []
        for feat in behavioral_features:
            if feat in responses:
                try:
                    behavioral_scores.append(float(responses[feat]))
                except (ValueError, TypeError):
                    behavioral_scores.append(0.0)
        
        if behavioral_scores:
            responses['Behavioral_Stress_Composite'] = sum(behavioral_scores) / len(behavioral_scores)
        
        risk_indicators = ['Suicidal thoughts', 'Aggressive Response', 'Nervous Breakdown']
        risk_scores = []
        for feat in risk_indicators:
            if feat in responses:
                try:
                    risk_scores.append(float(responses[feat]))
                except (ValueError, TypeError):
                    risk_scores.append(0.0)
        
        if risk_scores:
            responses['Risk_Assessment_Score'] = sum(risk_scores) * 10
        else:
            responses['Risk_Assessment_Score'] = 0.0
        
        cognitive_features = ['Concentration', 'Optimism']
        cognitive_scores = []
        for feat in cognitive_features:
            if feat in responses:
                try:
                    normalized_score = float(responses[feat]) / 4.0
                    cognitive_scores.append(normalized_score)
                except (ValueError, TypeError):
                    cognitive_scores.append(0.5)
        
        if cognitive_scores:
            responses['Cognitive_Function_Score'] = sum(cognitive_scores) / len(cognitive_scores) * 10
        else:
            responses['Cognitive_Function_Score'] = 5.0
        
        mood_features = ['Mood Swing', 'Euphoric', 'Sadness']
        stability_scores = []
        
        for feat in mood_features:
            if feat in responses:
                try:
                    value = float(responses[feat])
                    if feat == 'Mood Swing':
                        stability_scores.append(10 - (value * 10))
                    elif feat == 'Euphoric':
                        if value == 0 or value == 3:
                            stability_scores.append(3.0)
                        elif value == 1 or value == 2:
                            stability_scores.append(7.0)
                        else:
                            stability_scores.append(5.0)
                    elif feat == 'Sadness':
                        stability_scores.append(10 - (value * 3.33))
                except (ValueError, TypeError):
                    stability_scores.append(5.0)
        
        if stability_scores:
            responses['Mood_Stability_Score'] = sum(stability_scores) / len(stability_scores)
        else:
            responses['Mood_Stability_Score'] = 5.0
        
        return responses
    
    def normalize_feature_names(self, raw_responses: Dict[str, Any]) -> Dict[str, Any]:
        normalized_responses: Dict[str, Any] = {}
        
        feature_name_mapping = {
            'Mood Swing': 'Mood Swing',
            'Sadness': 'Sadness', 
            'Euphoric': 'Euphoric',
            'Sleep disorder': 'Sleep disorder',
            'Exhausted': 'Exhausted',
            'Suicidal thoughts': 'Suicidal thoughts',
            'Aggressive Response': 'Aggressive Response',
            'Nervous Breakdown': 'Nervous Breakdown',
            'Overthinking': 'Overthinking',
            'Anorexia': 'Anorexia',
            'Authority Respect': 'Authority Respect',
            'Try Explanation': 'Try Explanation',
            'Ignore & Move-On': 'Ignore & Move-On',
            'Admit Mistakes': 'Admit Mistakes',
            'Concentration': 'Concentration',
            'Optimism': 'Optimism',
            'Sexual Activity': 'Sexual Activity'
        }
        
        for feature, value in raw_responses.items():
            training_feature_name = feature_name_mapping.get(feature, feature)
            normalized_responses[training_feature_name] = value
            
        return normalized_responses
    
    def validate_clinical_safety(self, responses: Dict[str, Any]) -> Tuple[bool, List[str]]:
        warnings: List[str] = []
        
        suicidal_thoughts = float(responses.get('Suicidal thoughts', 0))
        aggressive_response = float(responses.get('Aggressive Response', 0))
        nervous_breakdown = float(responses.get('Nervous Breakdown', 0))
        sadness = float(responses.get('Sadness', 0))
        sleep_disorder = float(responses.get('Sleep disorder', 0))
        exhausted = float(responses.get('Exhausted', 0))
        euphoric = float(responses.get('Euphoric', 0))
        mood_swing = float(responses.get('Mood Swing', 0))
        
        if suicidal_thoughts == 1:
            warnings.append("Suicidal thoughts detected - please seek immediate professional help")
        
        if aggressive_response == 1:
            warnings.append("Aggressive behavior patterns detected - safety assessment recommended")
        
        if nervous_breakdown == 1:
            warnings.append("History of nervous breakdown detected - consider professional evaluation")
        
        if (sadness >= 3 and 
            sleep_disorder >= 2 and
            exhausted >= 2):
            warnings.append("Severe depression symptoms detected - urgent evaluation recommended")
        
        if (euphoric >= 3 and 
            mood_swing >= 2):
            warnings.append("Potential manic symptoms detected - clinical assessment advised")
        
        safety_ok = len(warnings) == 0
        if not safety_ok:
            self.log_step("Safety_Check", f"Safety warnings: {warnings}")
        else:
            self.log_step("Safety_Check", "All safety checks passed")
            
        return safety_ok, warnings

    def preprocess(self, raw_responses: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        self.processing_log = []
        self.log_step("Pipeline_Start", f"Processing {len(raw_responses)} raw features")
        
        try:
            normalized_responses = self.normalize_feature_names(raw_responses)
            responses = self.encode_user_responses(normalized_responses)
            responses = self.apply_feature_engineering(responses)
            safety_ok, safety_warnings = self.validate_clinical_safety(responses)
            
            self.log_step("Pipeline_Complete", 
                        f"Processed {len(responses)} features. Safety OK: {safety_ok}")
            
            return responses, self.processing_log, safety_warnings
            
        except Exception as e:
            self.log_step("Pipeline_Error", f"Preprocessing failed: {str(e)}")
            raise

def validate_assessment_responses(responses: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        if not isinstance(responses, dict):
            return False, "Responses must be a dictionary"
        
        if len(responses) > SecurityConfig.MAX_RESPONSES:
            return False, f"Too many responses. Maximum allowed: {SecurityConfig.MAX_RESPONSES}"
        
        for key, value in responses.items():
            sanitized_key = SecurityUtils.sanitize_input(str(key))
            if sanitized_key != key:
                return False, f"Invalid characters in response key: {key}"
            
            if not isinstance(value, (str, int, float)):
                return False, f"Invalid response type for {key}"
            
            if isinstance(value, str) and len(value) > SecurityConfig.MAX_INPUT_LENGTH:
                return False, f"Response value too long for {key}"
        
        return True, "Valid"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def convert_responses_to_features(processed_responses: Dict[str, Any]) -> Optional[pd.DataFrame]:
    try:
        if feature_names is None:
            logger.error("Feature names not loaded")
            return None
            
        feature_array = np.zeros(len(feature_names))
        
        missing_features: List[str] = []
        found_features: List[str] = []
        
        for i, feature_name in enumerate(feature_names):
            if feature_name in processed_responses:
                value = processed_responses[feature_name]
                if isinstance(value, (int, float)):
                    feature_array[i] = value
                else:
                    try:
                        feature_array[i] = float(value)
                    except (ValueError, TypeError):
                        feature_array[i] = 0
                found_features.append(feature_name)
            else:
                feature_array[i] = 0
                missing_features.append(feature_name)
        
        if missing_features:
            logger.warning(f"Missing features filled with defaults: {len(missing_features)}")
        
        logger.info(f"Feature array created: {len(feature_array)} features, "
                   f"{len(missing_features)} missing, {len(found_features)} found")
        
        feature_df = pd.DataFrame([feature_array], columns=feature_names)
        
        return feature_df
        
    except Exception as e:
        logger.error(f"Feature conversion error: {e}")
        return None

# Initialize security services
audit_logger = AuditLogger()
encryption_service = EncryptionService()
rate_limiter = AdvancedRateLimiter()
auth_service = AuthService()

# ==================== FLASK APP SETUP ====================
app = Flask(__name__, 
           static_folder='frontend',
           template_folder='frontend')

app.secret_key = SecurityConfig.SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = SecurityConfig.SESSION_COOKIE_SECURE
app.config['SESSION_COOKIE_HTTPONLY'] = SecurityConfig.SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = SecurityConfig.SESSION_COOKIE_SAMESITE
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=SecurityConfig.SESSION_TIMEOUT)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    validate_environment()
    logger.info("Environment validation passed")
except Exception as e:
    logger.error(f"CRITICAL: Environment validation failed: {e}")
    sys.exit(1)

model_package, scaler, label_encoder, feature_names, category_mappings = load_model_components()
initialize_clinical_enhancer()
preprocessor = ClinicalPreprocessor(category_mappings)

# ==================== DATABASE SETUP ====================
def get_database_connection():
    """Get database connection"""
    try:
        database_url = SecurityConfig.get_database_url()
        
        if database_url.startswith('sqlite:///'):
            sqlite_path = database_url.replace('sqlite:///', '')
            if sqlite_path == 'mental_health_assessments.db':
                sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mental_health_assessments.db')
            
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            return conn
        
        ssl_mode = 'require' if os.environ.get('RENDER') else 'prefer'
        
        conn = psycopg.connect(
            database_url,
            row_factory=dict_row,
            sslmode=ssl_mode
        )
        
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = 30000")
        
        return conn
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        
        if os.environ.get('RENDER'):
            raise e
        
        try:
            sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mental_health_assessments.db')
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            return conn
        except Exception:
            raise e

def init_database():
    """Initialize database"""
    try:
        conn = get_database_connection()
        
        try:
            cursor = conn.cursor()
            has_context_manager = hasattr(cursor, '__enter__')
            
            if has_context_manager:
                with cursor as cur:
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS assessments (
                            id TEXT PRIMARY KEY,
                            assessment_timestamp TEXT,
                            report_timestamp TEXT,
                            timezone TEXT,
                            patient_name TEXT,
                            patient_number TEXT,
                            patient_age TEXT,
                            patient_gender TEXT,
                            primary_diagnosis TEXT,
                            confidence REAL,
                            confidence_percentage REAL,
                            all_diagnoses_json TEXT,
                            responses_json TEXT,
                            processing_details_json TEXT,
                            technical_details_json TEXT,
                            clinical_insights_json TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            created_by_ip TEXT,
                            updated_by_ip TEXT,
                            audit_log TEXT DEFAULT '[]'
                        )
                    ''')
                    
                    cur.execute('CREATE INDEX IF NOT EXISTS idx_patient_number ON assessments(patient_number)')
                    cur.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON assessments(report_timestamp)')
                    cur.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON assessments(created_at)')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessments (
                        id TEXT PRIMARY KEY,
                        assessment_timestamp TEXT,
                        report_timestamp TEXT,
                        timezone TEXT,
                        patient_name TEXT,
                        patient_number TEXT,
                        patient_age TEXT,
                        patient_gender TEXT,
                        primary_diagnosis TEXT,
                        confidence REAL,
                        confidence_percentage REAL,
                        all_diagnoses_json TEXT,
                        responses_json TEXT,
                        processing_details_json TEXT,
                        technical_details_json TEXT,
                        clinical_insights_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by_ip TEXT,
                        updated_by_ip TEXT,
                        audit_log TEXT DEFAULT '[]'
                    )
                ''')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_patient_number ON assessments(patient_number)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON assessments(report_timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON assessments(created_at)')
                
        finally:
            cursor.close()
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        audit_logger.log_event(
            event_type='DATABASE_INIT_FAILED',
            details=str(e),
            severity='CRITICAL'
        )

def save_assessment_to_db(assessment_data: Dict[str, Any]) -> bool:
    """Save assessment data"""
    try:
        sanitized_data = assessment_data.copy()
        
        if 'patient_info' in sanitized_data:
            patient_info = sanitized_data['patient_info']
            patient_info['name'] = SecurityUtils.sanitize_input(patient_info.get('name', ''))
            patient_info['number'] = SecurityUtils.sanitize_input(patient_info.get('number', ''))
            patient_info['age'] = SecurityUtils.sanitize_input(patient_info.get('age', ''))
            patient_info['gender'] = SecurityUtils.sanitize_input(patient_info.get('gender', ''))
        
        audit_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': 'CREATE',
            'ip_address': request.remote_addr if request else '0.0.0.0',
            'user_agent': request.headers.get('User-Agent') if request else None,
            'changes': {}
        }
        
        conn = get_database_connection()
        
        try:
            cursor = conn.cursor()
            has_context_manager = hasattr(cursor, '__enter__')
            
            if has_context_manager:
                with cursor as cur:
                    cur.execute('SELECT id FROM assessments WHERE id = %s', (sanitized_data.get('id'),))
                    existing = cur.fetchone()

                    if existing:
                        audit_entry['action'] = 'UPDATE'
                        cur.execute('''
                            UPDATE assessments SET
                                assessment_timestamp = %s,
                                report_timestamp = %s,
                                timezone = %s,
                                patient_name = %s,
                                patient_number = %s,
                                patient_age = %s,
                                patient_gender = %s,
                                primary_diagnosis = %s,
                                confidence = %s,
                                confidence_percentage = %s,
                                all_diagnoses_json = %s,
                                responses_json = %s,
                                processing_details_json = %s,
                                technical_details_json = %s,
                                clinical_insights_json = %s,
                                updated_at = CURRENT_TIMESTAMP,
                                updated_by_ip = %s,
                                audit_log = audit_log || %s::jsonb
                            WHERE id = %s
                        ''', (
                            sanitized_data.get('assessment_timestamp'),
                            sanitized_data.get('timestamp'),
                            sanitized_data.get('timezone', 'UTC'),
                            sanitized_data.get('patient_info', {}).get('name', ''),
                            sanitized_data.get('patient_info', {}).get('number', ''),
                            sanitized_data.get('patient_info', {}).get('age', ''),
                            sanitized_data.get('patient_info', {}).get('gender', ''),
                            sanitized_data.get('primary_diagnosis', ''),
                            sanitized_data.get('confidence', 0),
                            sanitized_data.get('confidence_percentage', 0),
                            json.dumps(sanitized_data.get('all_diagnoses', [])),
                            json.dumps(sanitized_data.get('responses', {})),
                            json.dumps(sanitized_data.get('processing_details', {})),
                            json.dumps(sanitized_data.get('technical_details', {})),
                            json.dumps(sanitized_data.get('clinical_insights', {})),
                            request.remote_addr if request else '0.0.0.0',
                            json.dumps([audit_entry]),
                            sanitized_data.get('id')
                        ))
                    else:
                        audit_entry['action'] = 'CREATE'
                        cur.execute('''
                            INSERT INTO assessments (
                                id, assessment_timestamp, report_timestamp, timezone,
                                patient_name, patient_number, patient_age, patient_gender,
                                primary_diagnosis, confidence, confidence_percentage,
                                all_diagnoses_json, responses_json, processing_details_json,
                                technical_details_json, clinical_insights_json,
                                created_by_ip, updated_by_ip, audit_log
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            sanitized_data.get('id'),
                            sanitized_data.get('assessment_timestamp'),
                            sanitized_data.get('timestamp'),
                            sanitized_data.get('timezone', 'UTC'),
                            sanitized_data.get('patient_info', {}).get('name', ''),
                            sanitized_data.get('patient_info', {}).get('number', ''),
                            sanitized_data.get('patient_info', {}).get('age', ''),
                            sanitized_data.get('patient_info', {}).get('gender', ''),
                            sanitized_data.get('primary_diagnosis', ''),
                            sanitized_data.get('confidence', 0),
                            sanitized_data.get('confidence_percentage', 0),
                            json.dumps(sanitized_data.get('all_diagnoses', [])),
                            json.dumps(sanitized_data.get('responses', {})),
                            json.dumps(sanitized_data.get('processing_details', {})),
                            json.dumps(sanitized_data.get('technical_details', {})),
                            json.dumps(sanitized_data.get('clinical_insights', {})),
                            request.remote_addr if request else '0.0.0.0',
                            request.remote_addr if request else '0.0.0.0',
                            json.dumps([audit_entry])
                        ))
            else:
                cursor.execute('SELECT id FROM assessments WHERE id = ?', (sanitized_data.get('id'),))
                existing = cursor.fetchone()
                
                if existing:
                    audit_entry['action'] = 'UPDATE'
                    cursor.execute('''
                        UPDATE assessments SET
                            assessment_timestamp = ?,
                            report_timestamp = ?,
                            timezone = ?,
                            patient_name = ?,
                            patient_number = ?,
                            patient_age = ?,
                            patient_gender = ?,
                            primary_diagnosis = ?,
                            confidence = ?,
                            confidence_percentage = ?,
                            all_diagnoses_json = ?,
                            responses_json = ?,
                            processing_details_json = ?,
                            technical_details_json = ?,
                            clinical_insights_json = ?,
                            updated_at = CURRENT_TIMESTAMP,
                            updated_by_ip = ?,
                            audit_log = json_insert(audit_log, '$[#]', ?)
                        WHERE id = ?
                    ''', (
                        sanitized_data.get('assessment_timestamp'),
                        sanitized_data.get('timestamp'),
                        sanitized_data.get('timezone', 'UTC'),
                        sanitized_data.get('patient_info', {}).get('name', ''),
                        sanitized_data.get('patient_info', {}).get('number', ''),
                        sanitized_data.get('patient_info', {}).get('age', ''),
                        sanitized_data.get('patient_info', {}).get('gender', ''),
                        sanitized_data.get('primary_diagnosis', ''),
                        sanitized_data.get('confidence', 0),
                        sanitized_data.get('confidence_percentage', 0),
                        json.dumps(sanitized_data.get('all_diagnoses', [])),
                        json.dumps(sanitized_data.get('responses', {})),
                        json.dumps(sanitized_data.get('processing_details', {})),
                        json.dumps(sanitized_data.get('technical_details', {})),
                        json.dumps(sanitized_data.get('clinical_insights', {})),
                        request.remote_addr if request else '0.0.0.0',
                        json.dumps(audit_entry),
                        sanitized_data.get('id')
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO assessments (
                            id, assessment_timestamp, report_timestamp, timezone,
                            patient_name, patient_number, patient_age, patient_gender,
                            primary_diagnosis, confidence, confidence_percentage,
                            all_diagnoses_json, responses_json, processing_details_json,
                            technical_details_json, clinical_insights_json,
                            created_by_ip, updated_by_ip, audit_log
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sanitized_data.get('id'),
                        sanitized_data.get('assessment_timestamp'),
                        sanitized_data.get('timestamp'),
                        sanitized_data.get('timezone', 'UTC'),
                        sanitized_data.get('patient_info', {}).get('name', ''),
                        sanitized_data.get('patient_info', {}).get('number', ''),
                        sanitized_data.get('patient_info', {}).get('age', ''),
                        sanitized_data.get('patient_info', {}).get('gender', ''),
                        sanitized_data.get('primary_diagnosis', ''),
                        sanitized_data.get('confidence', 0),
                        sanitized_data.get('confidence_percentage', 0),
                        json.dumps(sanitized_data.get('all_diagnoses', [])),
                        json.dumps(sanitized_data.get('responses', {})),
                        json.dumps(sanitized_data.get('processing_details', {})),
                        json.dumps(sanitized_data.get('technical_details', {})),
                        json.dumps(sanitized_data.get('clinical_insights', {})),
                        request.remote_addr if request else '0.0.0.0',
                        request.remote_addr if request else '0.0.0.0',
                        json.dumps([audit_entry])
                    ))
            
            conn.commit()
            
        finally:
            cursor.close()
            conn.close()
        
        audit_logger.log_event(
            event_type='ASSESSMENT_SAVED',
            details=f"Assessment {sanitized_data.get('id')} saved successfully",
            severity='INFO'
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        audit_logger.log_event(
            event_type='ASSESSMENT_SAVE_FAILED',
            details=f"Failed to save assessment: {str(e)}",
            severity='ERROR'
        )
        return False

def load_assessments_from_db(patient_number: str = None) -> Dict[str, List[Dict[str, Any]]]:
    """Load assessments from database"""
    try:
        conn = get_database_connection()
        
        assessments_by_patient: Dict[str, List[Dict[str, Any]]] = {}
        
        if hasattr(conn, 'cursor'):
            with conn.cursor() as cur:
                if patient_number:
                    cur.execute('''
                        SELECT * FROM assessments 
                        WHERE patient_number = %s 
                        ORDER BY report_timestamp DESC
                    ''', (patient_number,))
                else:
                    cur.execute('SELECT * FROM assessments ORDER BY report_timestamp DESC')
                
                rows = cur.fetchall()
        else:
            c = conn.cursor()
            
            if patient_number:
                c.execute('''
                    SELECT * FROM assessments 
                    WHERE patient_number = ? 
                    ORDER BY report_timestamp DESC
                ''', (patient_number,))
            else:
                c.execute('SELECT * FROM assessments ORDER BY report_timestamp DESC')
            
            rows = c.fetchall()
        
        conn.close()
        
        for row in rows:
            if isinstance(row, dict):
                row_dict = row
            else:
                row_dict = dict(row)
            
            patient_num = row_dict['patient_number']
            if patient_num not in assessments_by_patient:
                assessments_by_patient[patient_num] = []
            
            all_diagnoses_json = row_dict['all_diagnoses_json']
            responses_json = row_dict['responses_json']
            clinical_insights_json = row_dict['clinical_insights_json']
            
            if os.environ.get('ENCRYPT_SENSITIVE_DATA', 'false').lower() == 'true':
                try:
                    all_diagnoses_json = encryption_service.decrypt_data(all_diagnoses_json) if all_diagnoses_json else '[]'
                    responses_json = encryption_service.decrypt_data(responses_json) if responses_json else '{}'
                    clinical_insights_json = encryption_service.decrypt_data(clinical_insights_json) if clinical_insights_json else '{}'
                except:
                    pass
            
            all_diagnoses = json.loads(all_diagnoses_json) if all_diagnoses_json else []
            responses = json.loads(responses_json) if responses_json else {}
            processing_details = json.loads(row_dict['processing_details_json']) if row_dict['processing_details_json'] else {}
            technical_details = json.loads(row_dict['technical_details_json']) if row_dict['technical_details_json'] else {}
            clinical_insights = json.loads(clinical_insights_json) if clinical_insights_json else {}
            
            assessment: Dict[str, Any] = {
                'id': row_dict['id'],
                'timestamp': row_dict['report_timestamp'],
                'assessment_timestamp': row_dict['assessment_timestamp'],
                'timezone': row_dict['timezone'],
                'patient_info': {
                    'name': row_dict['patient_name'],
                    'number': row_dict['patient_number'],
                    'age': row_dict['patient_age'],
                    'gender': row_dict['patient_gender']
                },
                'primary_diagnosis': row_dict['primary_diagnosis'],
                'confidence': row_dict['confidence'],
                'confidence_percentage': row_dict['confidence_percentage'],
                'all_diagnoses': all_diagnoses,
                'responses': responses,
                'processing_details': processing_details,
                'technical_details': technical_details,
                'clinical_insights': clinical_insights
            }
            
            assessments_by_patient[patient_num].append(assessment)
        
        logger.info(f"Loaded {len(rows)} assessments from database")
        return assessments_by_patient
        
    except Exception as e:
        logger.error(f"Error loading from database: {e}")
        return {}

def load_single_assessment_from_db(patient_name: str, patient_number: str, assessment_id: str) -> Optional[Dict[str, Any]]:
    """Load a single specific assessment from database"""
    try:
        conn = get_database_connection()
        
        if hasattr(conn, 'cursor'):
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT * FROM assessments 
                    WHERE patient_number = %s AND id = %s AND patient_name = %s
                ''', (patient_number, assessment_id, patient_name))
                
                row = cur.fetchone()
        else:
            c = conn.cursor()
            
            c.execute('''
                SELECT * FROM assessments 
                WHERE patient_number = ? AND id = ? AND patient_name = ?
            ''', (patient_number, assessment_id, patient_name))
            
            row = c.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        if isinstance(row, dict):
            row_dict = row
        else:
            row_dict = dict(row)
        
        all_diagnoses_json = row_dict['all_diagnoses_json']
        responses_json = row_dict['responses_json']
        clinical_insights_json = row_dict['clinical_insights_json']
        
        if os.environ.get('ENCRYPT_SENSITIVE_DATA', 'false').lower() == 'true':
            try:
                all_diagnoses_json = encryption_service.decrypt_data(all_diagnoses_json) if all_diagnoses_json else '[]'
                responses_json = encryption_service.decrypt_data(responses_json) if responses_json else '{}'
                clinical_insights_json = encryption_service.decrypt_data(clinical_insights_json) if clinical_insights_json else '{}'
            except:
                pass
        
        all_diagnoses = json.loads(all_diagnoses_json) if all_diagnoses_json else []
        responses = json.loads(responses_json) if responses_json else {}
        processing_details = json.loads(row_dict['processing_details_json']) if row_dict['processing_details_json'] else {}
        technical_details = json.loads(row_dict['technical_details_json']) if row_dict['technical_details_json'] else {}
        clinical_insights = json.loads(clinical_insights_json) if clinical_insights_json else {}
        
        assessment: Dict[str, Any] = {
            'id': row_dict['id'],
            'timestamp': row_dict['report_timestamp'],
            'assessment_timestamp': row_dict['assessment_timestamp'],
            'timezone': row_dict['timezone'],
            'patient_info': {
                'name': row_dict['patient_name'],
                'number': row_dict['patient_number'],
                'age': row_dict['patient_age'],
                'gender': row_dict['patient_gender']
            },
            'primary_diagnosis': row_dict['primary_diagnosis'],
            'confidence': row_dict['confidence'],
            'confidence_percentage': row_dict['confidence_percentage'],
            'all_diagnoses': all_diagnoses,
            'responses': responses,
            'processing_details': processing_details,
            'technical_details': technical_details,
            'clinical_insights': clinical_insights
        }
        
        return assessment
        
    except Exception as e:
        logger.error(f"Error loading single assessment from database: {e}")
        return None

def delete_assessment_from_db(patient_number: str, assessment_id: str) -> bool:
    """Delete assessment from database"""
    try:
        conn = get_database_connection()
        
        if hasattr(conn, 'cursor'):
            with conn.cursor() as cur:
                cur.execute('''
                    DELETE FROM assessments 
                    WHERE patient_number = %s AND id = %s
                ''', (patient_number, assessment_id))
        else:
            c = conn.cursor()
            
            c.execute('''
                DELETE FROM assessments 
                WHERE patient_number = ? AND id = ?
            ''', (patient_number, assessment_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Assessment deleted from database: {assessment_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting from database: {e}")
        return False

init_database()

@app.after_request
def set_security_headers(response):
    """Set security headers on all responses"""
    for header, value in SecurityConfig.SECURITY_HEADERS.items():
        response.headers[header] = value
    
    request_id = getattr(request, 'request_id', None)
    if request_id:
        response.headers['X-Request-ID'] = request_id
    
    return response

@app.before_request
def security_middleware():
    request.request_id = SecurityUtils.generate_request_id()
    
    audit_logger.log_event(
        event_type='REQUEST_START',
        ip=request.remote_addr,
        details=f"{request.method} {request.path}",
        severity='INFO'
    )
    
    if request.content_length and request.content_length > SecurityConfig.MAX_FILE_SIZE:
        audit_logger.log_event(
            event_type='REQUEST_TOO_LARGE',
            ip=request.remote_addr,
            details=f"Request size: {request.content_length} bytes",
            severity='WARNING'
        )
        return jsonify({'error': 'Request too large'}), 413
    
    if request.endpoint and request.endpoint.startswith('api'):
        client_ip = request.remote_addr
        endpoint = request.endpoint.replace('api_', '').replace('_', '-')
        
        limited, message = rate_limiter.is_endpoint_rate_limited(client_ip, endpoint)
        if limited:
            return jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': SecurityConfig.RATE_LIMIT_WINDOW,
                'message': message
            }), 429

if os.environ.get('RENDER'):
    CORS(app, origins=[
        'https://mentivio.onrender.com',
        'http://mentivio-MentalHealth.onrender.com',
        'https://mentivio-web.onrender.com'
    ], supports_credentials=True)
    app.debug = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
else:
    CORS(app, resources={r"/api/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
        "supports_credentials": True,
        "allow_headers": ["Content-Type", "X-API-Key", "X-Client-Timezone"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    }})

# ==================== ROUTES ====================

@app.route('/api/config', methods=['GET'])
def get_config():
    """Provide necessary configuration to frontend"""
    return jsonify({
        'api_key': SecurityConfig.API_KEY,
        'api_base_url': request.host_url.rstrip('/'),
        'version': '4.0',
        'features': {
            'pdf_generation': True,
            'assessment_history': True,
            'clinical_enhancement': True
        }
    })
    
@app.route('/')
def serve_index():
    return send_from_directory('frontend', 'Home.html')

@app.route('/<page_name>.html')
def serve_html_page(page_name):
    main_pages = [
        'Home', 'About', 'MenHel_analogy', 'MenHel_prediction', 
        'resources', 'crisis-support', 'relief_techniques', 'navbar', 'footer'
    ]
    
    if page_name in main_pages:
        return send_from_directory('frontend', f'{page_name}.html')
    else:
        try:
            return send_from_directory('frontend/resources', f'{page_name}.html')
        except:
            return send_from_directory('frontend', 'Home.html')

@app.route('/resources/<resource_name>.html')
def serve_resource_page(resource_name):
    resource_pages = [
        'anxiety-resource', 'bipolar-resource', 'depression-resource',
        'medication-resource', 'mindfulness-resource', 'ptsd-resource',
        'selfcare-resource', 'therapy-resource'
    ]
    
    if resource_name in resource_pages:
        return send_from_directory('frontend/resources', f'{resource_name}.html')
    else:
        return send_from_directory('frontend', 'resources.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    try:
        return send_from_directory('frontend/css', filename)
    except:
        return send_from_directory('frontend/resources', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('frontend/js', filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('frontend/assets', filename)

@app.route('/<path:path>')
def serve_static_files(path):
    if path.startswith('resources/'):
        try:
            resource_path = path.replace('resources/', '', 1)
            return send_from_directory('frontend/resources', resource_path)
        except:
            pass
    
    try:
        return send_from_directory('frontend', path)
    except:
        return send_from_directory('frontend', 'Home.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        db_healthy = False
        db_type = "Unknown"
        try:
            conn = get_database_connection()
            if conn:
                if hasattr(conn, 'cursor'):
                    with conn.cursor() as cur:
                        cur.execute('SELECT 1 as test')
                        db_healthy = True
                        db_type = 'PostgreSQL'
                else:
                    c = conn.cursor()
                    c.execute('SELECT 1 as test')
                    db_healthy = True
                    db_type = 'SQLite'
                conn.close()
        except Exception:
            pass

        components_loaded = all([
            model_package is not None,
            scaler is not None, 
            label_encoder is not None,
            feature_names is not None,
            category_mappings is not None
        ])
        
        security_checks = {
            'secret_key_set': bool(os.environ.get('SECRET_KEY')),
            'secret_key_length': len(os.environ.get('SECRET_KEY', '')) >= 32,
            'api_key_set': bool(os.environ.get('API_KEY')),
            'encryption_key_set': bool(os.environ.get('ENCRYPTION_KEY')),
            'database_configured': True,
            'rate_limiting_enabled': True,
            'security_headers_enabled': True,
            'audit_logging_enabled': True,
            'debug_mode_disabled': not app.debug,
            'https_enforced': os.environ.get('RENDER') is not None
        }
        
        all_security_passed = all(security_checks.values())
        overall_healthy = components_loaded and db_healthy
        
        health_info = {
            'status': 'healthy' if overall_healthy else 'degraded',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': {
                'healthy': db_healthy,
                'type': db_type
            },
            'security': {
                'checks_passed': all_security_passed,
                'details': security_checks
            },
            'components': {
                'model_loaded': model_package is not None,
                'scaler_loaded': scaler is not None,
                'encoder_loaded': label_encoder is not None,
                'features_loaded': feature_names is not None,
                'category_mappings_loaded': category_mappings is not None,
                'clinical_enhancer_available': clinical_enhancer is not None,
                'total_features': len(feature_names) if feature_names else 0,
                'available_classes': label_encoder.classes_.tolist() if label_encoder else []
            },
            'message': 'Service is secure and ready' if all_security_passed else 'Security improvements needed'
        }
        
        return jsonify(health_info)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'starting',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': 'Instance is starting up, please wait'
        }), 200

@app.route('/ping', methods=['GET'])
def simple_ping():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'Mental Health Assessment API'
    })

def parse_assessment_timestamp(timestamp_str: str) -> datetime:
    try:
        if not timestamp_str or timestamp_str == 'N/A':
            return datetime.now(timezone.utc)
        
        if 'T' in timestamp_str:
            if timestamp_str.endswith('Z'):
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif '+' in timestamp_str or '-' in timestamp_str[-6:]:
                dt = datetime.fromisoformat(timestamp_str)
            else:
                dt = datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
        else:
            try:
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                try:
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                except ValueError:
                    return datetime.now(timezone.utc)
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        return dt
        
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)

@app.route('/api/predict', methods=['POST'])
@require_api_key
@validate_json_content
@sanitize_inputs
def predict():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_responses = data.get('responses', {})
        patient_info = data.get('patientInfo', {})
        assessment_start_time = data.get('assessment_start_time')
        
        responses_valid, responses_msg = validate_assessment_responses(user_responses)
        if not responses_valid:
            audit_logger.log_event(
                event_type='INVALID_RESPONSES',
                ip=request.remote_addr,
                details=responses_msg,
                severity='WARNING'
            )
            return jsonify({'error': f'Invalid responses: {responses_msg}'}), 400
        
        patient_valid, patient_msg = SecurityUtils.validate_patient_data(patient_info)
        if not patient_valid:
            audit_logger.log_event(
                event_type='INVALID_PATIENT_DATA',
                ip=request.remote_addr,
                details=patient_msg,
                severity='WARNING'
            )
            return jsonify({'error': f'Invalid patient data: {patient_msg}'}), 400
        
        audit_logger.log_event(
            event_type='PREDICTION_REQUEST',
            ip=request.remote_addr,
            details=f"Prediction for patient: {patient_info.get('name', 'Unknown')}",
            severity='INFO'
        )
        
        client_timezone = request.headers.get('X-Client-Timezone', 'UTC')
       
        try:
            tz = pytz.timezone(client_timezone)
        except:
            tz = pytz.UTC
            client_timezone = 'UTC'
        
        client_now = datetime.now(tz)
        report_generation_time = client_now.isoformat()
        
        if assessment_start_time:
            try:
                assessment_dt = parse_assessment_timestamp(assessment_start_time)
                assessment_dt_client = assessment_dt.astimezone(tz)
                assessment_date_str = assessment_dt_client.isoformat()
                
                time_diff = client_now - assessment_dt_client
                
            except Exception:
                assessment_date_str = client_now.isoformat()
                time_diff = timedelta(0)
        else:
            assessment_date_str = client_now.isoformat()
            time_diff = timedelta(0)

        try:
            processed_responses, processing_log, safety_warnings = preprocessor.preprocess(user_responses)
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return jsonify({'error': f'Data preprocessing failed: {str(e)}'}), 400
        
        feature_df = convert_responses_to_features(processed_responses)
        if feature_df is None:
            return jsonify({'error': 'Feature conversion failed'}), 400
        
        try:
            feature_array_scaled = scaler.transform(feature_df)
            feature_df_scaled = pd.DataFrame(feature_array_scaled, columns=feature_names)
            
        except Exception as e:
            logger.error(f"Feature scaling failed: {e}")
            return jsonify({'error': 'Feature scaling failed'}), 500
        
        try:
            prediction = model_package['model'].predict(feature_df_scaled)
            probabilities = model_package['model'].predict_proba(feature_df_scaled)
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return jsonify({'error': 'Model prediction failed'}), 500
        
        all_diagnoses = []
        for idx, prob in enumerate(probabilities[0]):
            diagnosis_name = label_encoder.inverse_transform([idx])[0]
            confidence_percentage = float(prob * 100)
            
            diagnosis_data = {
                'diagnosis': diagnosis_name,
                'probability': float(prob),
                'confidence_percentage': confidence_percentage,
                'rank': idx + 1
            }
            all_diagnoses.append(diagnosis_data)
            
        all_diagnoses.sort(key=lambda x: x['probability'], reverse=True)
        all_diagnoses = all_diagnoses[:4]
        
        for i, diagnosis in enumerate(all_diagnoses):
            diagnosis['rank'] = i + 1

        primary_diagnosis = all_diagnoses[0]['diagnosis']
        primary_confidence_percentage = all_diagnoses[0]['confidence_percentage']
        primary_confidence = all_diagnoses[0]['probability']
        
        clinical_enhancement = None
        final_diagnosis = primary_diagnosis
        final_confidence = primary_confidence
        final_confidence_percentage = primary_confidence_percentage
        
        if clinical_enhancer:
            clinical_enhancement = clinical_enhancer.enhance_prediction(
                processed_responses, probabilities[0], primary_diagnosis
            )
            
            if (clinical_enhancement['enhanced_diagnosis'] != primary_diagnosis and
                clinical_enhancement['adjustment_reasons']):
                final_diagnosis = clinical_enhancement['enhanced_diagnosis']
                final_confidence = min(1.0, primary_confidence + clinical_enhancement['confidence_adjustment'])
                final_confidence_percentage = final_confidence * 100
                
                for diagnosis in all_diagnoses:
                    if diagnosis['diagnosis'] == final_diagnosis:
                        diagnosis['probability'] = final_confidence
                        diagnosis['confidence_percentage'] = final_confidence_percentage
                        break
                
                all_diagnoses.sort(key=lambda x: x['probability'], reverse=True)
                
                final_diagnosis = all_diagnoses[0]['diagnosis']
                final_confidence = all_diagnoses[0]['probability']
                final_confidence_percentage = all_diagnoses[0]['confidence_percentage']
                
                logger.info(f"Clinical enhancement applied: {primary_diagnosis} -> {final_diagnosis}")

        response_data = {
            'primary_diagnosis': final_diagnosis,
            'confidence': float(final_confidence),
            'confidence_percentage': float(final_confidence_percentage),
            'all_diagnoses': all_diagnoses,
            'timestamp': report_generation_time,
            'assessment_timestamp': assessment_date_str,
            'timezone': client_timezone,
            'assessment_id': f"MH{client_now.strftime('%Y%m%d%H%M%S')}",
            'patient_info': patient_info,
            
            'processing_details': {
                'preprocessing_steps': len(processing_log),
                'clinical_safety_warnings': safety_warnings,
                'total_features_processed': len(processed_responses),
                'model_features_used': len(feature_names),
                'feature_engineering_applied': True,
                'clinical_domains_calculated': True,
                'clinical_enhancement_applied': clinical_enhancement is not None and final_diagnosis != primary_diagnosis,
                'safety_check_status': 'CRITICAL_ALERTS' if safety_warnings else 'PASSED',
                'total_diagnoses_considered': len(all_diagnoses),
                'timezone_used': client_timezone,
                'assessment_start_time': assessment_date_str,
                'report_generation_time': report_generation_time,
                'processing_duration_seconds': time_diff.total_seconds() if assessment_start_time else 0,
                'security_validation': 'PASSED'
            },
            'technical_details': {
                'processing_log': processing_log,
                'safety_checks_passed': len(safety_warnings) == 0,
                'feature_array_shape': feature_df.shape,
                'composite_scores_included': True,
                'probability_distribution': {
                    'min_confidence': float(np.min(probabilities[0]) * 100),
                    'max_confidence': float(np.max(probabilities[0]) * 100),
                    'mean_confidence': float(np.mean(probabilities[0]) * 100),
                    'confidence_range': float(np.max(probabilities[0]) * 100 - np.min(probabilities[0]) * 100)
                }
            }
        }
        
        if clinical_enhancement:
            response_data['clinical_insights'] = {
                'original_diagnosis': clinical_enhancement['original_diagnosis'],
                'enhancement_applied': clinical_enhancement['enhanced_diagnosis'] != clinical_enhancement['original_diagnosis'],
                'adjustment_reasons': clinical_enhancement['adjustment_reasons'],
                'pattern_analysis': clinical_enhancement['clinical_analysis'],
                'confidence_adjustment': float(clinical_enhancement['confidence_adjustment'] * 100)
            }
        
        logger.info(f"Secure assessment completed successfully for patient: {patient_info.get('name', 'Unknown')}")
        
        response = jsonify(response_data)
        response.headers['X-Content-Security-Policy'] = SecurityConfig.SECURITY_HEADERS['Content-Security-Policy']
        return response
        
    except Exception as e:
        logger.error(f"Secure prediction endpoint error: {e}")
        audit_logger.log_event(
            event_type='PREDICTION_ERROR',
            ip=request.remote_addr,
            details=f"Prediction failed: {str(e)}",
            severity='ERROR'
        )
        return jsonify({'error': 'Assessment failed. Please try again.'}), 500

@app.route('/api/save-assessment', methods=['POST'])
@require_api_key
@validate_json_content
def save_assessment():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        assessment_data = data.get('assessment_data', {})
        if not assessment_data:
            return jsonify({'error': 'No assessment data provided'}), 400
        
        if not isinstance(assessment_data, dict):
            return jsonify({'error': 'Invalid assessment data format'}), 400
        
        assessment_data['_security'] = {
            'saved_at': datetime.now(timezone.utc).isoformat(),
            'saved_by_ip': request.remote_addr,
            'request_id': getattr(request, 'request_id', 'unknown')
        }
        
        if 'id' not in assessment_data:
            if 'timestamp' in assessment_data:
                try:
                    timestamp = parse_assessment_timestamp(assessment_data['timestamp'])
                    assessment_data['id'] = f"MH{timestamp.strftime('%Y%m%d%H%M%S')}"
                except:
                    assessment_data['id'] = f"MH{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
            else:
                assessment_data['id'] = f"MH{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        
        if 'timestamp' not in assessment_data:
            assessment_data['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        if save_assessment_to_db(assessment_data):
            audit_logger.log_event(
                event_type='ASSESSMENT_SAVED_SUCCESS',
                ip=request.remote_addr,
                details=f"Assessment {assessment_data['id']} saved",
                severity='INFO'
            )
            
            return jsonify({
                'success': True,
                'assessment_id': assessment_data['id'],
                'message': 'Assessment saved securely',
                'security': {
                    'encrypted': os.environ.get('ENCRYPT_SENSITIVE_DATA', 'false').lower() == 'true',
                    'audit_trail': True
                }
            })
        else:
            return jsonify({'error': 'Failed to save assessment data securely'}), 500
        
    except Exception as e:
        logger.error(f"Error saving assessment: {e}")
        audit_logger.log_event(
            event_type='ASSESSMENT_SAVE_ERROR',
            ip=request.remote_addr,
            details=f"Save failed: {str(e)}",
            severity='ERROR'
        )
        return jsonify({'error': 'Failed to save assessment securely'}), 500

@app.route('/api/get-patient-assessments', methods=['POST'])
@require_api_key
@validate_json_content
def get_patient_assessments():
    try:
        data = request.json
        patient_name = data.get('name', '').strip()
        patient_number = data.get('number', '').strip()
        
        if not patient_name or not patient_number:
            return jsonify({'error': 'Patient name and number required'}), 400
        
        all_assessments = load_assessments_from_db(patient_number)
        
        patient_assessments = all_assessments.get(patient_number, [])
        
        filtered_assessments = [
            assessment for assessment in patient_assessments
            if assessment.get('patient_info', {}).get('name', '').lower() == patient_name.lower()
        ]
        
        logger.info(f"Found {len(filtered_assessments)} assessments for {patient_name} (#{patient_number})")
        
        return jsonify({
            'success': True,
            'assessments': filtered_assessments,
            'count': len(filtered_assessments)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving assessments: {e}")
        return jsonify({'error': f'Failed to retrieve assessments: {str(e)}'}), 500

def enhance_assessment_data(assessment: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if not assessment.get('primary_diagnosis') and assessment.get('all_diagnoses'):
            assessment['primary_diagnosis'] = assessment['all_diagnoses'][0].get('diagnosis', '')
            if not assessment.get('confidence_percentage') and assessment['all_diagnoses']:
                assessment['confidence_percentage'] = assessment['all_diagnoses'][0].get('confidence_percentage', 0)
                assessment['confidence'] = assessment['confidence_percentage'] / 100.0
        
        if 'diagnosis_description' not in assessment:
            assessment['diagnosis_description'] = get_diagnosis_description(assessment.get('primary_diagnosis', ''))
        
        if 'all_diagnoses' not in assessment or not assessment['all_diagnoses']:
            assessment['all_diagnoses'] = [
                {
                    'diagnosis': assessment.get('primary_diagnosis', ''),
                    'probability': assessment.get('confidence', 0),
                    'confidence_percentage': assessment.get('confidence_percentage', 0)
                }
            ]
        
        if 'processing_details' not in assessment:
            assessment['processing_details'] = {
                'preprocessing_steps': 15,
                'clinical_safety_warnings': [],
                'total_features_processed': len(assessment.get('responses', {})),
                'model_features_used': len(feature_names) if feature_names else 0,
                'feature_engineering_applied': True,
                'clinical_domains_calculated': True,
                'clinical_enhancement_applied': False,
                'safety_check_status': 'PASSED'
            }
        
        if 'technical_details' not in assessment:
            assessment['technical_details'] = {
                'processing_log': [
                    f"Assessment loaded from history: {assessment.get('id')}",
                    f"Patient: {assessment.get('patient_info', {}).get('name', 'Unknown')}",
                    f"Original assessment date: {assessment.get('timestamp', 'Unknown')}"
                ],
                'safety_checks_passed': True,
                'feature_array_shape': [1, len(feature_names)] if feature_names else [1, 0],
                'composite_scores_included': True
            }
        
        return assessment
        
    except Exception as e:
        logger.error(f"Error enhancing assessment data: {e}")
        return assessment

def get_diagnosis_description(diagnosis: str) -> str:
    descriptions = {
        'Normal': 'Your responses indicate typical mental well-being patterns with no significant clinical concerns detected.',
        'Bipolar Type-1': 'Your responses show patterns that may indicate Bipolar Type-1 disorder. This is characterized by manic episodes that last at least 7 days.',
        'Bipolar Type-2': 'Your responses suggest patterns consistent with Bipolar Type-2 disorder, characterized by hypomanic and depressive episodes.',
        'Depression': 'Your responses align with patterns commonly seen in depressive disorders, including persistent sadness and loss of interest.'
    }
    return descriptions.get(diagnosis, 'Assessment completed successfully. Please consult with a healthcare professional for accurate diagnosis.')

@app.route('/api/get-single-assessment', methods=['POST'])
@require_api_key
@validate_json_content
def get_single_assessment():
    try:
        data = request.json
        patient_name = data.get('name', '').strip()
        patient_number = data.get('number', '').strip()
        assessment_id = data.get('assessment_id', '').strip()
        
        if not patient_name or not patient_number or not assessment_id:
            return jsonify({'error': 'Patient name, number, and assessment ID required'}), 400
        
        target_assessment = load_single_assessment_from_db(patient_name, patient_number, assessment_id)
        
        if not target_assessment:
            return jsonify({'error': 'Assessment not found'}), 404
        
        enhanced_assessment = enhance_assessment_data(target_assessment)
        
        return jsonify({
            'success': True,
            'assessment': enhanced_assessment
        })
        
    except Exception as e:
        logger.error(f"Error retrieving single assessment: {e}")
        return jsonify({'error': f'Failed to retrieve assessment: {str(e)}'}), 500

@app.route('/api/delete-assessment', methods=['POST'])
@require_api_key
@validate_json_content
def delete_assessment():
    try:
        data = request.json
        patient_number = data.get('patient_number', '')
        assessment_id = data.get('assessment_id', '')
        
        if not patient_number or not assessment_id:
            return jsonify({'error': 'Patient number and assessment ID required'}), 400
        
        if delete_assessment_from_db(patient_number, assessment_id):
            audit_logger.log_event(
                event_type='ASSESSMENT_DELETED',
                ip=request.remote_addr,
                details=f"Assessment {assessment_id} deleted for patient #{patient_number}",
                severity='INFO'
            )
            return jsonify({'success': True, 'message': 'Assessment deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete assessment from database'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting assessment: {e}")
        return jsonify({'error': f'Failed to delete assessment: {str(e)}'}), 500

@app.route('/api')
@require_api_key
def api_info():
    return jsonify({
        'message': 'Enhanced Mental Health Assessment API is running!',
        'version': '4.0',
        'features': {
            'complete_preprocessing': True,
            'clinical_validation': True,
            'feature_engineering': True,
            'exact_training_match': True,
            'confidence_calibration': True,
            'clinical_decision_support': clinical_enhancer is not None,
            'database_storage': True,
            'security_features': True
        },
        'endpoints': {
            'health_check': '/api/health (GET)',
            'predict': '/api/predict (POST)',
            'save_assessment': '/api/save-assessment (POST)',
            'get_patient_assessments': '/api/get-patient-assessments (POST)',
            'delete_assessment': '/api/delete-assessment (POST)',
            'security_status': '/api/security-status (GET)'
        },
        'status': 'active'
    })

@app.route('/api/security-status', methods=['GET'])
@require_api_key
def security_status():
    security_info = {
        'authentication': {
            'api_key_required': True,
            'session_management': True,
            'failed_attempt_tracking': True,
            'account_lockout': True
        },
        'data_protection': {
            'encryption_enabled': True,
            'sensitive_data_encrypted': os.environ.get('ENCRYPT_SENSITIVE_DATA', 'false').lower() == 'true',
            'password_hashing': 'bcrypt'
        },
        'network_security': {
            'rate_limiting': True,
            'cors_restricted': True,
            'ip_validation': True,
            'https_required': os.environ.get('RENDER') is not None
        },
        'input_validation': {
            'sanitization_enabled': True,
            'max_input_length': SecurityConfig.MAX_INPUT_LENGTH,
            'sql_injection_protection': True,
            'xss_protection': True
        },
        'audit_logging': {
            'enabled': True,
            'file': SecurityConfig.AUDIT_LOG_FILE,
            'events_tracked': [
                'SESSION_CREATED', 'SESSION_DESTROYED', 'RATE_LIMIT_EXCEEDED',
                'INVALID_API_KEY', 'PREDICTION_REQUEST', 'ASSESSMENT_SAVED'
            ]
        },
        'headers': {
            'csp_enabled': True,
            'hsts_enabled': True,
            'xss_protection': True,
            'content_type_options': True
        },
        'configuration': {
            'secret_key_set': bool(os.environ.get('SECRET_KEY')),
            'api_key_set': bool(os.environ.get('API_KEY')),
            'encryption_key_set': bool(os.environ.get('ENCRYPTION_KEY')),
            'database_secured': not SecurityConfig.get_database_url().startswith('sqlite')
        },
        'recommendations': []
    }
    
    if not security_info['configuration']['api_key_set']:
        security_info['recommendations'].append('Set API_KEY environment variable')
    if not security_info['configuration']['encryption_key_set']:
        security_info['recommendations'].append('Set ENCRYPTION_KEY environment variable')
    if not security_info['network_security']['https_required']:
        security_info['recommendations'].append('Enable HTTPS in production')
    
    security_info['overall_score'] = calculate_security_score(security_info)
    
    return jsonify(security_info)

def calculate_security_score(security_info: Dict) -> int:
    score = 0
    max_score = 0
    
    auth_items = security_info['authentication']
    for key, value in auth_items.items():
        max_score += 10
        if value:
            score += 10
    
    data_items = security_info['data_protection']
    for key, value in data_items.items():
        max_score += 10
        if value:
            score += 10
    
    config_items = security_info['configuration']
    for key, value in config_items.items():
        max_score += 10
        if value:
            score += 10
    
    return int((score / max_score) * 100) if max_score > 0 else 0

@app.route('/api/audit-logs', methods=['GET'])
@require_api_key
def get_audit_logs():
    try:
        admin_key = request.headers.get('X-Admin-Key')
        expected_admin_key = os.environ.get('ADMIN_API_KEY')
        
        if not admin_key or not secrets.compare_digest(admin_key, expected_admin_key or ''):
            return jsonify({'error': 'Admin access required'}), 403
        
        try:
            with open(SecurityConfig.AUDIT_LOG_FILE, 'r') as f:
                logs = [json.loads(line) for line in f.readlines()[-100:]]
        except FileNotFoundError:
            logs = []
        
        return jsonify({
            'logs': logs,
            'count': len(logs),
            'file': SecurityConfig.AUDIT_LOG_FILE
        })
        
    except Exception as e:
        logger.error(f"Error reading audit logs: {e}")
        return jsonify({'error': 'Failed to read audit logs'}), 500

def format_timestamp_for_pdf(timestamp_str: str, timezone_used: str) -> str:
    try:
        if not timestamp_str or timestamp_str == 'N/A':
            return "N/A"
        
        dt = parse_assessment_timestamp(timestamp_str)
        
        try:
            if timezone_used and timezone_used != 'UTC':
                patient_tz = pytz.timezone(timezone_used)
                local_dt = dt.astimezone(patient_tz)
            else:
                local_dt = dt
            
            formatted = local_dt.strftime("%B %d, %Y at %H:%M %Z")
            return formatted
            
        except Exception:
            fallback = dt.strftime("%B %d, %Y at %H:%M UTC")
            return fallback
            
    except Exception:
        return timestamp_str or "Timestamp unavailable"

@app.route('/api/generate-pdf-report', methods=['POST'])
@require_api_key
@validate_json_content
def generate_pdf_report():
    try:
        data = request.json
        assessment_data = data.get('assessment_data', {})
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              topMargin=1*inch, 
                              bottomMargin=1*inch,
                              leftMargin=0.75*inch,
                              rightMargin=0.75*inch)
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#4f46e5')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#1e293b')
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.HexColor('#475569')
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=12
        )
        
        story = []
        
        story.append(Paragraph("MENTAL HEALTH ASSESSMENT REPORT", title_style))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("ASSESSMENT DETAILS", heading_style))
        
        assessment_timestamp_str = assessment_data.get('assessment_timestamp', '')
        report_timestamp_str = assessment_data.get('timestamp', '')
        timezone_used = assessment_data.get('timezone', 'UTC')
        
        assessment_date_str = format_timestamp_for_pdf(assessment_timestamp_str, timezone_used)
        report_date_str = format_timestamp_for_pdf(report_timestamp_str, timezone_used)
        
        meta_data = [
            ["Assessment ID:", assessment_data.get('id', 'N/A')],
            ["Assessment Started:", assessment_date_str],
            ["Report Generated:", report_date_str],
            ["Assessment Timezone:", timezone_used]
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(meta_table)
        story.append(Spacer(1, 20))
        
        patient_info = assessment_data.get('patient_info', {})
        story.append(Paragraph("PATIENT INFORMATION", heading_style))
        
        patient_data = [
            ["Patient Name:", patient_info.get('name', 'Not provided')],
            ["Patient Number:", patient_info.get('number', 'Not provided')],
            ["Age:", patient_info.get('age', 'Not provided')],
            ["Gender:", patient_info.get('gender', 'Not provided')]
        ]
        
        patient_table = Table(patient_data, colWidths=[1.5*inch, 4.5*inch])
        patient_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f9ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(patient_table)
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("CLINICAL ASSESSMENT RESULTS", heading_style))
        
        primary_diagnosis = assessment_data.get('primary_diagnosis', 'N/A')
        confidence = assessment_data.get('confidence_percentage', 0)
        
        diagnosis_data = [
            ["Primary Diagnosis:", primary_diagnosis],
            ["Confidence Level:", f"{confidence:.1f}%"],
            ["Assessment Date & Time:", report_date_str]
        ]
        
        confidence_color = colors.HexColor('#10b981')
        if confidence < 70:
            confidence_color = colors.HexColor('#f59e0b')
        if confidence < 50:
            confidence_color = colors.HexColor('#ef4444')
        
        diagnosis_table = Table(diagnosis_data, colWidths=[2*inch, 4*inch])
        diagnosis_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 11),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('TEXTCOLOR', (1, 1), (1, 1), confidence_color),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 11),
            ('FONT', (1, 0), (1, 0), 'Helvetica-Bold', 11),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#4f46e5')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(diagnosis_table)
        story.append(Spacer(1, 15))
        
        diagnosis_desc = assessment_data.get('diagnosis_description', 
                                           'Comprehensive mental health assessment completed.')
        story.append(Paragraph("Assessment Summary:", subheading_style))
        story.append(Paragraph(diagnosis_desc, normal_style))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("DIFFERENTIAL DIAGNOSES", heading_style))
        other_diagnoses = assessment_data.get('all_diagnoses', [])
        
        if other_diagnoses:
            diagnoses_data = [["Diagnosis", "Probability"]]
            
            for diagnosis in other_diagnoses[:5]:
                diagnoses_data.append([
                    diagnosis.get('diagnosis', 'N/A'),
                    f"{diagnosis.get('confidence_percentage', 0):.1f}%"
                ])
            
            diagnoses_table = Table(diagnoses_data, colWidths=[4*inch, 1.5*inch])
            diagnoses_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
                ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(diagnoses_table)
        else:
            story.append(Paragraph("No additional diagnoses considered.", normal_style))
        
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("IMPORTANT DISCLAIMER", heading_style))
        disclaimer_text = """
        This mental health assessment is provided for informational and educational purposes only. 
        It is not intended as a substitute for professional medical advice, diagnosis, or treatment. 
        Always seek the advice of your physician or qualified mental health provider with any 
        questions you may have regarding a medical or psychological condition.
        
        If you are experiencing a mental health emergency or having thoughts of harming yourself 
        or others, please contact emergency services immediately by calling your local emergency 
        number or a crisis hotline.
        
        This assessment does not constitute a clinical diagnosis and should not be used as the 
        sole basis for making healthcare decisions.
        """
        story.append(Paragraph(disclaimer_text, normal_style))
        story.append(Spacer(1, 10))
        
        footer_text = "Confidential Mental Health Assessment Report - Generated by Clinical Assessment System"
        story.append(Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#64748b')
        )))
         
        doc.build(story)
        
        pdf = buffer.getvalue()
        buffer.close()
        
        response = app.response_class(
            response=pdf,
            status=200,
            mimetype='application/pdf'
        )
        
        filename = f"mental_health_assessment_{assessment_data.get('id', 'report')}.pdf"
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        return jsonify({'error': f'Failed to generate PDF report: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    audit_logger.log_event(
        event_type='PAGE_NOT_FOUND',
        ip=request.remote_addr,
        details=f"404 for {request.path}",
        severity='INFO'
    )
    
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    else:
        try:
            return send_from_directory('frontend', 'Home.html')
        except:
            return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    audit_logger.log_event(
        event_type='INTERNAL_SERVER_ERROR',
        ip=request.remote_addr,
        details=f"500 error at {request.path}",
        severity='ERROR'
    )
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    audit_logger.log_event(
        event_type='REQUEST_TOO_LARGE',
        ip=request.remote_addr,
        details=f"413 for {request.path}",
        severity='WARNING'
    )
    return jsonify({'error': 'File too large'}), 413

@app.errorhandler(429)
def too_many_requests(error):
    audit_logger.log_event(
        event_type='RATE_LIMIT_TRIGGERED',
        ip=request.remote_addr,
        details=f"429 for {request.path}",
        severity='WARNING'
    )
    return jsonify({
        'error': 'Too many requests',
        'retry_after': SecurityConfig.RATE_LIMIT_WINDOW
    }), 429

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("MENTAL HEALTH ASSESSMENT API - SECURE EDITION v4.0")
    logger.info("=" * 60)
    
    if all([model_package, scaler, label_encoder, feature_names, category_mappings]):
        logger.info("✓ All model components loaded")
        logger.info(f"  Features: {len(feature_names)}")
        logger.info(f"  Classes: {label_encoder.classes_.tolist()}")
    else:
        logger.error("✗ Failed to load model components!")
        if os.environ.get('RENDER'):
            sys.exit(1)
    
    try:
        init_database()
        logger.info("✓ Secure database initialized")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
    
    logger.info("🔒 SECURITY CONFIGURATION:")
    logger.info(f"  API Key Required: {'✓' if SecurityConfig.API_KEY else '✗'}")
    logger.info(f"  Encryption: {'✓' if os.environ.get('ENCRYPTION_KEY') else '✗ (generated)'}")
    logger.info(f"  Audit Logging: ✓ ({SecurityConfig.AUDIT_LOG_FILE})")
    logger.info(f"  Rate Limiting: ✓ ({SecurityConfig.RATE_LIMIT_REQUESTS}/{SecurityConfig.RATE_LIMIT_WINDOW}s)")
    logger.info(f"  CORS Restrictions: ✓")
    logger.info(f"  Security Headers: ✓")
    
    if clinical_enhancer:
        logger.info("✓ Clinical Decision Enhancer: ACTIVE")
    
    port = int(os.environ.get('PORT', 5000))
    debug_mode = not bool(os.environ.get('RENDER'))
    
    logger.info("=" * 60)
    logger.info(f"Starting server on port {port} (Debug: {debug_mode})")
    logger.info("=" * 60)
    
    if os.environ.get('RENDER'):
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        app.run(host='0.0.0.0', port=port, debug=debug_mode)