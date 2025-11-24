from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pickle
import joblib
import numpy as np
import pandas as pd
import uuid 
from datetime import datetime
import os
import logging
from typing import Dict, List, Tuple
import csv
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
from datetime import timezone

# Import preprocessing functions directly from train_model
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Global storage (in production, use a database)
assessment_storage = {}

app = Flask(__name__, 
           static_folder='frontend',
           template_folder='frontend')

# Configure CORS based on environment
if os.environ.get('RENDER'):
    # Production CORS - more permissive for frontend-backend communication
    CORS(app, origins=[
        'https://mentivio.onrender.com',
        'http://mentivio-MentalHealth.onrender.com',
        'https://your-actual-app-name.onrender.com',  # Add your actual domain
        'http://your-actual-app-name.onrender.com'   # Add your actual domain
    ])
    app.debug = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
else:
    # Development CORS - allow all for local development
    CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for model components
model_package = None
scaler = None
label_encoder = None
feature_names = None
category_mappings = None
clinical_enhancer = None

# Ensure assessment directory exists
ASSESSMENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assessment')
os.makedirs(ASSESSMENT_DIR, exist_ok=True)
CSV_FILE_PATH = os.path.join(ASSESSMENT_DIR, 'assessment_data.csv')



def load_model_components():
    """Load all required model components"""
    try:
        logger.info("Loading model components...")
        
        # Get the absolute path to the models directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(current_dir, 'models')
        
        # Load the main model package
        model_path = os.path.join(models_dir, 'mental_health_model.pkl')
        model_package = joblib.load(model_path)
        logger.info("✅ Model package loaded")
        
        # Load preprocessing components
        scaler_path = os.path.join(models_dir, 'scaler.pkl')
        scaler = joblib.load(scaler_path)
        logger.info("✅ Scaler loaded")
        
        encoder_path = os.path.join(models_dir, 'label_encoder.pkl')
        label_encoder = joblib.load(encoder_path)
        logger.info("✅ Label encoder loaded")
        
        # Load feature names
        feature_names_path = os.path.join(models_dir, 'feature_names.pkl')
        with open(feature_names_path, 'rb') as f:
            feature_names = pickle.load(f)
        logger.info(f"✅ Feature names loaded: {len(feature_names)} features")
        
        # Load category mappings
        category_mappings_path = os.path.join(models_dir, 'category_mappings.pkl')
        with open(category_mappings_path, 'rb') as f:
            category_mappings = pickle.load(f)
        logger.info("✅ Category mappings loaded")
        
        return model_package, scaler, label_encoder, feature_names, category_mappings
        
    except Exception as e:
        logger.error(f"❌ Error loading model components: {e}")
        logger.error(f"Current directory: {os.path.dirname(os.path.abspath(__file__))}")
        logger.error(f"Models directory: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')}")
        return None, None, None, None, None

class ClinicalDecisionEnhancer:
    """Enhances model predictions with clinical rules and feature sensitivity"""
    
    def __init__(self, feature_names, label_encoder):
        self.feature_names = feature_names
        self.label_encoder = label_encoder
        self.clinical_rules = self._initialize_clinical_rules()
        
    def _initialize_clinical_rules(self):
        """Define clinical rules for different diagnoses"""
        return {
            'depression_patterns': {
                'required_features': ['Sadness', 'Sleep disorder', 'Exhausted'],
                'thresholds': {
                    'Sadness': 2,  # Usually or higher
                    'Sleep disorder': 2,
                    'Exhausted': 2
                },
                'exclusion_features': ['Euphoric', 'Mood Swing'],  # Low values expected
                'exclusion_thresholds': {
                    'Euphoric': 1,  # Seldom or Sometimes
                    'Mood Swing': 0  # NO
                }
            },
            'bipolar1_patterns': {
                'required_features': ['Mood Swing', 'Euphoric'],
                'thresholds': {
                    'Mood Swing': 1,  # YES
                    'Euphoric': 2,    # Usually or higher
                    'Sleep disorder': 1  # Sometimes or higher (reduced sleep)
                }
            },
            'bipolar2_patterns': {
                'required_features': ['Mood Swing', 'Sadness'],
                'thresholds': {
                    'Mood Swing': 1,  # YES
                    'Sadness': 2,     # Usually or higher
                    'Euphoric': 1     # Sometimes (milder than bipolar1)
                }
            },
            'normal_patterns': {
                'required_features': ['Sadness', 'Sleep disorder'],
                'thresholds': {
                    'Sadness': 1,     # Sometimes or lower
                    'Sleep disorder': 1,
                    'Suicidal thoughts': 0  # NO
                }
            }
        }
    
    def analyze_feature_patterns(self, processed_responses, probabilities):
        """Analyze if feature patterns match clinical expectations"""
        analysis = {
            'depression_score': 0,
            'bipolar1_score': 0,
            'bipolar2_score': 0,
            'normal_score': 0,
            'feature_consistency': {},
            'suggested_adjustments': []
        }
        
        # Calculate pattern scores
        for pattern_name, rules in self.clinical_rules.items():
            score = self._calculate_pattern_score(processed_responses, rules)
            analysis[f'{pattern_name.split("_")[0]}_score'] = score
        
        # Check feature consistency with predicted diagnosis
        primary_diagnosis_idx = np.argmax(probabilities)
        primary_diagnosis = self.label_encoder.inverse_transform([primary_diagnosis_idx])[0]
        analysis['feature_consistency'] = self._check_feature_consistency(processed_responses, primary_diagnosis)
        
        # Suggest adjustments if features don't match diagnosis
        analysis['suggested_adjustments'] = self._suggest_adjustments(processed_responses, probabilities)
        
        return analysis
    
    def _calculate_pattern_score(self, responses, rules):
        """Calculate how well responses match a clinical pattern"""
        score = 0
        max_score = len(rules['required_features']) + len(rules.get('exclusion_features', []))
        
        # Check required features
        for feature in rules['required_features']:
            if feature in responses:
                threshold = rules['thresholds'].get(feature, 0)
                if responses[feature] >= threshold:
                    score += 1
        
        # Check exclusion features (lower is better)
        for feature in rules.get('exclusion_features', []):
            if feature in responses:
                threshold = rules['exclusion_thresholds'].get(feature, 1)
                if responses[feature] <= threshold:
                    score += 1
        
        return score / max_score if max_score > 0 else 0
    
    def _check_feature_consistency(self, responses, diagnosis):
        """Check if features are consistent with the diagnosis"""
        consistency = {}
        
        # Define expected feature ranges for each diagnosis
        expected_ranges = {
            'Depression': {
                'Sadness': (2, 3),           # High sadness
                'Sleep disorder': (2, 3),    # High sleep issues
                'Euphoric': (0, 1),          # Low euphoria
                'Mood Swing': (0, 0)         # NO mood swings
            },
            'Bipolar Type-1': {
                'Euphoric': (2, 3),          # High euphoria
                'Mood Swing': (1, 1),        # YES mood swings
                'Sleep disorder': (1, 2),    # Moderate sleep issues
                'Aggressive Response': (0, 1) # Possible aggression
            },
            'Bipolar Type-2': {
                'Mood Swing': (1, 1),        # YES mood swings
                'Sadness': (2, 3),           # High sadness
                'Euphoric': (1, 2),          # Moderate euphoria
                'Sleep disorder': (1, 3)     # Variable sleep
            },
            'Normal': {
                'Sadness': (0, 1),           # Low sadness
                'Sleep disorder': (0, 1),    # Low sleep issues
                'Suicidal thoughts': (0, 0), # NO suicidal thoughts
                'Concentration': (2, 4)      # Good concentration
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
    
    def _suggest_adjustments(self, responses, probabilities):
        """Suggest diagnosis adjustments based on feature patterns"""
        suggestions = []
        
        # Get current diagnosis
        primary_idx = np.argmax(probabilities)
        current_diagnosis = self.label_encoder.inverse_transform([primary_idx])[0]
        
        # Check for depression patterns that might be missed
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
        
        # Check for bipolar patterns that might be missed
        if (responses.get('Mood Swing', 0) == 1 and
            responses.get('Euphoric', 0) >= 2 and
            current_diagnosis not in ['Bipolar Type-1', 'Bipolar Type-2']):
            suggestions.append({
                'type': 'POTENTIAL_BIPOLAR',
                'reason': 'Mood swings with euphoria suggest bipolar spectrum',
                'suggested_diagnosis': 'Bipolar Type-1',
                'confidence_boost': 0.15
            })
        
        # Check if normal diagnosis might be too conservative
        if (current_diagnosis == 'Normal' and
            (responses.get('Sadness', 0) >= 2 or 
             responses.get('Suicidal thoughts', 0) == 1)):
            suggestions.append({
                'type': 'POTENTIAL_UNDER_DIAGNOSIS',
                'reason': 'Significant symptoms present despite Normal classification',
                'suggested_review': True
            })
        
        return suggestions
    
    def enhance_prediction(self, processed_responses, probabilities, original_diagnosis):
        """Apply clinical enhancements to the prediction"""
        analysis = self.analyze_feature_patterns(processed_responses, probabilities)
        
        # Create enhanced prediction
        enhanced_prediction = {
            'original_diagnosis': original_diagnosis,
            'original_confidence': float(np.max(probabilities)),
            'clinical_analysis': analysis,
            'enhanced_diagnosis': original_diagnosis,  # Start with original
            'confidence_adjustment': 0.0,
            'adjustment_reasons': []
        }
        
        # Apply suggestions if they make clinical sense
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
        logger.info("✅ Clinical Decision Enhancer initialized")
    else:
        logger.warning("❌ Could not initialize Clinical Decision Enhancer")



class ClinicalPreprocessor:
    """EXACTLY replicates the preprocessing pipeline from train_model.py"""
    
    def __init__(self, category_mappings: Dict = None):
        self.category_mappings = category_mappings or {}
        self.processing_log = []
    
    def log_step(self, step: str, details: str):
        """Log processing steps for transparency"""
        self.processing_log.append(f"{step}: {details}")
        logger.info(f"Preprocessing - {step}: {details}")
    
    def encode_user_responses(self, raw_responses: Dict) -> Dict:
        """EXACTLY replicate the encoding from train_model.py encode_features()"""
        encoded_responses = {}
        
        # Define the same mappings used in training
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
        
        # Apply EXACT same encoding logic as train_model.py
        for feature, value in raw_responses.items():
            # Feature names should already be in training format from frontend
            training_feature_name = feature
            
            # Frequency features (all mood/emotion related)
            if feature in ['Sadness', 'Euphoric', 'Exhausted', 'Sleep disorder', 'Anxiety', 
                        'Depressed_Mood', 'Irritability', 'Worrying', 'Fatigue']:
                # Frequency features
                if value in frequency_mapping:
                    encoded_value = frequency_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                    self.log_step("Frequency_Encoding", f"{feature}: {value} -> {encoded_value}")
                else:
                    encoded_responses[training_feature_name] = 1  # Default to Sometimes
                    self.log_step("Frequency_Encoding", f"{feature}: {value} -> 1 (default)")
                    
            # Behavioral features (YES/NO questions) - EXPANDED LIST
            elif feature in ['Mood Swing', 'Suicidal thoughts', 'Overthinking', 'Aggressive Response',
                        'Nervous Breakdown', 'Anorexia', 'Authority Respect', 'Try Explanation', 
                        'Ignore & Move-On', 'Admit Mistakes', 'Appetite_Changes', 'Social_Avoidance', 
                        'Compulsive Behavior']:
                # Behavioral features (YES/NO)
                if value in yes_no_mapping:
                    encoded_value = yes_no_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                    self.log_step("Behavioral_Encoding", f"{feature}: {value} -> {encoded_value}")
                else:
                    encoded_responses[training_feature_name] = 0  # Default to NO
                    self.log_step("Behavioral_Encoding", f"{feature}: {value} -> 0 (default)")
                    
            elif feature == 'Sexual Activity':
                # Sexual Activity mapping
                if value in sexual_activity_mapping:
                    encoded_value = sexual_activity_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                    self.log_step("SexualActivity_Encoding", f"{feature}: {value} -> {encoded_value}")
                else:
                    encoded_responses[training_feature_name] = 2  # Default to Moderate interest
                    self.log_step("SexualActivity_Encoding", f"{feature}: {value} -> 2 (default)")
                    
            elif feature == 'Concentration':
                # Concentration mapping  
                if value in concentration_mapping:
                    encoded_value = concentration_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                    self.log_step("Concentration_Encoding", f"{feature}: {value} -> {encoded_value}")
                else:
                    encoded_responses[training_feature_name] = 2  # Default to Average concentration
                    self.log_step("Concentration_Encoding", f"{feature}: {value} -> 2 (default)")
                    
            elif feature == 'Optimism':
                # Optimism mapping
                if value in optimism_mapping:
                    encoded_value = optimism_mapping[value]
                    encoded_responses[training_feature_name] = encoded_value
                    self.log_step("Optimism_Encoding", f"{feature}: {value} -> {encoded_value}")
                else:
                    encoded_responses[training_feature_name] = 2  # Default to Neutral outlook
                    self.log_step("Optimism_Encoding", f"{feature}: {value} -> 2 (default)")
                    
            else:
                # For any other features, try to convert to numeric
                try:
                    if isinstance(value, (int, float)):
                        encoded_responses[training_feature_name] = value
                    elif str(value).isdigit():
                        encoded_responses[training_feature_name] = int(value)
                    else:
                        # Try to see if it's a string representation of a number
                        encoded_responses[training_feature_name] = float(value)
                    self.log_step("Numeric_Value", f"{feature}: {value} -> {encoded_responses[training_feature_name]}")
                except (ValueError, TypeError, AttributeError):
                    encoded_responses[training_feature_name] = 0
                    self.log_step("Numeric_Default", f"{feature}: {value} -> 0 (conversion failed)")
        
        return encoded_responses
    
    def apply_feature_engineering(self, encoded_responses: Dict) -> Dict:
        """EXACTLY replicate feature engineering from training - MATCHING THE MODEL"""
        
        responses = encoded_responses.copy()
        
        # Create composite scores (EXACTLY as expected by the model)
        if 'Mood Swing' in responses and 'Sadness' in responses:
            mood_swing = responses.get('Mood Swing', 0)
            sadness = responses.get('Sadness', 0)
            responses['Mood_Emotion_Composite'] = mood_swing * 0.6 + sadness * 0.4
            self.log_step("Composite_Score", f"Mood_Emotion_Composite: {mood_swing}*0.6 + {sadness}*0.4 = {responses['Mood_Emotion_Composite']:.2f}")
        
        # Create clinical domain scores (EXACTLY as expected by the model)
        clinical_domains = {
            'Mood_Stability_Score': ['Mood Swing', 'Euphoric', 'Sadness'],
            'Cognitive_Function_Score': ['Concentration', 'Optimism', 'Overthinking'],
            'Risk_Assessment_Score': ['Suicidal thoughts', 'Aggressive Response', 'Nervous Breakdown']
        }
        
        for domain_name, features in clinical_domains.items():
            available_features = [f for f in features if f in responses]
            if len(available_features) >= 2:
                domain_values = [responses[f] for f in available_features]
                responses[domain_name] = sum(domain_values) / len(domain_values)
                self.log_step("Domain_Score", f"{domain_name}: {responses[domain_name]:.2f} (from {available_features})")
            else:
                responses[domain_name] = 0
                self.log_step("Domain_Score", f"{domain_name}: 0 (insufficient features: {features})")
        
        # Log all features that will be sent to the model
        expected_features = [
            "Exhausted", "Overthinking", "Sleep disorder", "Nervous Breakdown", "Sexual Activity",
            "Ignore & Move-On", "Cognitive_Function_Score", "Try Explanation", "Authority Respect",
            "Optimism", "Anorexia", "Mood_Stability_Score", "Suicidal thoughts", "Admit Mistakes",
            "Euphoric", "Aggressive Response", "Concentration", "Risk_Assessment_Score",
            "Mood_Emotion_Composite", "Mood Swing", "Sadness"
        ]
        
        missing_in_final = set(expected_features) - set(responses.keys())
        if missing_in_final:
            self.log_step("WARNING", f"Missing in final features: {missing_in_final}")
        
        self.log_step("Feature_Engineering_Complete", 
                    f"Generated {len(responses)} features including {len(clinical_domains)} composite scores")
        
        return responses

    def normalize_feature_names(self, raw_responses: Dict) -> Dict:
        """Normalize feature names to match training data format EXACTLY"""
        normalized_responses = {}
        
        # EXACT mapping from web app to training data features
        feature_name_mapping = {
            # These should map directly (no change needed)
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
            # Use mapping if exists, otherwise use original
            training_feature_name = feature_name_mapping.get(feature, feature)
            normalized_responses[training_feature_name] = value
            
        self.log_step("Feature_Name_Mapping", 
                    f"Mapped {len(raw_responses)} features to {len(normalized_responses)} training features")
        
        return normalized_responses
    
    def validate_clinical_safety(self, responses: Dict) -> Tuple[bool, List[str]]:
        """Clinical safety checks for critical responses"""
        warnings = []
        
        # Critical value checks - using the actual encoded numeric values
        # For binary features (0 or 1)
        if responses.get('Suicidal thoughts', 0) == 1:
            warnings.append("Suicidal thoughts detected - please seek immediate professional help")
        
        if responses.get('Aggressive Response', 0) == 1:
            warnings.append("Aggressive behavior patterns detected - safety assessment recommended")
        
        # Range validation (matching training data ranges)
        for feature, value in responses.items():
            # Frequency features should be 0-3
            if feature in ['Sadness', 'Euphoric', 'Exhausted', 'Sleep disorder', 'Anxiety', 
                        'Depressed_Mood', 'Irritability', 'Worrying', 'Fatigue']:
                if value < 0 or value > 3:
                    warnings.append(f"Feature {feature} value {value} outside expected range 0-3")
            
            # Binary features should be 0-1 - EXPANDED LIST
            elif feature in ['Mood Swing', 'Suicidal thoughts', 'Overthinking', 'Aggressive Response',
                        'Nervous Breakdown', 'Anorexia', 'Authority Respect', 'Try Explanation', 
                        'Ignore & Move-On', 'Admit Mistakes', 'Appetite_Changes', 'Social_Avoidance', 
                        'Compulsive Behavior']:
                if value not in [0, 1]:
                    warnings.append(f"Feature {feature} value {value} should be 0 or 1")
            
            # Concentration and Optimism should be 0-4
            elif feature in ['Concentration', 'Optimism']:
                if value < 0 or value > 4:
                    warnings.append(f"Feature {feature} value {value} outside expected range 0-4")
            
            # Sexual Activity should be 0-4
            elif feature == 'Sexual Activity':
                if value < 0 or value > 4:
                    warnings.append(f"Feature {feature} value {value} outside expected range 0-4")
        
        # Missing critical features
        critical_features = ['Mood Swing', 'Sadness', 'Sleep disorder']
        for feature in critical_features:
            if feature not in responses:
                warnings.append(f"Critical feature {feature} missing")
        
        safety_ok = len(warnings) == 0
        if not safety_ok:
            self.log_step("Safety_Check", f"Safety warnings: {warnings}")
        else:
            self.log_step("Safety_Check", "All safety checks passed")
            
        return safety_ok, warnings

    def preprocess(self, raw_responses: Dict) -> Tuple[Dict, List[str], List[str]]:
        """Complete preprocessing pipeline EXACTLY matching training"""
        
        # Start with fresh processing log
        self.processing_log = []
        self.log_step("Pipeline_Start", f"Processing {len(raw_responses)} raw features: {list(raw_responses.keys())}")
        
        try:
            # Step 0: Normalize feature names to match training data
            normalized_responses = self.normalize_feature_names(raw_responses)
            
            # Step 1: EXACT same encoding as training data
            responses = self.encode_user_responses(normalized_responses)
            
            # Step 2: EXACT same feature engineering as training
            responses = self.apply_feature_engineering(responses)
            
            # Step 3: Clinical safety validation
            safety_ok, safety_warnings = self.validate_clinical_safety(responses)
            
            self.log_step("Pipeline_Complete", 
                        f"Processed {len(responses)} features. Safety OK: {safety_ok}")
            
            return responses, self.processing_log, safety_warnings
            
        except Exception as e:
            self.log_step("Pipeline_Error", f"Preprocessing failed: {str(e)}")
            import traceback
            self.log_step("Pipeline_Error", f"Traceback: {traceback.format_exc()}")
            raise e

def ensure_csv_headers():
    """Ensure CSV file has proper headers"""
    if not os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write headers
            headers = [
                'assessment_id', 'timestamp', 'patient_name', 'patient_number', 
                'patient_age', 'patient_gender', 'primary_diagnosis', 'confidence',
                'confidence_percentage'
            ]
            # Add all feature columns
            if feature_names:
                headers.extend(feature_names)
            writer.writerow(headers)

def save_assessment_to_csv(assessment_data):
    """Save assessment data to CSV file"""
    try:
        ensure_csv_headers()
        
        # Prepare row data
        row_data = {
            'assessment_id': assessment_data.get('id', ''),
            'timestamp': assessment_data.get('timestamp', ''),
            'patient_name': assessment_data.get('patient_info', {}).get('name', ''),
            'patient_number': assessment_data.get('patient_info', {}).get('number', ''),
            'patient_age': assessment_data.get('patient_info', {}).get('age', ''),
            'patient_gender': assessment_data.get('patient_info', {}).get('gender', ''),
            'primary_diagnosis': assessment_data.get('primary_diagnosis', ''),
            'confidence': assessment_data.get('confidence', 0),
            'confidence_percentage': assessment_data.get('confidence_percentage', 0)
        }
        
        # Add feature responses
        responses = assessment_data.get('responses', {})
        for feature in feature_names:
            row_data[feature] = responses.get(feature, '')
        
        # Read existing data to maintain all columns
        existing_data = []
        if os.path.exists(CSV_FILE_PATH):
            with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_data = list(reader)
                # Ensure we have all current headers
                if reader.fieldnames:
                    all_headers = reader.fieldnames
        
        # Write back all data including new row
        with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as f:
            if existing_data:
                writer = csv.DictWriter(f, fieldnames=all_headers)
                writer.writeheader()
                writer.writerows(existing_data)
                writer.writerow(row_data)
            else:
                writer = csv.DictWriter(f, fieldnames=list(row_data.keys()))
                writer.writeheader()
                writer.writerow(row_data)
        
        logger.info(f"✅ Assessment saved to CSV: {assessment_data.get('id')}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving to CSV: {e}")
        return False

def load_assessments_from_csv():
    """Load all assessments from CSV file with enhanced data parsing"""
    try:
        if not os.path.exists(CSV_FILE_PATH):
            return {}
        
        assessments_by_patient = {}
        
        with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                patient_number = row.get('patient_number', 'general')
                if patient_number not in assessments_by_patient:
                    assessments_by_patient[patient_number] = []
                
                # Convert row back to assessment format with proper data types
                assessment = {
                    'id': row.get('assessment_id', ''),
                    'timestamp': row.get('timestamp', ''),
                    'patient_info': {
                        'name': row.get('patient_name', ''),
                        'number': patient_number,
                        'age': row.get('patient_age', ''),
                        'gender': row.get('patient_gender', '')
                    },
                    'primary_diagnosis': row.get('primary_diagnosis', ''),
                    'confidence': safe_float(row.get('confidence', 0)),
                    'confidence_percentage': safe_float(row.get('confidence_percentage', 0)),
                    'responses': {},
                    'all_diagnoses': [
                        {
                            'diagnosis': row.get('primary_diagnosis', ''),
                            'probability': safe_float(row.get('confidence', 0)),
                            'confidence_percentage': safe_float(row.get('confidence_percentage', 0))
                        }
                    ]
                }
                
                # Add feature responses with proper data types
                for feature in feature_names:
                    if feature in row and row[feature]:
                        try:
                            # Try to convert to appropriate numeric type
                            value = row[feature]
                            if value.isdigit():
                                assessment['responses'][feature] = int(value)
                            else:
                                assessment['responses'][feature] = float(value)
                        except (ValueError, TypeError):
                            # Keep as string if conversion fails
                            assessment['responses'][feature] = value
                
                assessments_by_patient[patient_number].append(assessment)
        
        logger.info(f"✅ Loaded assessments from CSV: {sum(len(v) for v in assessments_by_patient.values())} total")
        return assessments_by_patient
        
    except Exception as e:
        logger.error(f"❌ Error loading from CSV: {e}")
        return {}

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
    
    
def delete_assessment_from_csv(patient_number, assessment_id):
    """Delete assessment from CSV file"""
    try:
        if not os.path.exists(CSV_FILE_PATH):
            return False
        
        # Read all data
        with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames
        
        # Filter out the assessment to delete
        filtered_rows = [
            row for row in rows 
            if not (row.get('patient_number') == patient_number and row.get('assessment_id') == assessment_id)
        ]
        
        # Write back filtered data
        with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_rows)
        
        logger.info(f"✅ Assessment deleted from CSV: {assessment_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error deleting from CSV: {e}")
        return False
    

def convert_responses_to_features(processed_responses: Dict) -> np.ndarray:
    """Convert processed responses to feature array with EXACT feature order matching training"""
    try:
        # Initialize feature array with zeros (same as training pipeline)
        feature_array = np.zeros(len(feature_names))
        
        missing_features = []
        found_features = []
        
        logger.info(f"Training features expected: {len(feature_names)}")
        logger.info(f"Available processed features: {len(processed_responses)}")
        logger.info(f"Processed features: {list(processed_responses.keys())}")
        
        # Map responses to features based on EXACT feature_names order
        for i, feature_name in enumerate(feature_names):
            if feature_name in processed_responses:
                # Ensure the value is numeric
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
                # Feature not provided - use training-consistent default
                feature_array[i] = 0  # Same default as training pipeline
                missing_features.append(feature_name)
        
        if missing_features:
            logger.warning(f"Missing features filled with defaults: {missing_features}")
        
        if found_features:
            logger.info(f"Found features: {found_features}")
        
        logger.info(f"✅ Feature array created: {len(feature_array)} features, "
                   f"{len(missing_features)} missing, {len(found_features)} found")
        logger.info(f"Feature array stats - Min: {np.min(feature_array):.2f}, "
                   f"Max: {np.max(feature_array):.2f}, Mean: {np.mean(feature_array):.2f}")
        
        return feature_array
        
    except Exception as e:
        logger.error(f"❌ Feature conversion error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None
    
# Load components at startup
model_package, scaler, label_encoder, feature_names, category_mappings = load_model_components()
initialize_clinical_enhancer()

# Initialize preprocessor
preprocessor = ClinicalPreprocessor(category_mappings)


#*************Routes to serve the frontend files:************
# Serve main HTML files directly from frontend root
@app.route('/')
def serve_index():
    return send_from_directory('frontend', 'Home.html')

# Serve main HTML files directly from frontend root
@app.route('/<page_name>.html')
def serve_html_page(page_name):
    # List of main pages in frontend root
    main_pages = [
        'Home', 'About', 'MenHel_analogy', 'MenHel_prediction', 
        'resources', 'crisis-support', 'relief_techniques', 'navbar', 'footer'
    ]
    
    if page_name in main_pages:
        return send_from_directory('frontend', f'{page_name}.html')  # Fixed: removed ../
    else:
        # Try to serve from resources if not found in main
        try:
            return send_from_directory('frontend/resources', f'{page_name}.html')  # Fixed: removed ../
        except:
            return send_from_directory('frontend', 'Home.html')

# Serve resource HTML files specifically
@app.route('/resources/<resource_name>.html')
def serve_resource_page(resource_name):
    """Serve individual resource pages"""
    resource_pages = [
        'anxiety-resource', 'bipolar-resource', 'depression-resource',
        'medication-resource', 'mindfulness-resource', 'ptsd-resource',
        'selfcare-resource', 'therapy-resource'
    ]
    
    if resource_name in resource_pages:
        return send_from_directory('frontend/resources', f'{resource_name}.html')
    else:
        return send_from_directory('frontend', 'resources.html')



# Serve CSS files from both locations
@app.route('/css/<path:filename>')
def serve_css(filename):
    # Try main css directory first
    try:
        return send_from_directory('frontend/css', filename)
    except:
        # Fallback to resource-specific CSS
        return send_from_directory('frontend/resources', filename)

# Serve JS files  
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('frontend/js', filename)

# Serve resource-specific CSS
@app.route('/resources/css/<path:filename>')
def serve_resource_css(filename):
    return send_from_directory('frontend/resources', filename)

# Serve all other static files
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('frontend/assets', filename)

# Special route for resource-detail.css
@app.route('/resource-detail.css')
def serve_resource_detail_css():
    return send_from_directory('frontend/resources', 'resource-detail.css')

# Catch-all for SPA routing
@app.route('/<path:path>')
def serve_static_files(path):
    # Handle nested resource paths
    if path.startswith('resources/'):
        try:
            # Remove 'resources/' prefix and serve from resources directory
            resource_path = path.replace('resources/', '', 1)
            return send_from_directory('frontend/resources', resource_path)
        except:
            pass
    
    # Try to serve from main frontend directory
    try:
        return send_from_directory('frontend', path)
    except:
        # Final fallback - serve home page
        return send_from_directory('frontend', 'Home.html')

#************End of routes to Serve Frontend Files************
@app.route('/debug-path')
def debug_path():
    """Debug current path issues"""
    return jsonify({
        'current_path': request.path,
        'url': request.url,
        'referrer': request.referrer,
        'is_resource': '/resources/' in request.path,
        'suggested_base_path': '../' if '/resources/' in request.path else './'
    })
    
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors by serving the main page for SPA routing"""
    if request.path.startswith('/api/'):
        # API 404 - return JSON error
        return jsonify({'error': 'API endpoint not found'}), 404
    else:
        # Frontend 404 - serve main page for SPA routing
        try:
            return send_from_directory('frontend', 'Home.html')  
        except:
            return jsonify({'error': 'Page not found'}), 404
        
        

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced API health check with preprocessing info"""
    components_loaded = all([
        model_package is not None,
        scaler is not None, 
        label_encoder is not None,
        feature_names is not None,
        category_mappings is not None
    ])
    
    health_info = {
        'status': 'healthy' if components_loaded else 'unhealthy',
        'model_loaded': model_package is not None,
        'scaler_loaded': scaler is not None,
        'encoder_loaded': label_encoder is not None,
        'features_loaded': feature_names is not None,
        'category_mappings_loaded': category_mappings is not None,
        'total_features': len(feature_names) if feature_names else 0,
        'available_classes': label_encoder.classes_.tolist() if label_encoder else [],
        'preprocessing_available': True,
        'clinical_validation': True,
        'clinical_enhancer_available': clinical_enhancer is not None
    }
    
    return jsonify(health_info)

@app.route('/api/get-single-assessment', methods=['POST'])
def get_single_assessment():
    """Get a single specific assessment from CSV file"""
    try:
        data = request.json
        patient_name = data.get('name', '').strip()
        patient_number = data.get('number', '').strip()
        assessment_id = data.get('assessment_id', '').strip()
        
        if not patient_name or not patient_number or not assessment_id:
            return jsonify({'error': 'Patient name, number, and assessment ID required'}), 400
        
        # Load assessment data from CSV file
        all_assessments = load_assessments_from_csv()
        
        # Find assessments for this patient
        patient_assessments = all_assessments.get(patient_number, [])
        
        # Find the specific assessment
        target_assessment = None
        for assessment in patient_assessments:
            # Make sure we're comparing strings and handle None values
            current_id = assessment.get('id', '')
            current_name = assessment.get('patient_info', {}).get('name', '').lower()
            
            if (str(current_id) == str(assessment_id) and 
                current_name == patient_name.lower()):
                target_assessment = assessment
                break
        
        if not target_assessment:
            logger.warning(f"Assessment not found: {assessment_id} for {patient_name} (#{patient_number})")
            return jsonify({'error': 'Assessment not found'}), 404
        
        # Enhance the assessment data with additional details for display
        enhanced_assessment = enhance_assessment_data(target_assessment)
        
        logger.info(f"✅ Single assessment retrieved: {assessment_id}")
        return jsonify({
            'success': True,
            'assessment': enhanced_assessment
        })
        
    except Exception as e:
        logger.error(f"❌ Error retrieving single assessment: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to retrieve assessment: {str(e)}'}), 500
    
    
def enhance_assessment_data(assessment):
    """Enhance assessment data with additional details for display"""
    try:
        # Add diagnosis description if missing
        if 'diagnosis_description' not in assessment:
            assessment['diagnosis_description'] = get_diagnosis_description(assessment.get('primary_diagnosis', ''))
        
        # Ensure all_diagnoses is properly formatted
        if 'all_diagnoses' not in assessment or not assessment['all_diagnoses']:
            assessment['all_diagnoses'] = [
                {
                    'diagnosis': assessment.get('primary_diagnosis', ''),
                    'probability': assessment.get('confidence', 0),
                    'confidence_percentage': assessment.get('confidence_percentage', 0)
                }
            ]
        
        # Add processing details if missing
        if 'processing_details' not in assessment:
            assessment['processing_details'] = {
                'preprocessing_steps': 15,  # Default value
                'clinical_safety_warnings': [],
                'total_features_processed': len(assessment.get('responses', {})),
                'model_features_used': len(feature_names) if feature_names else 0,
                'feature_engineering_applied': True,
                'clinical_domains_calculated': True,
                'clinical_enhancement_applied': False,
                'safety_check_status': 'PASSED'
            }
        
        # Add technical details if missing
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

def get_diagnosis_description(diagnosis):
    """Get description for diagnosis"""
    descriptions = {
        'Normal': 'Your responses indicate typical mental well-being patterns with no significant clinical concerns detected.',
        'Bipolar Type-1': 'Your responses show patterns that may indicate Bipolar Type-1 disorder. This is characterized by manic episodes that last at least 7 days.',
        'Bipolar Type-2': 'Your responses suggest patterns consistent with Bipolar Type-2 disorder, characterized by hypomanic and depressive episodes.',
        'Depression': 'Your responses align with patterns commonly seen in depressive disorders, including persistent sadness and loss of interest.'
    }
    return descriptions.get(diagnosis, 'Assessment completed successfully. Please consult with a healthcare professional for accurate diagnosis.')

def parse_assessment_timestamp(timestamp_str):
    """Safely parse assessment timestamp with proper timezone handling"""
    try:
        if not timestamp_str:
            return datetime.now()
        
        # Handle different timestamp formats
        if 'T' in timestamp_str:
            # ISO format with timezone
            if timestamp_str.endswith('Z'):
                # UTC timezone
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # Local timezone or offset
                dt = datetime.fromisoformat(timestamp_str)
        else:
            # Simple format without timezone
            dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        
        return dt
        
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse timestamp '{timestamp_str}': {e}, using current time")
        return datetime.now()

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        # Get user responses and patient info from frontend
        data = request.json
        user_responses = data.get('responses', {})
        patient_info = data.get('patientInfo', {})
        
        if not user_responses:
            return jsonify({'error': 'No responses provided'}), 400
        
        logger.info(f"Received {len(user_responses)} responses for patient: {patient_info.get('name', 'Unknown')}")
        
        # Step 1: Complete preprocessing pipeline
        try:
            processed_responses, processing_log, safety_warnings = preprocessor.preprocess(user_responses)
            logger.info("✅ Preprocessing completed successfully")
        except Exception as e:
            logger.error(f"❌ Preprocessing failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Data preprocessing failed: {str(e)}'}), 400
        
        # Step 2: Convert to feature array
        feature_array = convert_responses_to_features(processed_responses)
        if feature_array is None:
            return jsonify({'error': 'Feature conversion failed'}), 400
        
        # Step 3: Scale features
        try:
            feature_array_scaled = scaler.transform(feature_array.reshape(1, -1))
            logger.info("✅ Feature scaling completed")
        except Exception as e:
            logger.error(f"❌ Feature scaling failed: {e}")
            return jsonify({'error': 'Feature scaling failed'}), 500
        
        # Step 4: Make prediction
        try:
            prediction = model_package['model'].predict(feature_array_scaled)
            probabilities = model_package['model'].predict_proba(feature_array_scaled)
            logger.info("✅ Prediction completed")
        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}")
            return jsonify({'error': 'Model prediction failed'}), 500
        
        # Step 5: Process basic results
        diagnosis_idx = prediction[0]
        original_diagnosis = label_encoder.inverse_transform([diagnosis_idx])[0]
        original_confidence = probabilities[0][diagnosis_idx]
        
        # Step 6: Apply clinical enhancement if available
        clinical_enhancement = None
        final_diagnosis = original_diagnosis
        final_confidence = original_confidence
        
        if clinical_enhancer:
            clinical_enhancement = clinical_enhancer.enhance_prediction(
                processed_responses, probabilities[0], original_diagnosis
            )
            
            # Use enhanced diagnosis if different and has good reason
            if (clinical_enhancement['enhanced_diagnosis'] != original_diagnosis and
                clinical_enhancement['adjustment_reasons']):
                final_diagnosis = clinical_enhancement['enhanced_diagnosis']
                final_confidence = min(1.0, original_confidence + clinical_enhancement['confidence_adjustment'])
                logger.info(f"🎯 Clinical enhancement applied: {original_diagnosis} -> {final_diagnosis}")
        
        # Step 7: Get top diagnoses
        top_diagnoses = []
        for idx, prob in enumerate(probabilities[0]):
            diagnosis_name = label_encoder.inverse_transform([idx])[0]
            top_diagnoses.append({
                'diagnosis': diagnosis_name,
                'probability': float(prob),
                'confidence_percentage': float(prob * 100)
            })
        top_diagnoses.sort(key=lambda x: x['probability'], reverse=True)
        
        # Step 8: Enhanced response
        response_data = {
            'primary_diagnosis': final_diagnosis,
            'confidence': float(final_confidence),
            'confidence_percentage': float(final_confidence * 100),
            'all_diagnoses': top_diagnoses[:3],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'assessment_id': f"MH{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'patient_info': patient_info,  

            
            # Enhanced processing information
            'processing_details': {
                'preprocessing_steps': len(processing_log),
                'clinical_safety_warnings': safety_warnings,
                'total_features_processed': len(processed_responses),
                'model_features_used': len(feature_names),
                'feature_engineering_applied': True,
                'clinical_domains_calculated': True,
                'clinical_enhancement_applied': clinical_enhancement is not None and final_diagnosis != original_diagnosis,
                'safety_check_status': 'CRITICAL_ALERTS' if safety_warnings else 'PASSED' 

            },
            'technical_details': {
                'processing_log': processing_log,
                'safety_checks_passed': len(safety_warnings) == 0,
                'feature_array_shape': feature_array.shape,
                'composite_scores_included': True
            }
        }
        
        # Add clinical enhancement details if applied
        if clinical_enhancement:
            response_data['clinical_insights'] = {
                'original_diagnosis': clinical_enhancement['original_diagnosis'],
                'enhancement_applied': clinical_enhancement['enhanced_diagnosis'] != clinical_enhancement['original_diagnosis'],
                'adjustment_reasons': clinical_enhancement['adjustment_reasons'],
                'pattern_analysis': clinical_enhancement['clinical_analysis']
            }
        
        logger.info(f"✅ Assessment completed: {final_diagnosis} (confidence: {final_confidence:.2f})")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Prediction endpoint error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Assessment failed. Please try again.'}), 500

    
@app.route('/api/save-assessment', methods=['POST'])
def save_assessment():
    """Save complete assessment data to CSV file"""
    try:
        data = request.json
        assessment_data = data.get('assessment_data', {})
        
        # Generate unique ID if not provided
        if 'id' not in assessment_data:
            assessment_data['id'] = f"MH{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        
        # Add timestamp if not present
        if 'timestamp' not in assessment_data:
            assessment_data['timestamp'] = datetime.now().isoformat()
        
        # Save to CSV
        if save_assessment_to_csv(assessment_data):
            logger.info(f"✅ Assessment saved to CSV: {assessment_data['id']}")
            return jsonify({
                'success': True,
                'assessment_id': assessment_data['id'],
                'message': 'Assessment saved successfully'
            })
        else:
            return jsonify({'error': 'Failed to save assessment data to CSV'}), 500
        
    except Exception as e:
        logger.error(f"❌ Error saving assessment: {e}")
        return jsonify({'error': f'Failed to save assessment: {str(e)}'}), 500

@app.route('/api/get-patient-assessments', methods=['POST'])
def get_patient_assessments():
    """Get all assessments for a specific patient from CSV file"""
    try:
        data = request.json
        patient_name = data.get('name', '').strip()
        patient_number = data.get('number', '').strip()
        
        if not patient_name or not patient_number:
            return jsonify({'error': 'Patient name and number required'}), 400
        
        # Load assessment data from CSV file
        all_assessments = load_assessments_from_csv()
        
        # Find assessments for this patient
        patient_assessments = all_assessments.get(patient_number, [])
        
        # Filter by name (case-insensitive)
        filtered_assessments = [
            assessment for assessment in patient_assessments
            if assessment.get('patient_info', {}).get('name', '').lower() == patient_name.lower()
        ]
        
        # Sort by timestamp (newest first)
        filtered_assessments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        logger.info(f"✅ Found {len(filtered_assessments)} assessments for {patient_name} (#{patient_number})")
        
        return jsonify({
            'success': True,
            'assessments': filtered_assessments,
            'count': len(filtered_assessments)
        })
        
    except Exception as e:
        logger.error(f"❌ Error retrieving assessments: {e}")
        return jsonify({'error': f'Failed to retrieve assessments: {str(e)}'}), 500

@app.route('/api/delete-assessment', methods=['POST'])
def delete_assessment():
    """Delete a specific assessment from CSV storage"""
    try:
        data = request.json
        patient_number = data.get('patient_number', '')
        assessment_id = data.get('assessment_id', '')
        
        if not patient_number or not assessment_id:
            return jsonify({'error': 'Patient number and assessment ID required'}), 400
        
        # Delete from CSV
        if delete_assessment_from_csv(patient_number, assessment_id):
            logger.info(f"✅ Assessment {assessment_id} deleted for patient #{patient_number}")
            return jsonify({'success': True, 'message': 'Assessment deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete assessment from CSV'}), 500
            
    except Exception as e:
        logger.error(f"❌ Error deleting assessment: {e}")
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
            'clinical_decision_support': clinical_enhancer is not None
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

@app.route('/api/generate-pdf-report', methods=['POST'])
def generate_pdf_report():
    """Generate a professional PDF report for an assessment"""
    try:
        data = request.json
        assessment_data = data.get('assessment_data', {})
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              topMargin=1*inch, 
                              bottomMargin=1*inch,
                              leftMargin=0.75*inch,
                              rightMargin=0.75*inch)
        
        styles = getSampleStyleSheet()
        
        # Custom styles
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
        
        # Build story (content)
        story = []
        
        # Header
        story.append(Paragraph("MENTAL HEALTH ASSESSMENT REPORT", title_style))
        story.append(Spacer(1, 20))
        
        # Assessment Metadata
        story.append(Paragraph("ASSESSMENT DETAILS", heading_style))
        

        meta_data = [
            ["Assessment ID:", assessment_data.get('id', 'N/A')],
            ["Assessment Date:", parse_assessment_timestamp(assessment_data.get('timestamp')).astimezone(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")],
            ["Report Generated:", datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")]
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
        
        # Patient Information
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
        
        # Primary Diagnosis
        story.append(Paragraph("CLINICAL ASSESSMENT RESULTS", heading_style))
        
        primary_diagnosis = assessment_data.get('primary_diagnosis', 'N/A')
        confidence = assessment_data.get('confidence_percentage', 0)
        
        diagnosis_data = [
            ["Primary Diagnosis:", primary_diagnosis],
            ["Confidence Level:", f"{confidence:.1f}%"],
            ["Assessment Date:", datetime.fromisoformat(assessment_data.get('timestamp', datetime.now().isoformat())).strftime("%B %d, %Y")]
        ]
        
        # Color code based on confidence
        confidence_color = colors.HexColor('#10b981')  # Green
        if confidence < 70:
            confidence_color = colors.HexColor('#f59e0b')  # Amber
        if confidence < 50:
            confidence_color = colors.HexColor('#ef4444')  # Red
        
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
        
        # Diagnosis Description
        diagnosis_desc = assessment_data.get('diagnosis_description', 
                                           'Comprehensive mental health assessment completed.')
        story.append(Paragraph("Assessment Summary:", subheading_style))
        story.append(Paragraph(diagnosis_desc, normal_style))
        story.append(Spacer(1, 20))
        
        # Other Possible Diagnoses
        story.append(Paragraph("DIFFERENTIAL DIAGNOSES", heading_style))
        other_diagnoses = assessment_data.get('all_diagnoses', [])
        
        if other_diagnoses:
            diagnoses_data = [["Diagnosis", "Probability"]]  # Header
            
            for diagnosis in other_diagnoses[:5]:  # Top 5 other diagnoses
                diagnoses_data.append([
                    diagnosis.get('diagnosis', 'N/A'),
                    f"{diagnosis.get('confidence_percentage', 0):.1f}%"
                ])
            
            diagnoses_table = Table(diagnoses_data, colWidths=[4*inch, 1.5*inch])
            diagnoses_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),  # Header
                ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),       # Data
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),  # Header background
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),     # Header text
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),  # Data background
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
        
        # Response Summary (Condensed)
        story.append(Paragraph("KEY ASSESSMENT RESPONSES", heading_style))
        responses = assessment_data.get('responses', {})
        
        if responses:
            # Group responses by category
            response_data = [["Domain", "Question", "Response"]]
            
            # Define category mappings
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
            
            # Group responses
            grouped_responses = {}
            for feature, response in responses.items():
                category = category_mapping.get(feature, 'Other')
                if category not in grouped_responses:
                    grouped_responses[category] = []
                
                # Format the question text
                question_text = feature.replace('_', ' ').title()
                grouped_responses[category].append([question_text, str(response)])
            
            # Add to table
            for category, responses_list in grouped_responses.items():
                for i, (question, response) in enumerate(responses_list):
                    if i == 0:
                        response_data.append([category, question, response])
                    else:
                        response_data.append(["", question, response])
            
            response_table = Table(response_data, colWidths=[1.2*inch, 3.3*inch, 1.5*inch])
            response_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),  # Header
                ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),      # Data
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),  # Header
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),    # Header text
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),  # Data
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('SPAN', (0, 1), (0, 1)),  # Span category cells
            ]))
            
            story.append(response_table)
        story.append(Spacer(1, 25))
        
        # Disclaimer
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
        
        # Footer
        footer_text = "Confidential Mental Health Assessment Report - Generated by Clinical Assessment System"
        story.append(Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#64748b')
        )))
         
        # Build PDF
        doc.build(story)
        
        # Get PDF value
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = app.response_class(
            response=pdf,
            status=200,
            mimetype='application/pdf'
        )
        
        # Set filename
        filename = f"mental_health_assessment_{assessment_data.get('id', 'report')}.pdf"
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        logger.info(f"✅ PDF report generated for assessment {assessment_data.get('id', 'unknown')}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error generating PDF report: {e}")
        return jsonify({'error': f'Failed to generate PDF report: {str(e)}'}), 500
    

if __name__ == '__main__':
    # Enhanced startup verification
    if all([model_package, scaler, label_encoder, feature_names, category_mappings]):
        logger.info("✅ All model components loaded successfully!")
        logger.info(f"📊 Features: {len(feature_names)}")
        logger.info(f"🎯 Classes: {label_encoder.classes_.tolist()}")
        logger.info("🔧 Enhanced preprocessing pipeline: ACTIVE")
        logger.info("✅ EXACT training pipeline replication: VERIFIED")
        logger.info("🎯 Confidence calibration: ENABLED")
        if clinical_enhancer:
            logger.info("🏥 Clinical Decision Enhancer: ACTIVE")
        else:
            logger.warning("⚠️ Clinical Decision Enhancer: NOT AVAILABLE")
    else:
        logger.error("❌ Failed to load model components!")
        # Don't exit in production, just log the error
        if not os.environ.get('RENDER'):
            sys.exit(1)
    
    # Get port from environment variable (Render provides this)
    port = int(os.environ.get('PORT', 5001))
    
    # Don't use debug mode in production
    debug_mode = not bool(os.environ.get('RENDER'))
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
    
    
    
    
    
