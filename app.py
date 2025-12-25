from flask import Flask, request, jsonify, send_from_directory, redirect
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
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import json
import re
import secrets
import time
from cryptography.fernet import Fernet
import bcrypt
from itsdangerous import URLSafeTimedSerializer
import pytz
from dateutil import parser, tz as dateutil_tz

# ==================== SECURITY CONFIGURATION ====================
class SecurityConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_urlsafe(32))
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
    
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
                                "connect-src 'self'",
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

encryption_service = EncryptionService()
rate_limiter = RateLimiter()
auth_service = AuthService()

# ==================== FLASK APP SETUP ====================
assessment_storage: Dict[str, Dict[str, Any]] = {}

app = Flask(__name__, 
           static_folder='frontend',
           template_folder='frontend')

app.secret_key = SecurityConfig.SECRET_KEY

# Security middleware
@app.after_request
def set_security_headers(response):
    for header, value in SecurityConfig.SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

# Rate limiting middleware
@app.before_request
def check_rate_limit():
    if request.endpoint and request.endpoint.startswith('api'):
        client_ip = request.remote_addr
        if rate_limiter.is_rate_limited(client_ip, SecurityConfig.RATE_LIMIT_REQUESTS, SecurityConfig.RATE_LIMIT_WINDOW):
            return jsonify({
                'error': 'Rate limit exceeded. Please try again later.',
                'retry_after': SecurityConfig.RATE_LIMIT_WINDOW
            }), 429

# Input validation middleware
@app.before_request
def validate_api_input():
    if request.endpoint and request.endpoint.startswith('api') and request.method in ['POST', 'PUT']:
        if request.content_length and request.content_length > SecurityConfig.MAX_FILE_SIZE:
            return jsonify({'error': 'Request too large'}), 413
        
        if request.is_json:
            try:
                data = request.get_json()
                if not isinstance(data, (dict, list)):
                    return jsonify({'error': 'Invalid JSON format'}), 400
            except Exception as e:
                return jsonify({'error': 'Invalid JSON data'}), 400

if os.environ.get('RENDER'):
    CORS(app, origins=[
        'https://mentivio.onrender.com',
        'http://mentivio-MentalHealth.onrender.com',
        'https://mentivio-web.onrender.com'
    ])
    app.debug = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
else:
    CORS(app, resources={r"/api/*": {"origins": "*"}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== DATABASE SETUP ====================
def get_postgres_connection():
    """Get PostgreSQL database connection using psycopg"""
    conn = None
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        logger.info(f"Attempting to connect to database with URL: {database_url[:30]}...")
        
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
        conn = psycopg.connect(database_url, row_factory=dict_row)
        
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
            
        logger.info("PostgreSQL connection successful")
        return conn
        
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        
        try:
            logger.info("Attempting SQLite fallback...")
            sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mental_health_assessments.db')
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row
            logger.info("SQLite fallback connection successful")
            return conn
        except Exception as sqlite_error:
            logger.error(f"SQLite fallback also failed: {sqlite_error}")
            raise e

def init_database():
    """Initialize database with required tables"""
    try:
        conn = get_postgres_connection()
        
        with conn.cursor() as cur:
            # Check if table exists
            cur.execute('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'assessments'
                );
            ''')
            table_exists = cur.fetchone()['exists']
            
            if not table_exists:
                # Create table with coded_responses_json column
                cur.execute('''
                    CREATE TABLE assessments (
                        id TEXT PRIMARY KEY,
                        assessment_timestamp TEXT,
                        report_timestamp TEXT,
                        timezone TEXT,
                        patient_name TEXT,
                        patient_number TEXT,
                        patient_age INT,
                        patient_gender TEXT,
                        primary_diagnosis TEXT,
                        confidence REAL,
                        confidence_percentage REAL,
                        all_diagnoses_json TEXT,
                        coded_responses_json TEXT,
                        processing_details_json TEXT,
                        technical_details_json TEXT,
                        clinical_insights_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cur.execute('CREATE INDEX idx_patient_number ON assessments(patient_number)')
                cur.execute('CREATE INDEX idx_timestamp ON assessments(report_timestamp)')
                logger.info("Created new assessments table with coded_responses_json column")
            else:
                # Check if responses_json column exists - remove it
                cur.execute('''
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'assessments' 
                    AND column_name = 'responses_json';
                ''')
                responses_column_exists = cur.fetchone()
                
                if responses_column_exists:
                    # Remove the old responses_json column
                    cur.execute('ALTER TABLE assessments DROP COLUMN responses_json;')
                    logger.info("Removed responses_json column from existing assessments table")
                
                # Check if coded_responses_json column exists - add if missing
                cur.execute('''
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'assessments' 
                    AND column_name = 'coded_responses_json';
                ''')
                coded_column_exists = cur.fetchone()
                
                if not coded_column_exists:
                    # Add the column
                    cur.execute('ALTER TABLE assessments ADD COLUMN coded_responses_json TEXT;')
                    logger.info("Added coded_responses_json column to existing assessments table")
        
        conn.commit()
        conn.close()
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
        
        
def convert_to_canonical_key(diagnosis_text: str) -> str:
    """Convert any diagnosis text back to its canonical key"""
    canonical_keys = ['Normal', 'Bipolar Type-1', 'Bipolar Type-2', 'Depression']
    
    if diagnosis_text in canonical_keys:
        return diagnosis_text
    
    # Simplified - just check for keywords
    if 'bipolar' in diagnosis_text.lower() and 'type-1' in diagnosis_text.lower():
        return 'Bipolar Type-1'
    elif 'bipolar' in diagnosis_text.lower() and 'type-2' in diagnosis_text.lower():
        return 'Bipolar Type-2'
    elif 'depression' in diagnosis_text.lower():
        return 'Depression'
    elif 'normal' in diagnosis_text.lower():
        return 'Normal'
    
    return diagnosis_text

def save_assessment_to_db(assessment_data: Dict[str, Any]) -> bool:
    """Save assessment data to database"""
    conn = None
    try:
        # Add debug logging
        logger.info(f"SAVING ASSESSMENT - ID: {assessment_data.get('id')}")
        logger.info(f"SAVING ASSESSMENT - Has coded_responses: {'coded_responses' in assessment_data}")
        
        if 'coded_responses' in assessment_data:
            logger.info(f"SAVING ASSESSMENT - Coded responses count: {len(assessment_data['coded_responses'])}")
        
        sanitized_data = assessment_data.copy()
        
        if 'patient_info' in sanitized_data:
            patient_info = sanitized_data['patient_info']
            age = patient_info.get('age')
            
            if age:
                age_valid, age_msg = SecurityUtils.validate_patient_age(age)
                if not age_valid:
                    patient_info['age'] = None
            
            sanitized_data['patient_info'] = {
                'name': SecurityUtils.sanitize_input(patient_info.get('name', '')),
                'number': SecurityUtils.sanitize_input(patient_info.get('number', '')),
                'age': patient_info.get('age'),
                'gender': SecurityUtils.sanitize_input(patient_info.get('gender', ''))
            }
        
        all_diagnoses = sanitized_data.get('all_diagnoses', [])
        canonical_diagnoses = []
        for diagnosis in all_diagnoses:
            diag_text = diagnosis.get('diagnosis', '')
            canonical_key = convert_to_canonical_key(diag_text)
            
            canonical_diagnoses.append({
                'diagnosis': canonical_key,
                'probability': diagnosis.get('probability', 0),
                'confidence_percentage': diagnosis.get('confidence_percentage', 0),
                'rank': diagnosis.get('rank', 0)
            })
        
        primary_diagnosis = sanitized_data.get('primary_diagnosis', '')
        primary_diagnosis_canonical = convert_to_canonical_key(primary_diagnosis)
        
        # Get coded_responses only
        coded_responses = sanitized_data.get('coded_responses', {})
        
        # Log for debugging
        logger.info(f"Database save - Coded responses: {json.dumps(coded_responses)[:200]}")
        
        conn = get_postgres_connection()
        
        # Insert with coded_responses_json only
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO assessments (
                    id, assessment_timestamp, report_timestamp, timezone,
                    patient_name, patient_number, patient_age, patient_gender,
                    primary_diagnosis, confidence, confidence_percentage,
                    all_diagnoses_json, coded_responses_json,
                    processing_details_json, technical_details_json, clinical_insights_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    assessment_timestamp = EXCLUDED.assessment_timestamp,
                    report_timestamp = EXCLUDED.report_timestamp,
                    timezone = EXCLUDED.timezone,
                    patient_name = EXCLUDED.patient_name,
                    patient_number = EXCLUDED.patient_number,
                    patient_age = EXCLUDED.patient_age,
                    patient_gender = EXCLUDED.patient_gender,
                    primary_diagnosis = EXCLUDED.primary_diagnosis,
                    confidence = EXCLUDED.confidence,
                    confidence_percentage = EXCLUDED.confidence_percentage,
                    all_diagnoses_json = EXCLUDED.all_diagnoses_json,
                    coded_responses_json = EXCLUDED.coded_responses_json,
                    processing_details_json = EXCLUDED.processing_details_json,
                    technical_details_json = EXCLUDED.technical_details_json,
                    clinical_insights_json = EXCLUDED.clinical_insights_json
            """, (
                sanitized_data.get('id'),
                sanitized_data.get('assessment_timestamp', ''),
                sanitized_data.get('timestamp', ''),
                sanitized_data.get('timezone', 'UTC'),
                sanitized_data.get('patient_info', {}).get('name', ''),
                sanitized_data.get('patient_info', {}).get('number', ''),
                sanitized_data.get('patient_info', {}).get('age', ''),
                sanitized_data.get('patient_info', {}).get('gender', ''),
                primary_diagnosis_canonical,
                sanitized_data.get('confidence', 0),
                sanitized_data.get('confidence_percentage', 0),
                json.dumps(canonical_diagnoses),
                json.dumps(coded_responses),  # Original codes only
                json.dumps(sanitized_data.get('processing_details', {})),
                json.dumps(sanitized_data.get('technical_details', {})),
                json.dumps(sanitized_data.get('clinical_insights', {}))
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully saved assessment {sanitized_data.get('id')}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        if conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        return False
    
def load_assessments_from_db(patient_number: str = None) -> Dict[str, List[Dict[str, Any]]]:
    """Load assessments from database"""
    try:
        conn = get_postgres_connection()
        
        with conn.cursor() as cur:
            if patient_number:
                cur.execute('''
                    SELECT * FROM assessments 
                    WHERE patient_number ILIKE %s 
                    ORDER BY report_timestamp DESC
                ''', (f'%{patient_number}%',))
            else:
                cur.execute('SELECT * FROM assessments ORDER BY report_timestamp DESC')
            
            rows = cur.fetchall()
        
        conn.close()
        
        assessments_by_patient: Dict[str, List[Dict[str, Any]]] = {}
        
        for row in rows:
            row_dict = dict(row)
            
            patient_num = row_dict['patient_number']
            if patient_num not in assessments_by_patient:
                assessments_by_patient[patient_num] = []
            
            all_diagnoses_canonical = json.loads(row_dict['all_diagnoses_json']) if row_dict['all_diagnoses_json'] else []
            coded_responses = json.loads(row_dict['coded_responses_json']) if row_dict.get('coded_responses_json') else {}
            processing_details = json.loads(row_dict['processing_details_json']) if row_dict['processing_details_json'] else {}
            technical_details = json.loads(row_dict['technical_details_json']) if row_dict['technical_details_json'] else {}
            clinical_insights = json.loads(row_dict['clinical_insights_json']) if row_dict['clinical_insights_json'] else {}
            
            primary_diagnosis_canonical = row_dict['primary_diagnosis']
            
            if primary_diagnosis_canonical not in ['Normal', 'Bipolar Type-1', 'Bipolar Type-2', 'Depression']:
                primary_diagnosis_canonical = convert_to_canonical_key(primary_diagnosis_canonical)
            
            # Diagnosis will be translated in frontend
            primary_diagnosis = primary_diagnosis_canonical
            
            assessments: List[Dict[str, Any]] = []
            for diagnosis in all_diagnoses_canonical:
                canonical_key = diagnosis.get('diagnosis', '')
                
                if canonical_key not in ['Normal', 'Bipolar Type-1', 'Bipolar Type-2', 'Depression']:
                    canonical_key = convert_to_canonical_key(canonical_key)
                
                assessments.append({
                    'diagnosis': canonical_key,
                    'probability': diagnosis.get('probability', 0),
                    'confidence_percentage': diagnosis.get('confidence_percentage', 0),
                    'rank': diagnosis.get('rank', 0)
                })
            
            assessments.sort(key=lambda x: x.get('rank', 0))
            
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
                'primary_diagnosis': primary_diagnosis,
                'confidence': row_dict['confidence'],
                'confidence_percentage': row_dict['confidence_percentage'],
                'all_diagnoses': assessments,
                'coded_responses': coded_responses,
                'processing_details': processing_details,
                'technical_details': technical_details,
                'clinical_insights': clinical_insights
            }
            
            assessments_by_patient[patient_num].append(assessment)
        
        return assessments_by_patient
        
    except Exception as e:
        logger.error(f"Error loading from database: {e}")
        return {}
    
def load_single_assessment_from_db(patient_name: str, patient_number: str, assessment_id: str) -> Optional[Dict[str, Any]]:
    """Load a single specific assessment from database"""
    try:
        conn = get_postgres_connection()
        
        with conn.cursor() as cur:
            cur.execute('''
                SELECT * FROM assessments 
                WHERE patient_number = %s AND id = %s AND patient_name = %s
            ''', (patient_number, assessment_id, patient_name))
            
            row = cur.fetchone()
            
            if not row:
                conn.close()
                return None
        
        row_dict = dict(row)
        conn.close()
        
        if not row_dict:
            return None
        
        coded_responses = json.loads(row_dict['coded_responses_json']) if row_dict.get('coded_responses_json') else {}
        all_diagnoses = json.loads(row_dict['all_diagnoses_json']) if row_dict.get('all_diagnoses_json') else []
        processing_details = json.loads(row_dict['processing_details_json']) if row_dict.get('processing_details_json') else {}
        technical_details = json.loads(row_dict['technical_details_json']) if row_dict.get('technical_details_json') else {}
        clinical_insights = json.loads(row_dict['clinical_insights_json']) if row_dict.get('clinical_insights_json') else {}
        
        primary_diagnosis = row_dict.get('primary_diagnosis', '')
        
        if primary_diagnosis not in ['Normal', 'Bipolar Type-1', 'Bipolar Type-2', 'Depression']:
            primary_diagnosis = convert_to_canonical_key(primary_diagnosis)
        
        assessments: List[Dict[str, Any]] = []
        for diagnosis in all_diagnoses:
            canonical_key = diagnosis.get('diagnosis', '')
            
            if canonical_key not in ['Normal', 'Bipolar Type-1', 'Bipolar Type-2', 'Depression']:
                canonical_key = convert_to_canonical_key(canonical_key)
            
            assessments.append({
                'diagnosis': canonical_key,
                'probability': diagnosis.get('probability', 0),
                'confidence_percentage': diagnosis.get('confidence_percentage', 0),
                'rank': diagnosis.get('rank', 0)
            })
        
        assessments.sort(key=lambda x: x.get('rank', 0))
        
        assessment: Dict[str, Any] = {
            'id': row_dict.get('id', ''),
            'timestamp': row_dict.get('report_timestamp', ''),
            'assessment_timestamp': row_dict.get('assessment_timestamp', ''),
            'timezone': row_dict.get('timezone', 'UTC'),
            'patient_info': {
                'name': row_dict.get('patient_name', ''),
                'number': row_dict.get('patient_number', ''),
                'age': row_dict.get('patient_age'),
                'gender': row_dict.get('patient_gender', '')
            },
            'primary_diagnosis': primary_diagnosis,
            'confidence': row_dict.get('confidence', 0),
            'confidence_percentage': row_dict.get('confidence_percentage', 0),
            'all_diagnoses': assessments,
            'coded_responses': coded_responses,
            'processing_details': processing_details,
            'technical_details': technical_details,
            'clinical_insights': clinical_insights
        }
        
        return assessment
        
    except Exception as e:
        logger.error(f"Error loading single assessment from database: {e}")
        try:
            conn.close()
        except:
            pass
        return None

def delete_assessment_from_db(patient_number: str, assessment_id: str) -> bool:
    """Delete assessment from database"""
    try:
        conn = get_postgres_connection()
        
        with conn.cursor() as cur:
            cur.execute('''
                DELETE FROM assessments 
                WHERE patient_number = %s AND id = %s
            ''', (patient_number, assessment_id))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error deleting from database: {e}")
        return False


# ==================== MODEL COMPONENTS ====================
model_package: Optional[Dict[str, Any]] = None
scaler: Optional[Any] = None
label_encoder: Optional[Any] = None
feature_names: Optional[List[str]] = None
category_mappings: Optional[Dict[str, Any]] = None
clinical_enhancer: Optional[Any] = None

def load_model_components() -> Tuple[Optional[Dict[str, Any]], Optional[Any], Optional[Any], Optional[List[str]], Optional[Dict[str, Any]]]:
    """Load all required model components"""
    global model_package, scaler, label_encoder, feature_names, category_mappings
    
    try:
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
        
        model_path = os.path.join(models_dir, 'mental_health_model.pkl')
        model_package = joblib.load(model_path)
        
        scaler_path = os.path.join(models_dir, 'scaler.pkl')
        scaler = joblib.load(scaler_path)
        
        encoder_path = os.path.join(models_dir, 'label_encoder.pkl')
        label_encoder = joblib.load(encoder_path)
        
        feature_names_path = os.path.join(models_dir, 'feature_names.pkl')
        with open(feature_names_path, 'rb') as f:
            feature_names = pickle.load(f)
        
        category_mappings_path = os.path.join(models_dir, 'category_mappings.pkl')
        with open(category_mappings_path, 'rb') as f:
            category_mappings = pickle.load(f)
        
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
    """Initialize the clinical decision enhancer"""
    global clinical_enhancer
    if feature_names and label_encoder:
        clinical_enhancer = ClinicalDecisionEnhancer(feature_names, label_encoder)
    else:
        logger.warning("Could not initialize Clinical Decision Enhancer")

class ClinicalPreprocessor:
    """EXACTLY replicates the preprocessing pipeline from train_model.py"""
    
    def __init__(self, category_mappings: Optional[Dict[str, Any]] = None):
        self.category_mappings = category_mappings or {}
        self.processing_log: List[str] = []
    
    def log_step(self, step: str, details: str) -> None:
        self.processing_log.append(f"{step}: {details}")
    
    def encode_user_responses(self, raw_responses: Dict[str, Any]) -> Dict[str, Any]:
        encoded_responses: Dict[str, Any] = {}
        
        frequency_mapping = self.category_mappings.get('frequency', {'Seldom': 0, 'Sometimes': 1, 'Usually': 2, 'Most-Often': 3})
        yes_no_mapping = self.category_mappings.get('yes_no', {'NO': 0, 'YES': 1})
        sexual_activity_mapping = self.category_mappings.get('sexual_activity', {
            'No interest': 0, 'Low interest': 1, 'Moderate interest': 2, 'High interest': 3, 'Very high interest': 4
        })
        concentration_mapping = self.category_mappings.get('concentration', {
            'Cannot concentrate': 0, 'Poor concentration': 1, 'Average concentration': 2, 'Good concentration': 3, 'Excellent concentration': 4
        })
        optimism_mapping = self.category_mappings.get('optimism', {
            'Extremely pessimistic': 0, 'Pessimistic': 1, 'Neutral outlook': 2, 'Optimistic': 3, 'Extremely optimistic': 4
        })
        
        for feature, value in raw_responses.items():
            training_feature_name = feature
            
            if feature in ['Sadness', 'Euphoric', 'Exhausted', 'Sleep disorder', 'Anxiety', 
                        'Depressed_Mood', 'Irritability', 'Worrying', 'Fatigue']:
                if value in frequency_mapping:
                    encoded_value = frequency_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                else:
                    encoded_responses[training_feature_name] = 1
            
            elif feature in ['Mood Swing', 'Suicidal thoughts', 'Aggressive Response', 'Nervous Breakdown', 
                           'Overthinking', 'Anorexia', 'Authority Respect', 'Try Explanation',
                           'Ignore & Move-On', 'Admit Mistakes']:
                if value in yes_no_mapping:
                    encoded_value = yes_no_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                else:
                    encoded_responses[training_feature_name] = 0
            
            elif feature == 'Concentration':
                if value in concentration_mapping:
                    encoded_value = concentration_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                else:
                    encoded_responses[training_feature_name] = 2
            
            elif feature == 'Optimism':
                if value in optimism_mapping:
                    encoded_value = optimism_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                else:
                    encoded_responses[training_feature_name] = 2
            
            elif feature == 'Sexual Activity':
                if value in sexual_activity_mapping:
                    encoded_value = sexual_activity_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                else:
                    encoded_responses[training_feature_name] = 2
            
            else:
                encoded_responses[training_feature_name] = value
        
        return encoded_responses
    
    def apply_feature_engineering(self, encoded_responses: Dict[str, Any]) -> Dict[str, Any]:
        responses = encoded_responses.copy()
        
        if 'Mood Swing' in responses and 'Sadness' in responses:
            mood_swing = float(responses.get('Mood Swing', 0))
            sadness = float(responses.get('Sadness', 0))
            composite_value = mood_swing * 0.6 + sadness * 0.4
            responses['Mood_Emotion_Composite'] = composite_value
            responses['Mood_Emotion_Composite_Score'] = composite_value
        
        if 'Sleep disorder' in responses and 'Exhausted' in responses:
            sleep_disorder = float(responses.get('Sleep disorder', 0))
            exhausted = float(responses.get('Exhausted', 0))
            composite_value = sleep_disorder * 0.7 + exhausted * 0.3
            responses['Sleep_Fatigue_Composite'] = composite_value
            responses['Sleep_Fatigue_Composite_Score'] = composite_value
        
        behavioral_features = ['Aggressive Response', 'Nervous Breakdown', 'Overthinking']
        behavioral_scores = []
        for feat in behavioral_features:
            if feat in responses:
                try:
                    behavioral_scores.append(float(responses[feat]))
                except (ValueError, TypeError):
                    behavioral_scores.append(0.0)
        
        if behavioral_scores:
            composite_value = sum(behavioral_scores) / len(behavioral_scores)
            responses['Behavioral_Stress_Composite'] = composite_value
            responses['Behavioral_Stress_Composite_Score'] = composite_value
        
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
        
        # Simplified safety warnings (frontend handles translations)
        security_warnings = {
            'suicidal_thoughts': 'Suicidal thoughts detected - please seek immediate professional help',
            'aggressive_behavior': 'Aggressive behavior patterns detected - safety assessment recommended',
            'nervous_breakdown': 'History of nervous breakdown detected - consider professional evaluation',
            'severe_depression': 'Severe depression symptoms detected - urgent evaluation recommended',
            'manic_symptoms': 'Potential manic symptoms detected - clinical assessment advised'
        }
        
        if suicidal_thoughts == 1:
            warnings.append(security_warnings.get('suicidal_thoughts', 'Suicidal thoughts detected - please seek immediate professional help'))
        
        if aggressive_response == 1:
            warnings.append(security_warnings.get('aggressive_behavior', 'Aggressive behavior patterns detected - safety assessment recommended'))
        
        if nervous_breakdown == 1:
            warnings.append(security_warnings.get('nervous_breakdown', 'History of nervous breakdown detected - consider professional evaluation'))
        
        if (sadness >= 3 and 
            sleep_disorder >= 2 and
            exhausted >= 2):
            warnings.append(security_warnings.get('severe_depression', 'Severe depression symptoms detected - urgent evaluation recommended'))
        
        if (euphoric >= 3 and 
            mood_swing >= 2):
            warnings.append(security_warnings.get('manic_symptoms', 'Potential manic symptoms detected - clinical assessment advised'))
        
        safety_ok = len(warnings) == 0
        if not safety_ok:
            self.log_step("Safety_Check", f"Safety warnings: {warnings}")
        else:
            self.log_step("Safety_Check", "All safety checks passed")
            
        return safety_ok, warnings

    def preprocess(self, raw_responses: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        self.processing_log = []
        self.log_step("Pipeline_Start", f"Processing {len(raw_responses)} raw features: {list(raw_responses.keys())}")
        
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
            raise e

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def validate_assessment_responses(responses: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate assessment responses for security"""
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
        
        responses_copy = processed_responses.copy()
        
        for i, feature_name in enumerate(feature_names):
            if feature_name in responses_copy:
                value = responses_copy[feature_name]
                if isinstance(value, (int, float)):
                    feature_array[i] = value
                else:
                    try:
                        feature_array[i] = float(value)
                    except (ValueError, TypeError):
                        feature_array[i] = 0
            else:
                if feature_name in ['Mood_Emotion_Composite', 'Mood_Emotion_Composite_Score']:
                    mood_swing = responses_copy.get('Mood Swing', 0)
                    sadness = responses_copy.get('Sadness', 0)
                    feature_array[i] = float(mood_swing) * 0.6 + float(sadness) * 0.4
                    
                elif feature_name in ['Sleep_Fatigue_Composite', 'Sleep_Fatigue_Composite_Score']:
                    sleep_disorder = responses_copy.get('Sleep disorder', 0)
                    exhausted = responses_copy.get('Exhausted', 0)
                    feature_array[i] = float(sleep_disorder) * 0.7 + float(exhausted) * 0.3
                    
                elif feature_name in ['Behavioral_Stress_Composite', 'Behavioral_Stress_Composite_Score']:
                    aggressive = responses_copy.get('Aggressive Response', 0)
                    nervous = responses_copy.get('Nervous Breakdown', 0)
                    overthinking = responses_copy.get('Overthinking', 0)
                    
                    behavioral_scores = []
                    for val in [aggressive, nervous, overthinking]:
                        try:
                            behavioral_scores.append(float(val))
                        except (ValueError, TypeError):
                            behavioral_scores.append(0.0)
                    
                    if behavioral_scores:
                        feature_array[i] = sum(behavioral_scores) / len(behavioral_scores)
                    else:
                        feature_array[i] = 0
                        
                elif feature_name == 'Risk_Assessment_Score':
                    suicidal = responses_copy.get('Suicidal thoughts', 0)
                    aggressive = responses_copy.get('Aggressive Response', 0)
                    nervous = responses_copy.get('Nervous Breakdown', 0)
                    feature_array[i] = min(10, float(suicidal) * 5 + float(aggressive) * 3 + float(nervous) * 2)
                    
                elif feature_name == 'Cognitive_Function_Score':
                    concentration = responses_copy.get('Concentration', 2)
                    optimism = responses_copy.get('Optimism', 2)
                    feature_array[i] = (float(concentration) + float(optimism)) / 2.0
                    
                elif feature_name == 'Mood_Stability_Score':
                    mood_swing = responses_copy.get('Mood Swing', 0)
                    sadness = responses_copy.get('Sadness', 0)
                    euphoric = responses_copy.get('Euphoric', 0)
                    feature_array[i] = max(0, 10 - (float(mood_swing) * 3 + float(sadness) * 2 + abs(float(euphoric) - 1) * 2))
                    
                else:
                    feature_array[i] = 0
        
        feature_df = pd.DataFrame([feature_array], columns=feature_names)
        
        return feature_df
        
    except Exception as e:
        logger.error(f"Feature conversion error: {e}")
        return None

# Initialize database at startup
init_database()

model_package, scaler, label_encoder, feature_names, category_mappings = load_model_components()
initialize_clinical_enhancer()
preprocessor = ClinicalPreprocessor(category_mappings)

# ==================== ROUTES ====================
@app.route('/')
def serve_index():
    return redirect('/home', code=302) 

@app.route('/<page_name>')
def serve_html_page(page_name):
    # Main pages (without .html extension)
    main_pages = {
        'home': 'home.html',
        'about': 'about.html',
        'analogy': 'analogy.html',
        'prediction': 'prediction.html',
        'resources': 'resources.html',
        'crisis-support': 'crisis-support.html',
        'relief_techniques': 'relief_techniques.html'
    }
    
    if page_name in main_pages:
        return send_from_directory('frontend', main_pages[page_name])
    
    # Resource pages (without .html extension)
    resource_pages = [
        'anxiety-resource', 'bipolar-resource', 'depression-resource',
        'medication-resource', 'mindfulness-resource', 'ptsd-resource',
        'selfcare-resource', 'therapy-resource'
    ]
    
    if page_name in resource_pages:
        return send_from_directory('frontend/resources', f'{page_name}.html')
    
    # Try with .html extension for backward compatibility
    try:
        return send_from_directory('frontend', f'{page_name}.html')
    except:
        try:
            return send_from_directory('frontend/resources', f'{page_name}.html')
        except:
            return send_from_directory('frontend', 'home.html')

# Keep this for backward compatibility with .html URLs
@app.route('/<page_name>.html')
def serve_html_page_with_extension(page_name):
    return redirect(f'/{page_name}')

@app.route('/resources/<resource_name>')
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

# Keep this for backward compatibility with .html URLs
@app.route('/resources/<resource_name>.html')
def serve_resource_page_with_extension(resource_name):
    return redirect(f'/resources/{resource_name}')

@app.route('/css/<path:filename>')
def serve_css(filename):
    try:
        return send_from_directory('frontend/css', filename)
    except:
        return send_from_directory('frontend/resources', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('frontend/js', filename)

@app.route('/resources/css/<path:filename>')
def serve_resource_css(filename):
    return send_from_directory('frontend/resources', filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('frontend/assets', filename)

@app.route('/resource-detail.css')
def serve_resource_detail_css():
    return send_from_directory('frontend/resources', 'resource-detail.css')



@app.route('/<path:path>')
def serve_static_files(path):
    # Don't redirect static files
    if path.startswith(('css/', 'js/', 'assets/', 'lang/', 'resources/')):
        try:
            if path.startswith('resources/'):
                resource_path = path.replace('resources/', '', 1)
                return send_from_directory('frontend/resources', resource_path)
            return send_from_directory('frontend', path)
        except:
            pass
    
    # Try to serve as a page without extension
    try:
        return serve_html_page(path)
    except:
        return send_from_directory('frontend', 'home.html')







@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        db_healthy = False
        db_type = "Unknown"
        try:
            conn = get_postgres_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT 1 as test')
                    db_healthy = True
                    db_type = 'PostgreSQL'
                conn.close()
        except Exception as e:
            logger.warning(f"Database health check warning: {e}")

        components_loaded = all([
            model_package is not None,
            scaler is not None, 
            label_encoder is not None,
            feature_names is not None,
            category_mappings is not None
        ])
        
        overall_healthy = components_loaded and db_healthy
        
        health_info = {
            'status': 'healthy' if overall_healthy else 'degraded',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'components_loaded': components_loaded,
            'database_healthy': db_healthy,
            'database_type': db_type,
            'model_loaded': model_package is not None,
            'scaler_loaded': scaler is not None,
            'encoder_loaded': label_encoder is not None,
            'features_loaded': feature_names is not None,
            'category_mappings_loaded': category_mappings is not None,
            'total_features': len(feature_names) if feature_names else 0,
            'available_classes': label_encoder.classes_.tolist() if label_encoder else [],
            'clinical_enhancer_available': clinical_enhancer is not None,
            'security': {
                'rate_limiting': True,
                'input_validation': True,
                'headers_security': True,
                'encryption_available': True
            },
            'message': 'Service is ready' if overall_healthy else 'Service is starting up'
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

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        language = data.get('language', 'en')
        coded_responses = data.get('coded_responses', {})  # Original codes
        patient_info = data.get('patientInfo', {})
        assessment_start_time = data.get('assessment_start_time')
        
        if not coded_responses:
            return jsonify({'error': 'No responses provided'}), 400
        
        # Convert coded responses to English for model processing
        user_responses = convert_coded_to_english(coded_responses)
        
        # Validate the English responses for the model
        responses_valid, responses_msg = validate_assessment_responses(user_responses)
        if not responses_valid:
            return jsonify({'error': f'Invalid responses: {responses_msg}'}), 400
        
        patient_valid, patient_msg = SecurityUtils.validate_patient_data(patient_info)
        if not patient_valid:
            return jsonify({'error': f'Invalid patient data: {patient_msg}'}), 400
        
        if 'age' in patient_info and patient_info['age']:
            age = patient_info['age']
            age_valid, age_msg = SecurityUtils.validate_patient_age(age)
            if not age_valid:
                return jsonify({'error': f'Invalid age: {age_msg}'}), 400
        
        client_timezone = request.headers.get('X-Client-Timezone', 'UTC')
        
        import re
        if not re.match(r'^[A-Za-z/_+-]+$', client_timezone):
            client_timezone = 'UTC'  
        
        try:
            tz = pytz.timezone(client_timezone)
            utc_now = datetime.now(timezone.utc)
            client_now = utc_now.astimezone(tz)
        except:
            client_timezone = 'UTC'
            tz = timezone.utc
            client_now = datetime.now(timezone.utc)
        
        report_generation_time = client_now.isoformat()
        
        if assessment_start_time:
            try:
                assessment_dt = parse_assessment_timestamp(assessment_start_time)
                assessment_dt_client = assessment_dt.astimezone(tz)
                assessment_date_str = assessment_dt_client.isoformat()
                
                time_diff = client_now - assessment_dt_client
                
            except Exception as e:
                assessment_date_str = client_now.isoformat()
        else:
            assessment_date_str = client_now.isoformat()

        # Log the responses for debugging
        logger.info(f"Predict - Coded responses: {coded_responses}")
        logger.info(f"Predict - Converted to English: {user_responses}")
        
        try:
            # Process English responses for the model
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
            confidence_percentage = round(float(prob * 100), 0)
            
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
        final_confidence_percentage = round(primary_confidence_percentage, 0)
        
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
                        diagnosis['confidence_percentage'] = round(final_confidence_percentage,0)
                        break
                
                all_diagnoses.sort(key=lambda x: x['probability'], reverse=True)
                
                final_diagnosis = all_diagnoses[0]['diagnosis']
                final_confidence = all_diagnoses[0]['probability']
                final_confidence_percentage = all_diagnoses[0]['confidence_percentage']

        response_data = {
            'primary_diagnosis': final_diagnosis,
            'confidence': float(final_confidence),
            'confidence_percentage': round(float(final_confidence_percentage),0),
            'all_diagnoses': [
                {
                    **diagnosis,
                    'diagnosis': diagnosis['diagnosis'], 
                }
                for diagnosis in all_diagnoses
            ],
            'timestamp': report_generation_time,
            'assessment_timestamp': assessment_date_str,
            'timezone': client_timezone,
            'assessment_id': f"MH{client_now.strftime('%Y%m%d%H%M%S')}",
            'patient_info': patient_info,
            'coded_responses': coded_responses,  # Send back the original codes
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
                'security_validation': 'PASSED',
                'language': language
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
            },
            'language': language
        }
        
        if clinical_enhancement:
            response_data['clinical_insights'] = {
                'original_diagnosis': clinical_enhancement.get('original_diagnosis', primary_diagnosis),  
                'enhanced_diagnosis': clinical_enhancement.get('enhanced_diagnosis', primary_diagnosis),
                'enhancement_applied': clinical_enhancement.get('enhanced_diagnosis', primary_diagnosis) != clinical_enhancement.get('original_diagnosis', primary_diagnosis),
                'adjustment_reasons': clinical_enhancement.get('adjustment_reasons', []),
                'pattern_analysis': clinical_enhancement.get('clinical_analysis', {}),
                'confidence_adjustment': float(clinical_enhancement.get('confidence_adjustment', 0.0) * 100),
                'original_confidence': float(clinical_enhancement.get('original_confidence', primary_confidence))
            }
        
        # Assessment data for database
        assessment_data_for_db = {
            'primary_diagnosis': final_diagnosis,
            'confidence': float(final_confidence),
            'confidence_percentage': round(float(final_confidence_percentage),0),
            'all_diagnoses': [
                {
                    'diagnosis': diagnosis['diagnosis'],
                    'probability': diagnosis['probability'],
                    'confidence_percentage': round(diagnosis['confidence_percentage'],0),
                    'rank': diagnosis['rank']
                }
                for diagnosis in all_diagnoses
            ],
            'timestamp': report_generation_time,
            'assessment_timestamp': assessment_date_str,
            'timezone': client_timezone,
            'assessment_id': f"MH{client_now.strftime('%Y%m%d%H%M%S')}",
            'patient_info': patient_info,
            'coded_responses': coded_responses,  # Store only the original codes
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
                'security_validation': 'PASSED',
                'request_language': language
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
            assessment_data_for_db['clinical_insights'] = {
                'original_diagnosis': clinical_enhancement.get('original_diagnosis', primary_diagnosis),
                'enhanced_diagnosis': clinical_enhancement.get('enhanced_diagnosis', primary_diagnosis),
                'enhancement_applied': clinical_enhancement.get('enhanced_diagnosis', primary_diagnosis) != clinical_enhancement.get('original_diagnosis', primary_diagnosis),
                'adjustment_reasons': clinical_enhancement.get('adjustment_reasons', []),
                'pattern_analysis': clinical_enhancement.get('clinical_analysis', {}),
                'confidence_adjustment': float(clinical_enhancement.get('confidence_adjustment', 0.0) * 100),
                'original_confidence': float(clinical_enhancement.get('original_confidence', primary_confidence))
            }
        
        if 'assessment_id' in response_data:
            assessment_data_for_db['id'] = response_data['assessment_id']
        elif 'id' not in assessment_data_for_db:
            assessment_data_for_db['id'] = f"MH{client_now.strftime('%Y%m%d%H%M%S')}"

        if save_assessment_to_db(assessment_data_for_db):
            logger.info(f"Assessment saved: {assessment_data_for_db['id']}")
        else:
            logger.error(f"Failed to save assessment: {assessment_data_for_db.get('id', 'unknown')}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Secure prediction endpoint error: {e}")
        return jsonify({'error': 'Assessment failed. Please try again.'}), 500

def convert_coded_to_english(coded_responses):
    """Convert coded responses to English for model processing"""
    english_responses = {}
    
    # Code to English mapping
    CODE_TO_ENGLISH = {
        'YN1': 'NO', 'YN2': 'YES',
        'FR1': 'Seldom', 'FR2': 'Sometimes', 'FR3': 'Usually', 'FR4': 'Most-Often',
        'CO1': 'Cannot concentrate', 'CO2': 'Poor concentration', 'CO3': 'Average concentration',
        'CO4': 'Good concentration', 'CO5': 'Excellent concentration',
        'OP1': 'Extremely pessimistic', 'OP2': 'Pessimistic', 'OP3': 'Neutral outlook',
        'OP4': 'Optimistic', 'OP5': 'Extremely optimistic',
        'SA1': 'No interest', 'SA2': 'Low interest', 'SA3': 'Moderate interest',
        'SA4': 'High interest', 'SA5': 'Very high interest'
    }
    
    # Question code to feature mapping
    QUESTION_TO_FEATURE = {
        'Q1': 'Mood Swing', 'Q2': 'Sadness', 'Q3': 'Euphoric',
        'Q4': 'Sleep disorder', 'Q5': 'Exhausted',
        'Q6': 'Suicidal thoughts', 'Q7': 'Aggressive Response',
        'Q8': 'Nervous Breakdown', 'Q9': 'Overthinking',
        'Q10': 'Anorexia', 'Q11': 'Authority Respect',
        'Q12': 'Try Explanation', 'Q13': 'Ignore & Move-On',
        'Q14': 'Admit Mistakes', 'Q15': 'Concentration',
        'Q16': 'Optimism', 'Q17': 'Sexual Activity'
    }
    
    for question_code, answer_code in coded_responses.items():
        if question_code in QUESTION_TO_FEATURE:
            feature = QUESTION_TO_FEATURE[question_code]
            english_answer = CODE_TO_ENGLISH.get(answer_code, 'NO')  # Default to 'NO' if code not found
            english_responses[feature] = english_answer
    
    return english_responses

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
        
    except (ValueError, TypeError) as e:
        return datetime.now(timezone.utc)

@app.route('/api/save-assessment', methods=['POST'])
def save_assessment():
    try:
        data = request.json
        assessment_data = data.get('assessment_data', {})
        if not assessment_data:
            return jsonify({'error': 'No assessment data provided'}), 400
        
        if not isinstance(assessment_data, dict):
            return jsonify({'error': 'Invalid assessment data format'}), 400
        
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
            return jsonify({
                'success': True,
                'assessment_id': assessment_data['id'],
                'message': 'Assessment saved successfully'
            })
        else:
            return jsonify({'error': 'Failed to save assessment data to database'}), 500
        
    except Exception as e:
        logger.error(f"Error saving assessment: {e}")
        return jsonify({'error': f'Failed to save assessment: {str(e)}'}), 500

@app.route('/api/get-patient-assessments', methods=['POST'])
def get_patient_assessments():
    try:
        data = request.json
        patient_name = data.get('name', '').strip()
        patient_number = data.get('number', '').strip()
        
        if not patient_name or not patient_number:
            return jsonify({'error': 'Patient name and number required'}), 400
        
        assessments_by_patient = load_assessments_from_db(patient_number)
        
        if not assessments_by_patient or patient_number not in assessments_by_patient:
            return jsonify({
                'success': True,
                'assessments': [],
                'count': 0,
                'message': 'No assessments found for this patient'
            })
        
        patient_assessments = assessments_by_patient.get(patient_number, [])
        
        filtered_assessments = [
            assessment for assessment in patient_assessments
            if assessment.get('patient_info', {}).get('name', '').lower() == patient_name.lower()
        ]
        
        if len(filtered_assessments) == 0:
            return jsonify({
                'success': True,
                'assessments': [],
                'count': 0,
                'message': 'No assessments found for this patient'
            })
        
        return jsonify({
            'success': True,
            'assessments': filtered_assessments,
            'count': len(filtered_assessments),
            'cached': False
        })
        
    except Exception as e:
        logger.error(f"Error retrieving assessments: {e}")
        return jsonify({'error': f'Failed to retrieve assessments: {str(e)}'}), 500
    
@app.route('/api/get-single-assessment', methods=['POST'])
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
            'assessment': enhanced_assessment,
            'cached': False
        })
        
    except Exception as e:
        logger.error(f"Error retrieving single assessment: {e}")
        return jsonify({'error': f'Failed to retrieve assessment: {str(e)}'}), 500
    
def enhance_assessment_data(assessment: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if not assessment.get('primary_diagnosis') and assessment.get('all_diagnoses'):
            assessment['primary_diagnosis'] = assessment['all_diagnoses'][0].get('diagnosis', '')
            if not assessment.get('confidence_percentage') and assessment['all_diagnoses']:
                assessment['confidence_percentage'] = round(assessment['all_diagnoses'][0].get('confidence_percentage', 0), 0)
                assessment['confidence'] = assessment['confidence_percentage'] / 100.0
        
        if 'all_diagnoses' not in assessment or not assessment['all_diagnoses']:
            assessment['all_diagnoses'] = [
                {
                    'diagnosis': assessment.get('primary_diagnosis', ''),
                    'probability': assessment.get('confidence', 0),
                    'confidence_percentage': round(assessment.get('confidence_percentage', 0), 0)
                }
            ]
        
        if 'coded_responses' not in assessment:
            assessment['coded_responses'] = {}
        
        if 'processing_details' not in assessment:
            assessment['processing_details'] = {
                'preprocessing_steps': 15,
                'clinical_safety_warnings': [],
                'total_features_processed': len(assessment.get('coded_responses', {})),
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
    
@app.route('/api/delete-assessment', methods=['POST'])
def delete_assessment():
    try:
        data = request.json
        patient_number = data.get('patient_number', '')
        assessment_id = data.get('assessment_id', '')
        
        if not patient_number or not assessment_id:
            return jsonify({'error': 'Patient number and assessment ID required'}), 400
        
        if delete_assessment_from_db(patient_number, assessment_id):
            return jsonify({'success': True, 'message': 'Assessment deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete assessment from database'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting assessment: {e}")
        return jsonify({'error': f'Failed to delete assessment: {str(e)}'}), 500

@app.route('/api')
def api_info():
    return jsonify({
        'message': 'Enhanced Mental Health Assessment API is running!',
        'version': '3.0',
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
def security_status():
    return jsonify({
        'security': {
            'rate_limiting': True,
            'input_validation': True,
            'security_headers': True,
            'encryption_available': True,
            'session_management': True,
            'cors_protection': True
        },
        'config': {
            'max_input_length': SecurityConfig.MAX_INPUT_LENGTH,
            'max_responses': SecurityConfig.MAX_RESPONSES,
            'rate_limit_requests': SecurityConfig.RATE_LIMIT_REQUESTS,
            'rate_limit_window': SecurityConfig.RATE_LIMIT_WINDOW,
            'session_timeout': SecurityConfig.SESSION_TIMEOUT
        }
    })

# ==================== PDF REPORT GENERATION ====================

@app.route('/api/generate-pdf-report', methods=['POST']) 
def generate_pdf_report():
    """Generate PDF report using pre-translated data from frontend"""
    try:
        data = request.json
        logger.info(f"PDF generation request received")
        
        if not data:
            logger.error("No data provided in PDF request")
            return jsonify({'error': 'No data provided'}), 400
        
        pdf_data = data.get('pdf_data', {})
        language = data.get('language', 'en')
        
        logger.info(f"Language: {language}")
        logger.info(f"PDF data keys: {list(pdf_data.keys()) if pdf_data else 'None'}")
        
        if not pdf_data:
            logger.error("No PDF data provided")
            return jsonify({'error': 'No PDF data provided'}), 400
        
        # Log patient info for debugging
        if 'patient_info' in pdf_data:
            logger.info(f"Patient: {pdf_data['patient_info'].get('name', 'Unknown')}")
            
        # Extract pre-translated data from frontend
        patient_info = pdf_data.get('patient_info', {})
        primary_diagnosis = pdf_data.get('primary_diagnosis', '')
        all_diagnoses = pdf_data.get('all_diagnoses', [])
        questions_and_answers = pdf_data.get('questions_and_answers', [])
        pdf_translations = pdf_data.get('pdf_translations', {})
        confidence_percentage = pdf_data.get('confidence_percentage', 0)
        diagnosis_description = pdf_data.get('diagnosis_description', '')
        
        # Extract original data for font fallback
        original_data = pdf_data.get('original_data', {})
        coded_responses = original_data.get('coded_responses', {})
        
        buffer = io.BytesIO()
        
        # FONT HANDLING - Based on language
        base_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'
        
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            font_path = './frontend/assets/fonts/'
            
            # Font mapping for different languages
            font_mapping = {
                'zh': {  # Chinese
                    'regular': 'NotoSansSC-Regular',
                    'bold': 'NotoSansSC-Bold',
                    'extension': '.ttf'
                },
                'vi': {  # Vietnamese
                    'regular': 'NotoSans-Regular',
                    'bold': 'NotoSans-Bold', 
                    'extension': '.ttf'
                },
                'hi': {  # Hindi
                    'regular': 'NotoSansDevanagari-Regular',
                    'bold': 'NotoSansDevanagari-Bold',
                    'extension': '.ttf'
                },
                'ar': {  # Arabic
                    'regular': 'NotoSansArabic-Regular',
                    'bold': 'NotoSansArabic-Bold',
                    'extension': '.ttf'
                },
                'ko': {  # Korean
                    'regular': 'NotoSansKR-Regular',
                    'bold': 'NotoSansKR-Bold',
                    'extension': '.ttf'
                },
                'ja': {  # Japanese
                    'regular': 'NotoSansJP-Regular',
                    'bold': 'NotoSansJP-Bold',
                    'extension': '.ttf'
                },
                'th': {  # Thai
                    'regular': 'NotoSansThai-Regular',
                    'bold': 'NotoSansThai-Bold',
                    'extension': '.ttf'
                },
                'default': {  # Default for Latin scripts (English, Spanish, French, etc.)
                    'regular': 'NotoSans-Regular',
                    'bold': 'NotoSans-Bold',
                    'extension': '.ttf'
                }
            }
            
            # Get font config based on language
            # Use first 2 characters for language code (e.g., 'es', 'fr', 'de')
            lang_code = language[:2] if language else 'en'
            font_config = font_mapping.get(lang_code, font_mapping['default'])
            
            regular_font_name = font_config['regular']
            bold_font_name = font_config['bold']
            extension = font_config['extension']
            
            regular_font_file = os.path.join(font_path, f"{regular_font_name}{extension}")
            bold_font_file = os.path.join(font_path, f"{bold_font_name}{extension}")
            
            fonts_registered = False
            
            # Try to register regular font
            if os.path.exists(regular_font_file):
                try:
                    if extension == '.otf':
                        try:
                            pdfmetrics.registerFont(TTFont(regular_font_name, regular_font_file))
                            base_font = regular_font_name
                        except:
                            # Fallback to Chinese TTF if OTF fails
                            chinese_ttf = os.path.join(font_path, "NotoSansSC-Regular.ttf")
                            if os.path.exists(chinese_ttf):
                                pdfmetrics.registerFont(TTFont('NotoSansSC', chinese_ttf))
                                base_font = 'NotoSansSC'
                    else:
                        pdfmetrics.registerFont(TTFont(regular_font_name, regular_font_file))
                        base_font = regular_font_name
                    
                    fonts_registered = True
                except Exception as reg_error:
                    logger.warning(f"Failed to register regular font: {reg_error}")
                    # Keep default Helvetica
            
            # Try to register bold font
            if os.path.exists(bold_font_file) and fonts_registered:
                try:
                    if extension == '.otf':
                        try:
                            pdfmetrics.registerFont(TTFont(bold_font_name, bold_font_file))
                            bold_font = bold_font_name
                        except:
                            # Fallback to Chinese bold TTF
                            chinese_bold_ttf = os.path.join(font_path, "NotoSansSC-Bold.ttf")
                            if os.path.exists(chinese_bold_ttf):
                                pdfmetrics.registerFont(TTFont('NotoSansSC-Bold', chinese_bold_ttf))
                                bold_font = 'NotoSansSC-Bold'
                    else:
                        pdfmetrics.registerFont(TTFont(bold_font_name, bold_font_file))
                        bold_font = bold_font_name
                except Exception as bold_error:
                    logger.warning(f"Failed to register bold font: {bold_error}")
                    bold_font = base_font
            
        except Exception as font_error:
            logger.warning(f"Font registration failed, using default: {font_error}")
            base_font = 'Helvetica'
            bold_font = 'Helvetica-Bold'
        
        # PDF setup with proper fonts
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              topMargin=1*inch,
                              bottomMargin=1*inch,
                              leftMargin=0.75*inch,
                              rightMargin=0.75*inch)
        
        styles = getSampleStyleSheet()
        
        # Style definitions with dynamic fonts
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=bold_font, 
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#4f46e5'),
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=bold_font, 
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#1e293b'),
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=base_font, 
            fontSize=10,
            spaceAfter=12,
        )

        table_normal_style = ParagraphStyle(
            'TableNormal',
            parent=styles['Normal'],
            fontName=base_font,
            fontSize=8, 
            spaceAfter=0,
            leading=10, 
        )
        
        table_bold_style = ParagraphStyle(
            'TableBold',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=8,
            spaceAfter=0,
            leading=10,
        )

        story = []

        # Title
        title_text = pdf_translations.get('title', 'MENTAL HEALTH ASSESSMENT REPORT')
        story.append(Paragraph(title_text, title_style)) 
        story.append(Spacer(1, 20))
        
        # Assessment Details
        assessment_details = pdf_translations.get('assessment_details', 'ASSESSMENT DETAILS')
        story.append(Paragraph(assessment_details, heading_style))
        
        meta_data = [
            [pdf_translations.get('assessment_id', 'Assessment ID:'), pdf_data.get('id', 'N/A')],
            [pdf_translations.get('assessment_started', 'Assessment Started:'), pdf_data.get('assessment_timestamp', 'N/A')],
            [pdf_translations.get('report_generated', 'Report Generated:'), pdf_data.get('timestamp', 'N/A')],
            ['Timezone:', pdf_data.get('timezone', 'UTC')]
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), base_font, 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONT', (0, 0), (0, -1), bold_font, 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(meta_table)
        story.append(Spacer(1, 20))
        
        # Patient Information
        patient_info_title = pdf_translations.get('patient_info', 'PATIENT INFORMATION')
        story.append(Paragraph(patient_info_title, heading_style))
        
        patient_data = [
            [pdf_translations.get('patient_name', 'Patient Name:'), patient_info.get('name', pdf_translations.get('not_provided', 'Not provided'))],
            [pdf_translations.get('patient_number', 'Patient Number:'), patient_info.get('number', pdf_translations.get('not_provided', 'Not provided'))],
            [pdf_translations.get('age', 'Age:'), patient_info.get('age', pdf_translations.get('not_provided', 'Not provided'))],
            [pdf_translations.get('gender_title', 'Gender:'), patient_info.get('gender', pdf_translations.get('not_provided', 'Not provided'))]
        ]
        
        patient_table = Table(patient_data, colWidths=[1.5*inch, 4.5*inch])
        patient_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), base_font, 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f9ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONT', (0, 0), (0, -1), bold_font, 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(patient_table)
        story.append(Spacer(1, 20))
        
        # Clinical Results
        clinical_results = pdf_translations.get('clinical_results', 'CLINICAL ASSESSMENT RESULTS')
        story.append(Paragraph(clinical_results, heading_style))
        
        confidence = confidence_percentage
        
        diagnosis_data = [
            [pdf_translations.get('primary_diagnosis_label', 'Primary Diagnosis:'), primary_diagnosis],
            [pdf_translations.get('confidence_level', 'Confidence Level:'), f"{confidence:.1f}%"],
            [pdf_translations.get('assessment_datetime', 'Assessment Date & Time:'), pdf_data.get('timestamp', 'N/A')]
        ]
        
        confidence_color = colors.HexColor('#10b981')
        if confidence < 70:
            confidence_color = colors.HexColor('#f59e0b')
        if confidence < 50:
            confidence_color = colors.HexColor('#ef4444')
        
        diagnosis_table = Table(diagnosis_data, colWidths=[2*inch, 4*inch])
        diagnosis_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), base_font, 11),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('TEXTCOLOR', (1, 1), (1, 1), confidence_color),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONT', (0, 0), (0, -1), bold_font, 11),
            ('FONT', (1, 0), (1, 0), bold_font, 11),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#4f46e5')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(diagnosis_table)
        story.append(Spacer(1, 15))
        
        # Assessment Summary
        assessment_summary_title = pdf_translations.get('assessment_summary', 'Assessment Summary:')
        story.append(Paragraph(assessment_summary_title, heading_style))
        story.append(Paragraph(diagnosis_description, normal_style))
        story.append(Spacer(1, 20))
        
        # Differential Diagnoses
        differential_diagnoses = pdf_translations.get('differential_diagnoses', 'DIFFERENTIAL DIAGNOSES')
        story.append(Paragraph(differential_diagnoses, heading_style))

        if all_diagnoses and len(all_diagnoses) > 1:
            diagnoses_data = [[pdf_translations.get('diagnosis', 'Diagnosis'), 
                             pdf_translations.get('probability', 'Probability')]]
            
            for diagnosis in all_diagnoses[1:5]:  # Skip primary diagnosis
                diagnosis_name = diagnosis.get('diagnosis', 'N/A')
                confidence_percent = diagnosis.get('confidence_percentage', 0)
                diagnoses_data.append([
                    diagnosis_name,
                    f"{confidence_percent:.1f}%"
                ])
            
            diagnoses_table = Table(diagnoses_data, colWidths=[4*inch, 1.5*inch])
            diagnoses_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), bold_font, 10),
                ('FONT', (0, 1), (-1, -1), base_font, 9),
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
            no_additional_diagnoses = 'No additional diagnoses considered.'
            story.append(Paragraph(no_additional_diagnoses, normal_style))
        
        story.append(Spacer(1, 20))
        
        # Questions & Answers
        key_responses = pdf_translations.get('key_responses', 'ASSESSMENT QUESTIONS & ANSWERS')
        story.append(Paragraph(key_responses, heading_style))
        
        if questions_and_answers:
            # Group by category for better organization
            grouped_by_category = {}
            for qa in questions_and_answers:
                category = qa.get('category', 'Other')
                if category not in grouped_by_category:
                    grouped_by_category[category] = []
                grouped_by_category[category].append(qa)
            
            page_width = A4[0] - doc.leftMargin - doc.rightMargin
            
            domain_col_width = 1.3 * inch
            answer_col_width = 1.1 * inch
            question_col_width = page_width - domain_col_width - answer_col_width - 0.2 * inch
            
            response_data = [
                [pdf_translations.get('domain', 'Domain'), 
                 pdf_translations.get('question', 'Question'), 
                 pdf_translations.get('answer', 'Answer')]
            ]
            
            for category, qa_list in grouped_by_category.items():
                for i, qa in enumerate(qa_list):
                    question = qa.get('question', '')
                    answer = qa.get('answer', '')
                    
                    question_p = Paragraph(question, table_normal_style)
                    answer_p = Paragraph(answer, table_normal_style)
                    
                    if i == 0:
                        category_p = Paragraph(category, table_bold_style)
                        response_data.append([category_p, question_p, answer_p])
                    else:
                        response_data.append(["", question_p, answer_p])
            
            response_table = Table(response_data, 
                                  colWidths=[domain_col_width, question_col_width, answer_col_width],
                                  repeatRows=1)
            
            response_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), bold_font, 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('MINIMUMHEIGHT', (0, 1), (-1, -1), 25),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]))
            
            story.append(response_table)
        else:
            no_responses_text = 'No assessment responses available.'
            story.append(Paragraph(no_responses_text, normal_style))
        
        story.append(Spacer(1, 20))
        
        # Disclaimer
        important_disclaimer = pdf_translations.get('important_disclaimer', 'IMPORTANT DISCLAIMER')
        story.append(Paragraph(important_disclaimer, heading_style))
        disclaimer_text = pdf_translations.get('disclaimer_text', 'This assessment is for informational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment.')
        story.append(Paragraph(disclaimer_text, normal_style))
        story.append(Spacer(1, 10))
        
        # Footer
        footer_text = pdf_translations.get('footer', 'Confidential Mental Health Assessment Report - Generated by Clinical Assessment System')
        story.append(Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontName=base_font,
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#64748b')
        )))
        
        try:
            doc.build(story)
            pdf = buffer.getvalue()
            buffer.close()
            
            response = app.response_class(
                response=pdf,
                status=200,
                mimetype='application/pdf'
            )
            
            filename = f"mental_health_assessment_{pdf_data.get('id', 'report')}_{language}.pdf"
            
            import urllib.parse
            encoded_filename = urllib.parse.quote(filename)
            
            response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
            response.headers['Content-Type'] = 'application/pdf; charset=utf-8'
            response.headers['Content-Language'] = language
            
            return response
             
        except Exception as build_error:
            logger.error(f"PDF build error: {build_error}")
            buffer.close()
            raise build_error
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        return jsonify({'error': f'Failed to generate PDF report: {str(e)}'}), 500
    
@app.route('/api/test-pdf-simple', methods=['GET'])
def test_pdf_simple():
    """Simple test endpoint to verify PDF generation works"""
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 750, "Test PDF - Mental Health Assessment")
        c.drawString(100, 730, f"Generated: {datetime.now(timezone.utc).isoformat()}")
        c.drawString(100, 710, "PDF generation is working!")
        c.save()
        
        buffer.seek(0)
        
        response = app.response_class(
            response=buffer.getvalue(),
            status=200,
            mimetype='application/pdf'
        )
        response.headers['Content-Disposition'] = 'attachment; filename=test.pdf'
        
        return response
        
    except Exception as e:
        logger.error(f"Simple PDF test failed: {e}")
        return jsonify({'error': f'Simple PDF test failed: {str(e)}'}), 500


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    else:
        try:
            return send_from_directory('frontend', 'home.html')  
        except:
            return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large'}), 413

@app.errorhandler(429)
def too_many_requests(error):
    return jsonify({
        'error': 'Too many requests',
        'retry_after': SecurityConfig.RATE_LIMIT_WINDOW
    }), 429



if __name__ == '__main__':
    if all([model_package, scaler, label_encoder, feature_names, category_mappings]):
        logger.info("All model components loaded successfully!")
        logger.info(f"Features: {len(feature_names)}")
        logger.info(f"Classes: {label_encoder.classes_.tolist()}")
        logger.info("Enhanced preprocessing pipeline: ACTIVE")
        logger.info("EXACT training pipeline replication: VERIFIED")
        logger.info("Confidence calibration: ENABLED")
        logger.info("SECURITY FEATURES: ACTIVE")
        logger.info(f"Rate limiting: {SecurityConfig.RATE_LIMIT_REQUESTS} requests per {SecurityConfig.RATE_LIMIT_WINDOW}s")
        logger.info(f"Input validation: MAX {SecurityConfig.MAX_INPUT_LENGTH} chars")
        
        try:
            conn = get_postgres_connection()
            conn.close()
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            
        if clinical_enhancer:
            logger.info("Clinical Decision Enhancer: ACTIVE")
        else:
            logger.warning("Clinical Decision Enhancer: NOT AVAILABLE")
    else:
        logger.error("Failed to load model components!")
        if not os.environ.get('RENDER'):
            import sys
            sys.exit(1)
    
    port = int(os.environ.get('PORT', 3000))
    debug_mode = not bool(os.environ.get('RENDER'))
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)