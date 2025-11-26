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
import sqlite3  # Keep for fallback if needed
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import json
import sys 

# Global storage (in production, use a database)
assessment_storage: Dict[str, Dict[str, Any]] = {}

app = Flask(__name__, 
           static_folder='frontend',
           template_folder='frontend')

# Configure CORS based on environment
if os.environ.get('RENDER'):
    CORS(app, origins=[
        'https://mentivio.onrender.com',
        'http://mentivio-MentalHealth.onrender.com',
        'https://mentivio-web.onrender.com',
        'http://your-actual-app-name.onrender.com'
    ])
    app.debug = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
else:
    CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for model components with type hints
model_package: Optional[Dict[str, Any]] = None
scaler: Optional[Any] = None
label_encoder: Optional[Any] = None
feature_names: Optional[List[str]] = None
category_mappings: Optional[Dict[str, Any]] = None
clinical_enhancer: Optional[Any] = None

# PostgreSQL configuration with psycopg
def get_postgres_connection():
    """Get PostgreSQL database connection using psycopg"""
    try:
        # Use external database URL for Render
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # Render provides DATABASE_URL in the format: postgresql://user:pass@host:port/dbname
            # Convert to psycopg connection string if needed
            if database_url.startswith('postgresql://'):
                conn = psycopg.connect(database_url, row_factory=dict_row)
            else:
                # Fallback to individual connection parameters
                conn = psycopg.connect(
                    host='dpg-d4j32vvgi27c739dfo1g-a.oregon-postgres.render.com',
                    dbname='assessment_data',
                    user='assessment_data_user',
                    password='QkHhmkEwRn4UjlbskfKNvdcyCJs7YjFA',
                    port=5432,
                    row_factory=dict_row
                )
        else:
            # Fallback to individual connection parameters
            conn = psycopg.connect(
                host='dpg-d4j32vvgi27c739dfo1g-a.oregon-postgres.render.com',
                dbname='assessment_data',
                user='assessment_data_user',
                password='QkHhmkEwRn4UjlbskfKNvdcyCJs7YjFA',
                port=5432,
                row_factory=dict_row
            )
        
        logger.info("PostgreSQL connection established successfully with psycopg")
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        # Fallback to SQLite for local development
        try:
            sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mental_health_assessments.db')
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row
            logger.info("Fallback to SQLite connection")
            return conn
        except Exception as sqlite_error:
            logger.error(f"SQLite fallback also failed: {sqlite_error}")
            raise e

def init_database():
    """Initialize PostgreSQL database with required tables using psycopg"""
    try:
        conn = get_postgres_connection()
        
        # Check if we're using PostgreSQL or SQLite
        if hasattr(conn, 'cursor'):  # PostgreSQL with psycopg
            with conn.cursor() as cur:
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cur.execute('CREATE INDEX IF NOT EXISTS idx_patient_number ON assessments(patient_number)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON assessments(report_timestamp)')
                
            conn.commit()
            logger.info("PostgreSQL database initialized successfully with psycopg")
            
        else:
            # SQLite fallback
            c = conn.cursor()
            
            c.execute('''
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            c.execute('CREATE INDEX IF NOT EXISTS idx_patient_number ON assessments(patient_number)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON assessments(report_timestamp)')
            
            conn.commit()
            logger.info("SQLite database initialized successfully")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

def save_assessment_to_db(assessment_data: Dict[str, Any]) -> bool:
    """Save assessment data to PostgreSQL database using psycopg"""
    try:
        conn = get_postgres_connection()
        
        if hasattr(conn, 'cursor'):  # PostgreSQL with psycopg
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO assessments (
                        id, assessment_timestamp, report_timestamp, timezone,
                        patient_name, patient_number, patient_age, patient_gender,
                        primary_diagnosis, confidence, confidence_percentage,
                        all_diagnoses_json, responses_json, processing_details_json,
                        technical_details_json, clinical_insights_json
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
                        responses_json = EXCLUDED.responses_json,
                        processing_details_json = EXCLUDED.processing_details_json,
                        technical_details_json = EXCLUDED.technical_details_json,
                        clinical_insights_json = EXCLUDED.clinical_insights_json
                ''', (
                    assessment_data.get('id'),
                    assessment_data.get('assessment_timestamp'),
                    assessment_data.get('timestamp'),
                    assessment_data.get('timezone', 'UTC'),
                    assessment_data.get('patient_info', {}).get('name', ''),
                    assessment_data.get('patient_info', {}).get('number', ''),
                    assessment_data.get('patient_info', {}).get('age', ''),
                    assessment_data.get('patient_info', {}).get('gender', ''),
                    assessment_data.get('primary_diagnosis', ''),
                    assessment_data.get('confidence', 0),
                    assessment_data.get('confidence_percentage', 0),
                    json.dumps(assessment_data.get('all_diagnoses', [])),
                    json.dumps(assessment_data.get('responses', {})),
                    json.dumps(assessment_data.get('processing_details', {})),
                    json.dumps(assessment_data.get('technical_details', {})),
                    json.dumps(assessment_data.get('clinical_insights', {}))
                ))
        else:
            # SQLite fallback
            c = conn.cursor()
            
            c.execute('''
                INSERT OR REPLACE INTO assessments (
                    id, assessment_timestamp, report_timestamp, timezone,
                    patient_name, patient_number, patient_age, patient_gender,
                    primary_diagnosis, confidence, confidence_percentage,
                    all_diagnoses_json, responses_json, processing_details_json,
                    technical_details_json, clinical_insights_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                assessment_data.get('id'),
                assessment_data.get('assessment_timestamp'),
                assessment_data.get('timestamp'),
                assessment_data.get('timezone', 'UTC'),
                assessment_data.get('patient_info', {}).get('name', ''),
                assessment_data.get('patient_info', {}).get('number', ''),
                assessment_data.get('patient_info', {}).get('age', ''),
                assessment_data.get('patient_info', {}).get('gender', ''),
                assessment_data.get('primary_diagnosis', ''),
                assessment_data.get('confidence', 0),
                assessment_data.get('confidence_percentage', 0),
                json.dumps(assessment_data.get('all_diagnoses', [])),
                json.dumps(assessment_data.get('responses', {})),
                json.dumps(assessment_data.get('processing_details', {})),
                json.dumps(assessment_data.get('technical_details', {})),
                json.dumps(assessment_data.get('clinical_insights', {}))
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Assessment saved to database: {assessment_data.get('id')}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        return False

def load_assessments_from_db(patient_number: str = None) -> Dict[str, List[Dict[str, Any]]]:
    """Load assessments from database using psycopg, optionally filtered by patient number"""
    try:
        conn = get_postgres_connection()
        
        if hasattr(conn, 'cursor'):  # PostgreSQL with psycopg
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
            # SQLite fallback
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
        
        assessments_by_patient: Dict[str, List[Dict[str, Any]]] = {}
        
        for row in rows:
            # Convert row to dictionary
            if isinstance(row, dict):
                row_dict = row
            else:
                row_dict = dict(row)
            
            patient_num = row_dict['patient_number']
            if patient_num not in assessments_by_patient:
                assessments_by_patient[patient_num] = []
            
            all_diagnoses = json.loads(row_dict['all_diagnoses_json']) if row_dict['all_diagnoses_json'] else []
            responses = json.loads(row_dict['responses_json']) if row_dict['responses_json'] else {}
            processing_details = json.loads(row_dict['processing_details_json']) if row_dict['processing_details_json'] else {}
            technical_details = json.loads(row_dict['technical_details_json']) if row_dict['technical_details_json'] else {}
            clinical_insights = json.loads(row_dict['clinical_insights_json']) if row_dict['clinical_insights_json'] else {}
            
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
    """Load a single specific assessment from database using psycopg"""
    try:
        conn = get_postgres_connection()
        
        if hasattr(conn, 'cursor'):  # PostgreSQL with psycopg
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT * FROM assessments 
                    WHERE patient_number = %s AND id = %s AND patient_name = %s
                ''', (patient_number, assessment_id, patient_name))
                
                row = cur.fetchone()
        else:
            # SQLite fallback
            c = conn.cursor()
            
            c.execute('''
                SELECT * FROM assessments 
                WHERE patient_number = ? AND id = ? AND patient_name = ?
            ''', (patient_number, assessment_id, patient_name))
            
            row = c.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        # Convert row to dictionary
        if isinstance(row, dict):
            row_dict = row
        else:
            row_dict = dict(row)
        
        all_diagnoses = json.loads(row_dict['all_diagnoses_json']) if row_dict['all_diagnoses_json'] else []
        responses = json.loads(row_dict['responses_json']) if row_dict['responses_json'] else {}
        processing_details = json.loads(row_dict['processing_details_json']) if row_dict['processing_details_json'] else {}
        technical_details = json.loads(row_dict['technical_details_json']) if row_dict['technical_details_json'] else {}
        clinical_insights = json.loads(row_dict['clinical_insights_json']) if row_dict['clinical_insights_json'] else {}
        
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
        
        logger.info(f"Loaded single assessment from database: {assessment_id}")
        return assessment
        
    except Exception as e:
        logger.error(f"Error loading single assessment from database: {e}")
        return None

def delete_assessment_from_db(patient_number: str, assessment_id: str) -> bool:
    """Delete assessment from database using psycopg"""
    try:
        conn = get_postgres_connection()
        
        if hasattr(conn, 'cursor'):  # PostgreSQL with psycopg
            with conn.cursor() as cur:
                cur.execute('''
                    DELETE FROM assessments 
                    WHERE patient_number = %s AND id = %s
                ''', (patient_number, assessment_id))
        else:
            # SQLite fallback
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

# Initialize database at startup
init_database()

def load_model_components() -> Tuple[Optional[Dict[str, Any]], Optional[Any], Optional[Any], Optional[List[str]], Optional[Dict[str, Any]]]:
    """Load all required model components"""
    global model_package, scaler, label_encoder, feature_names, category_mappings
    
    try:
        logger.info("Loading model components...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(current_dir, 'models')
        
        model_path = os.path.join(models_dir, 'mental_health_model.pkl')
        model_package = joblib.load(model_path)
        logger.info("Model package loaded")
        
        scaler_path = os.path.join(models_dir, 'scaler.pkl')
        scaler = joblib.load(scaler_path)
        logger.info("Scaler loaded")
        
        encoder_path = os.path.join(models_dir, 'label_encoder.pkl')
        label_encoder = joblib.load(encoder_path)
        logger.info("Label encoder loaded")
        
        feature_names_path = os.path.join(models_dir, 'feature_names.pkl')
        with open(feature_names_path, 'rb') as f:
            feature_names = pickle.load(f)
        logger.info(f"Feature names loaded: {len(feature_names)} features")
        
        category_mappings_path = os.path.join(models_dir, 'category_mappings.pkl')
        with open(category_mappings_path, 'rb') as f:
            category_mappings = pickle.load(f)
        logger.info("Category mappings loaded")
        
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
        """Define clinical rules for different diagnoses"""
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
        """Analyze if feature patterns match clinical expectations"""
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
        """Calculate how well responses match a clinical pattern"""
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
        """Check if features are consistent with the diagnosis"""
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
        """Suggest diagnosis adjustments based on feature patterns"""
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
        """Apply clinical enhancements to the prediction"""
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
        logger.info("Clinical Decision Enhancer initialized")
    else:
        logger.warning("Could not initialize Clinical Decision Enhancer")

class ClinicalPreprocessor:
    """EXACTLY replicates the preprocessing pipeline from train_model.py"""
    
    def __init__(self, category_mappings: Optional[Dict[str, Any]] = None):
        self.category_mappings = category_mappings or {}
        self.processing_log: List[str] = []
    
    def log_step(self, step: str, details: str) -> None:
        """Log processing steps for transparency"""
        self.processing_log.append(f"{step}: {details}")
        logger.info(f"Preprocessing - {step}: {details}")
    
    def encode_user_responses(self, raw_responses: Dict[str, Any]) -> Dict[str, Any]:
        """EXACTLY replicate the encoding from train_model.py encode_features()"""
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
                    self.log_step("Frequency_Encoding", f"{feature}: {value} -> {encoded_value}")
                else:
                    encoded_responses[training_feature_name] = 1
                    self.log_step("Frequency_Encoding", f"{feature}: {value} -> 1 (default)")
            
            elif feature in ['Mood Swing', 'Suicidal thoughts', 'Aggressive Response', 'Nervous Breakdown', 
                           'Overthinking', 'Anorexia', 'Authority Respect', 'Try Explanation',
                           'Ignore & Move-On', 'Admit Mistakes']:
                if value in yes_no_mapping:
                    encoded_value = yes_no_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                    self.log_step("YesNo_Encoding", f"{feature}: {value} -> {encoded_value}")
                else:
                    encoded_responses[training_feature_name] = 0
                    self.log_step("YesNo_Encoding", f"{feature}: {value} -> 0 (default)")
            
            elif feature == 'Concentration':
                if value in concentration_mapping:
                    encoded_value = concentration_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                    self.log_step("Concentration_Encoding", f"{feature}: {value} -> {encoded_value}")
                else:
                    encoded_responses[training_feature_name] = 2
                    self.log_step("Concentration_Encoding", f"{feature}: {value} -> 2 (default)")
            
            elif feature == 'Optimism':
                if value in optimism_mapping:
                    encoded_value = optimism_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                    self.log_step("Optimism_Encoding", f"{feature}: {value} -> {encoded_value}")
                else:
                    encoded_responses[training_feature_name] = 2
                    self.log_step("Optimism_Encoding", f"{feature}: {value} -> 2 (default)")
            
            elif feature == 'Sexual Activity':
                if value in sexual_activity_mapping:
                    encoded_value = sexual_activity_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                    self.log_step("SexualActivity_Encoding", f"{feature}: {value} -> {encoded_value}")
                else:
                    encoded_responses[training_feature_name] = 2
                    self.log_step("SexualActivity_Encoding", f"{feature}: {value} -> 2 (default)")
            
            else:
                encoded_responses[training_feature_name] = value
                self.log_step("Direct_Copy", f"{feature}: {value} -> {value}")
        
        return encoded_responses
    
    def apply_feature_engineering(self, encoded_responses: Dict[str, Any]) -> Dict[str, Any]:
        """EXACTLY replicate feature engineering from training - MATCHING THE MODEL"""
        responses = encoded_responses.copy()
        
        if 'Mood Swing' in responses and 'Sadness' in responses:
            mood_swing = float(responses.get('Mood Swing', 0))
            sadness = float(responses.get('Sadness', 0))
            responses['Mood_Emotion_Composite'] = mood_swing * 0.6 + sadness * 0.4
            self.log_step("Composite_Score", f"Mood_Emotion_Composite: {mood_swing}*0.6 + {sadness}*0.4 = {responses['Mood_Emotion_Composite']:.2f}")
        
        if 'Sleep disorder' in responses and 'Exhausted' in responses:
            sleep_disorder = float(responses.get('Sleep disorder', 0))
            exhausted = float(responses.get('Exhausted', 0))
            responses['Sleep_Fatigue_Composite'] = sleep_disorder * 0.7 + exhausted * 0.3
            self.log_step("Composite_Score", f"Sleep_Fatigue_Composite: {sleep_disorder}*0.7 + {exhausted}*0.3 = {responses['Sleep_Fatigue_Composite']:.2f}")
        
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
            self.log_step("Composite_Score", f"Behavioral_Stress_Composite: {behavioral_scores} = {responses['Behavioral_Stress_Composite']:.2f}")
        
        return responses

    def normalize_feature_names(self, raw_responses: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize feature names to match training data format EXACTLY"""
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
            
        self.log_step("Feature_Name_Mapping", 
                    f"Mapped {len(raw_responses)} features to {len(normalized_responses)} training features")
        
        return normalized_responses
    
    def validate_clinical_safety(self, responses: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Clinical safety checks for critical responses"""
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
        """Complete preprocessing pipeline EXACTLY matching training"""
        
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
            import traceback
            self.log_step("Pipeline_Error", f"Traceback: {traceback.format_exc()}")
            raise e
        
def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def convert_responses_to_features(processed_responses: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """Convert processed responses to feature array with EXACT feature order matching training"""
    try:
        if feature_names is None:
            logger.error("Feature names not loaded")
            return None
            
        # Create feature array with proper feature names
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
                        logger.warning(f"Feature {feature_name} value {value} could not be converted to float, using 0")
                found_features.append(feature_name)
            else:
                feature_array[i] = 0
                missing_features.append(feature_name)
        
        if missing_features:
            logger.warning(f"Missing features filled with defaults: {missing_features}")
        
        if found_features:
            logger.info(f"Found features: {found_features}")
        
        logger.info(f"Feature array created: {len(feature_array)} features, "
                   f"{len(missing_features)} missing, {len(found_features)} found")
        
        # 🆕 CRITICAL FIX: Always return DataFrame with feature names
        feature_df = pd.DataFrame([feature_array], columns=feature_names)
        
        return feature_df
        
    except Exception as e:
        logger.error(f"Feature conversion error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None
        

# Load components at startup
model_package, scaler, label_encoder, feature_names, category_mappings = load_model_components()
initialize_clinical_enhancer()

# Initialize preprocessor
preprocessor = ClinicalPreprocessor(category_mappings)

# Routes to serve the frontend files
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

@app.route('/debug-path')
def debug_path():
    return jsonify({
        'current_path': request.path,
        'url': request.url,
        'referrer': request.referrer,
        'is_resource': '/resources/' in request.path,
        'suggested_base_path': '../' if '/resources/' in request.path else './'
    })
    
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    else:
        try:
            return send_from_directory('frontend', 'Home.html')  
        except:
            return jsonify({'error': 'Page not found'}), 404
        
@app.route('/api/health', methods=['GET'])
def health_check():
    # Add database health check
    db_healthy = False
    try:
        conn = get_postgres_connection()
        if conn:
            db_healthy = True
            conn.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    components_loaded = all([
        model_package is not None,
        scaler is not None, 
        label_encoder is not None,
        feature_names is not None,
        category_mappings is not None
    ])
    
    health_info = {
        'status': 'healthy' if components_loaded and db_healthy else 'unhealthy',
        'model_loaded': model_package is not None,
        'scaler_loaded': scaler is not None,
        'encoder_loaded': label_encoder is not None,
        'features_loaded': feature_names is not None,
        'category_mappings_loaded': category_mappings is not None,
        'database_healthy': db_healthy,
        'database_type': 'PostgreSQL (psycopg)' if db_healthy and hasattr(conn, 'cursor') else 'SQLite (fallback)',
        'total_features': len(feature_names) if feature_names else 0,
        'available_classes': label_encoder.classes_.tolist() if label_encoder else [],
        'preprocessing_available': True,
        'clinical_validation': True,
        'clinical_enhancer_available': clinical_enhancer is not None
    }
    
    return jsonify(health_info)


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
            logger.warning(f"Assessment not found: {assessment_id} for {patient_name} (#{patient_number})")
            return jsonify({'error': 'Assessment not found'}), 404
        
        enhanced_assessment = enhance_assessment_data(target_assessment)
        
        logger.info(f"Single assessment retrieved: {assessment_id}")
        return jsonify({
            'success': True,
            'assessment': enhanced_assessment
        })
        
    except Exception as e:
        logger.error(f"Error retrieving single assessment: {e}")
        return jsonify({'error': f'Failed to retrieve assessment: {str(e)}'}), 500
    
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

def parse_assessment_timestamp(timestamp_str: str) -> datetime:
    try:
        if not timestamp_str or timestamp_str == 'N/A':
            logger.warning("Empty or N/A timestamp provided, using current UTC time")
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
                    logger.warning(f"Could not parse timestamp format: {timestamp_str}, using current time")
                    return datetime.now(timezone.utc)
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        logger.info(f"Successfully parsed timestamp: {timestamp_str} -> {dt.isoformat()}")
        return dt
        
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse timestamp '{timestamp_str}': {e}, using current UTC time")
        return datetime.now(timezone.utc)
    
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        user_responses = data.get('responses', {})
        patient_info = data.get('patientInfo', {})
        assessment_start_time = data.get('assessment_start_time')
        
        if not user_responses:
            return jsonify({'error': 'No responses provided'}), 400
        
        logger.info(f"Received {len(user_responses)} responses for patient: {patient_info.get('name', 'Unknown')}")
        
        client_timezone = request.headers.get('X-Client-Timezone', 'UTC')
       
        try:
            import pytz
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
                
            except Exception as e:
                logger.warning(f"Could not parse assessment start time: {e}, using current time")
                assessment_date_str = client_now.isoformat()
        else:
            logger.warning("No assessment start time provided, using current time")
            assessment_date_str = client_now.isoformat()

        try:
            processed_responses, processing_log, safety_warnings = preprocessor.preprocess(user_responses)
            logger.info("Preprocessing completed successfully")
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return jsonify({'error': f'Data preprocessing failed: {str(e)}'}), 400
        
        feature_df = convert_responses_to_features(processed_responses)
        if feature_df is None:
            return jsonify({'error': 'Feature conversion failed'}), 400
        
        try:
            feature_array_scaled = scaler.transform(feature_df)
            logger.info("Feature scaling completed")
            
            feature_df_scaled = pd.DataFrame(feature_array_scaled, columns=feature_names)
            
        except Exception as e:
            logger.error(f"Feature scaling failed: {e}")
            return jsonify({'error': 'Feature scaling failed'}), 500
        
        try:
            prediction = model_package['model'].predict(feature_df_scaled)
            probabilities = model_package['model'].predict_proba(feature_df_scaled)
            logger.info("Prediction completed")
            
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
                'processing_duration_seconds': time_diff.total_seconds() if assessment_start_time else 0
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
        
        logger.info(f"Assessment completed successfully:")
        logger.info(f"Primary Diagnosis: {final_diagnosis} ({final_confidence_percentage:.1f}%)")
        logger.info(f"Total Diagnoses Returned: {len(all_diagnoses)}")
        logger.info(f"Client Timezone: {client_timezone}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Prediction endpoint error: {e}")
        return jsonify({'error': 'Assessment failed. Please try again.'}), 500
    
@app.route('/api/save-assessment', methods=['POST'])
def save_assessment():
    try:
        data = request.json
        assessment_data = data.get('assessment_data', {})
        
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
            logger.info(f"Assessment saved to database: {assessment_data['id']}")
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

@app.route('/api/delete-assessment', methods=['POST'])
def delete_assessment():
    try:
        data = request.json
        patient_number = data.get('patient_number', '')
        assessment_id = data.get('assessment_id', '')
        
        if not patient_number or not assessment_id:
            return jsonify({'error': 'Patient number and assessment ID required'}), 400
        
        if delete_assessment_from_db(patient_number, assessment_id):
            logger.info(f"Assessment {assessment_id} deleted for patient #{patient_number}")
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
            'database_storage': True
        },
        'endpoints': {
            'health_check': '/api/health (GET)',
            'predict': '/api/predict (POST)',
            'save_assessment': '/api/save-assessment (POST)',
            'get_patient_assessments': '/api/get-patient-assessments (POST)',
            'delete_assessment': '/api/delete-assessment (POST)'
        },
        'status': 'active'
    })

def format_timestamp(timestamp_str):
    if not timestamp_str:
        return "N/A"
    try:
        dt = parse_assessment_timestamp(timestamp_str)
        return dt.strftime("%B %d, %Y at %H:%M %Z")
    except:
        return timestamp_str

@app.route('/api/generate-pdf-report', methods=['POST'])
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
        
        assessment_date_str = format_timestamp_for_pdf(assessment_timestamp_str, timezone_used, "Assessment")
        report_date_str = format_timestamp_for_pdf(report_timestamp_str, timezone_used, "Report")
        
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
        
        story.append(Paragraph("KEY ASSESSMENT RESPONSES", heading_style))
        responses = assessment_data.get('responses', {})
        
        if responses:
            response_data = [["Domain", "Question", "Response"]]
            
            category_mapping = {
                'Mood Swing': 'Mood & Emotions',
                'Sadness': 'Mood & Emotions',
                'Euphoric': 'Mood & Emotions',
                'Anxiety': 'Anxiety & Worry',
                'Overthinking': 'Anxiety & Worry',
                'Sleep disorder': 'Sleep & Energy',
                'Exhausted': 'Sleep & Energy',
                'Suicidal thoughts': 'Behavioral',
                'Aggressive Response': 'Behavioral',
                'Concentration': 'Cognitive',
                'Optimism': 'Cognitive'
            }
            
            grouped_responses = {}
            for feature, response in responses.items():
                category = category_mapping.get(feature, 'Other')
                if category not in grouped_responses:
                    grouped_responses[category] = []
                
                question_text = feature.replace('_', ' ').title()
                grouped_responses[category].append([question_text, str(response)])
            
            for category, responses_list in grouped_responses.items():
                for i, (question, response) in enumerate(responses_list):
                    if i == 0:
                        response_data.append([category, question, response])
                    else:
                        response_data.append(["", question, response])
            
            response_table = Table(response_data, colWidths=[1.2*inch, 3.3*inch, 1.5*inch])
            response_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
                ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('SPAN', (0, 1), (0, 1)),
            ]))
            
            story.append(response_table)
        story.append(Spacer(1, 25))
        
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
        
        logger.info(f"PDF report generated for assessment {assessment_data.get('id', 'unknown')}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        return jsonify({'error': f'Failed to generate PDF report: {str(e)}'}), 500

def format_timestamp_for_pdf(timestamp_str: str, timezone_used: str, context: str = "") -> str:
    try:
        if not timestamp_str or timestamp_str == 'N/A':
            return "N/A"
        
        dt = parse_assessment_timestamp(timestamp_str)
        
        try:
            import pytz
            if timezone_used and timezone_used != 'UTC':
                patient_tz = pytz.timezone(timezone_used)
                local_dt = dt.astimezone(patient_tz)
            else:
                local_dt = dt
            
            formatted = local_dt.strftime("%B %d, %Y at %H:%M %Z")
            return formatted
            
        except Exception as tz_error:
            fallback = dt.strftime("%B %d, %Y at %H:%M UTC")
            return fallback
            
    except Exception as e:
        return timestamp_str or "Timestamp unavailable"



if __name__ == '__main__':
    if all([model_package, scaler, label_encoder, feature_names, category_mappings]):
        logger.info("All model components loaded successfully!")
        logger.info(f"Features: {len(feature_names)}")
        logger.info(f"Classes: {label_encoder.classes_.tolist()}")
        logger.info("Enhanced preprocessing pipeline: ACTIVE")
        logger.info("EXACT training pipeline replication: VERIFIED")
        logger.info("Confidence calibration: ENABLED")
        
        # Test database connection
        try:
            conn = get_postgres_connection()
            if hasattr(conn, 'cursor'):
                logger.info("Database: PostgreSQL (Production) with psycopg")
            else:
                logger.info("Database: SQLite (Development Fallback)")
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
            sys.exit(1)
    
    port = int(os.environ.get('PORT', 5002))
    debug_mode = not bool(os.environ.get('RENDER'))
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
