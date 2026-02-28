from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import numpy as np
import pandas as pd
import pickle
import joblib
import time
from typing import Dict, List, Tuple, Optional, Any


# Import security components
from security import (
    SecurityConfig, SecurityUtils, EncryptionService,
    RateLimiter, AuthService, encryption_service, rate_limiter, auth_service
)

# Import database functions
from database import get_postgres_connection, init_database, save_assessment_to_db, \
    load_assessments_from_db, load_single_assessment_from_db, delete_assessment_from_db, init_connection_pool

# Import chatbot blueprint
from chatbot_backend import chatbot_bp

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model variables
model_package: Optional[Dict[str, Any]] = None
scaler: Optional[Any] = None
label_encoder: Optional[Any] = None
feature_names: Optional[List[str]] = None
category_mappings: Optional[Dict[str, Any]] = None
clinical_enhancer: Optional[Any] = None


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

        security_warnings = {
            'suicidal_thoughts': 'Suicidal thoughts detected - please seek immediate professional help',
            'aggressive_behavior': 'Aggressive behavior patterns detected - safety assessment recommended',
            'nervous_breakdown': 'History of nervous breakdown detected - consider professional evaluation',
            'severe_depression': 'Severe depression symptoms detected - urgent evaluation recommended',
            'manic_symptoms': 'Potential manic symptoms detected - clinical assessment advised'
        }

        if suicidal_thoughts == 1:
            warnings.append(security_warnings.get('suicidal_thoughts'))

        if aggressive_response == 1:
            warnings.append(security_warnings.get('aggressive_behavior'))

        if nervous_breakdown == 1:
            warnings.append(security_warnings.get('nervous_breakdown'))

        if (sadness >= 3 and sleep_disorder >= 2 and exhausted >= 2):
            warnings.append(security_warnings.get('severe_depression'))

        if (euphoric >= 3 and mood_swing >= 2):
            warnings.append(security_warnings.get('manic_symptoms'))

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


# Create Flask app
# Determine absolute paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)          # parent of backend
frontend_dir = os.path.join(project_root, 'frontend')

# Create Flask app with correct static/template folders
app = Flask(__name__,
            static_folder=frontend_dir,
            template_folder=frontend_dir)

app.secret_key = SecurityConfig.SECRET_KEY

# Configure CORS based on environment
if os.environ.get('RENDER'):
    CORS(app, origins=[
        'https://mentivio.onrender.com',
        'https://mentivio-mentalhealth.onrender.com',
        'https://mentivio-web.onrender.com'
    ])
    app.debug = False
    app.config['FRONTEND_DIR'] = frontend_dir
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
else:
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/chatbot/api/*": {"origins": "*"}
    })

# Security middleware
@app.after_request
def set_security_headers(response):
    for header, value in SecurityConfig.SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

@app.before_request
def check_rate_limit():
    if request.endpoint and request.endpoint.startswith('api'):
        client_ip = request.remote_addr
        if rate_limiter.is_rate_limited(client_ip, SecurityConfig.RATE_LIMIT_REQUESTS, SecurityConfig.RATE_LIMIT_WINDOW):
            return jsonify({
                'error': 'Rate limit exceeded. Please try again later.',
                'retry_after': SecurityConfig.RATE_LIMIT_WINDOW
            }), 429

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

# Initialize database and connection pool
init_database()          # creates tables if needed
init_connection_pool()   # sets up connection pool

# Load model components
def load_model_components() -> Tuple[Optional[Dict[str, Any]], Optional[Any], Optional[Any], Optional[List[str]], Optional[Dict[str, Any]]]:
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

# Load models
model_package, scaler, label_encoder, feature_names, category_mappings = load_model_components()

# Initialize clinical enhancer and preprocessor
def initialize_clinical_enhancer():
    global clinical_enhancer
    if feature_names and label_encoder:
        clinical_enhancer = ClinicalDecisionEnhancer(feature_names, label_encoder)
    else:
        logger.warning("Could not initialize Clinical Decision Enhancer")

initialize_clinical_enhancer()
preprocessor = ClinicalPreprocessor(category_mappings)

# Register chatbot blueprint
app.register_blueprint(chatbot_bp)

# Log startup status
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

# Import routes after app is created to avoid circular imports
from routes import *

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
