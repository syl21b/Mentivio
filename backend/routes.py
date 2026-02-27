from flask import request, jsonify, send_from_directory, redirect
from app import app, model_package, scaler, label_encoder, feature_names, category_mappings, clinical_enhancer, preprocessor
from database import (
    save_assessment_to_db, load_assessments_from_db, load_single_assessment_from_db,
    delete_assessment_from_db, get_postgres_connection, convert_to_canonical_key
)
from security import SecurityUtils, rate_limiter, SecurityConfig
import logging
import numpy as np
import pandas as pd
import json
import uuid
from datetime import datetime, timezone, timedelta
import pytz
import re
import io
import os
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)


# Helper functions
def convert_coded_to_english(coded_responses):
    """Convert coded responses to English for model processing"""
    english_responses = {}

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
            english_answer = CODE_TO_ENGLISH.get(answer_code, 'NO')
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


# Static routes
@app.route('/')
def serve_index():
    return redirect('/home', code=302)


@app.route('/<page_name>')
def serve_html_page(page_name):
    main_pages = {
        'home': 'home.html',
        'about': 'about.html',
        'analogy': 'analogy.html',
        'prediction': 'prediction.html',
        'resources': 'resources.html',
        'crisis-support': 'crisis-support.html',
        'relief_techniques': 'relief_techniques.html',
        'privacy': 'privacy.html',
        'terms': 'terms.html'
    }

    if page_name in main_pages:
        return send_from_directory(app.static_folder, main_pages[page_name])

    resource_pages = [
        'anxiety-resource', 'bipolar-resource', 'depression-resource',
        'medication-resource', 'mindfulness-resource', 'ptsd-resource',
        'selfcare-resource', 'therapy-resource', 'physical-resource'
    ]

    if page_name in resource_pages:
        return send_from_directory(os.path.join(app.static_folder, 'resources'), f'{page_name}.html')

    try:
        return send_from_directory(app.static_folder, f'{page_name}.html')
    except:
        try:
            return send_from_directory(os.path.join(app.static_folder, 'resources'), f'{page_name}.html')
        except:
            return send_from_directory(app.static_folder, 'home.html')


@app.route('/<page_name>.html')
def serve_html_page_with_extension(page_name):
    return redirect(f'/{page_name}')


@app.route('/resources/<resource_name>')
def serve_resource_page(resource_name):
    resource_pages = [
        'anxiety-resource', 'bipolar-resource', 'depression-resource',
        'medication-resource', 'mindfulness-resource', 'ptsd-resource',
        'selfcare-resource', 'therapy-resource', 'physical-resource'
    ]

    if resource_name in resource_pages:
        return send_from_directory(os.path.join(app.static_folder, 'resources'), f'{resource_name}.html')
    else:
        return send_from_directory(app.static_folder, 'resources.html')


@app.route('/resources/<resource_name>.html')
def serve_resource_page_with_extension(resource_name):
    return redirect(f'/resources/{resource_name}')


@app.route('/css/<path:filename>')
def serve_css(filename):
    try:
        return send_from_directory(os.path.join(app.static_folder, 'css'), filename)
    except:
        return send_from_directory(os.path.join(app.static_folder, 'resources'), filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)


@app.route('/resources/css/<path:filename>')
def serve_resource_css(filename):
    return send_from_directory(os.path.join(app.static_folder, 'resources'), filename)


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)


@app.route('/resource-detail.css')
def serve_resource_detail_css():
    return send_from_directory(os.path.join(app.static_folder, 'resources'), 'resource-detail.css')


@app.route('/<path:path>')
def serve_static_files(path):
    if path.startswith(('css/', 'js/', 'assets/', 'lang/', 'resources/')):
        try:
            if path.startswith('resources/'):
                resource_path = path.replace('resources/', '', 1)
                return send_from_directory(os.path.join(app.static_folder, 'resources'), resource_path)
            return send_from_directory(app.static_folder, path)
        except:
            pass

    try:
        return serve_html_page(path)
    except:
        return send_from_directory(app.static_folder, 'home.html')


# API routes
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
        coded_responses = data.get('coded_responses', {})
        patient_info = data.get('patientInfo', {})
        assessment_start_time = data.get('assessment_start_time')

        if not coded_responses:
            return jsonify({'error': 'No responses provided'}), 400

        coded_valid, coded_msg = SecurityUtils.validate_coded_responses(coded_responses)
        if not coded_valid:
            logger.warning(f"Invalid coded responses: {coded_msg}")
            return jsonify({'error': f'Invalid response format: {coded_msg}'}), 400

        user_responses = convert_coded_to_english(coded_responses)

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

        logger.info(f"Predict - Coded responses: {coded_responses}")
        logger.info(f"Predict - Converted to English: {user_responses}")

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
                        diagnosis['confidence_percentage'] = round(final_confidence_percentage, 0)
                        break

                all_diagnoses.sort(key=lambda x: x['probability'], reverse=True)

                final_diagnosis = all_diagnoses[0]['diagnosis']
                final_confidence = all_diagnoses[0]['probability']
                final_confidence_percentage = all_diagnoses[0]['confidence_percentage']

        response_data = {
            'primary_diagnosis': final_diagnosis,
            'confidence': float(final_confidence),
            'confidence_percentage': round(float(final_confidence_percentage), 0),
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
            'coded_responses': coded_responses,
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

        if safety_warnings:
            response_data['emergency_alert'] = True
            response_data['emergency_message'] = 'URGENT: Please seek immediate professional help. This assessment detected potential safety concerns. Call emergency services if needed.'
            logger.warning(f"Safety warnings triggered emergency alert: {safety_warnings}")

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

        assessment_data_for_db = {
            'primary_diagnosis': final_diagnosis,
            'confidence': float(final_confidence),
            'confidence_percentage': round(float(final_confidence_percentage), 0),
            'all_diagnoses': [
                {
                    'diagnosis': diagnosis['diagnosis'],
                    'probability': diagnosis['probability'],
                    'confidence_percentage': round(diagnosis['confidence_percentage'], 0),
                    'rank': diagnosis['rank']
                }
                for diagnosis in all_diagnoses
            ],
            'timestamp': report_generation_time,
            'assessment_timestamp': assessment_date_str,
            'timezone': client_timezone,
            'assessment_id': f"MH{client_now.strftime('%Y%m%d%H%M%S')}",
            'patient_info': patient_info,
            'coded_responses': coded_responses,
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


@app.route('/api/generate-pdf-report', methods=['POST'])
def generate_pdf_report():
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

        patient_info = pdf_data.get('patient_info', {})
        primary_diagnosis = pdf_data.get('primary_diagnosis', '')
        all_diagnoses = pdf_data.get('all_diagnoses', [])
        questions_and_answers = pdf_data.get('questions_and_answers', [])
        pdf_translations = pdf_data.get('pdf_translations', {})
        confidence_percentage = pdf_data.get('confidence_percentage', 0)
        diagnosis_description = pdf_data.get('diagnosis_description', '')
        safety_warnings = pdf_data.get('safety_warnings', [])

        original_data = pdf_data.get('original_data', {})
        coded_responses = original_data.get('coded_responses', {})

        buffer = io.BytesIO()

        base_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'

        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            font_path = os.path.join(app.static_folder, 'assets', 'fonts') + os.path.sep

            font_mapping = {
                'zh': {'regular': 'NotoSansSC-Regular', 'bold': 'NotoSansSC-Bold', 'extension': '.ttf'},
                'vi': {'regular': 'NotoSans-Regular', 'bold': 'NotoSans-Bold', 'extension': '.ttf'},
                'hi': {'regular': 'NotoSansDevanagari-Regular', 'bold': 'NotoSansDevanagari-Bold', 'extension': '.ttf'},
                'ar': {'regular': 'NotoSansArabic-Regular', 'bold': 'NotoSansArabic-Bold', 'extension': '.ttf'},
                'ko': {'regular': 'NotoSansKR-Regular', 'bold': 'NotoSansKR-Bold', 'extension': '.ttf'},
                'ja': {'regular': 'NotoSansJP-Regular', 'bold': 'NotoSansJP-Bold', 'extension': '.ttf'},
                'th': {'regular': 'NotoSansThai-Regular', 'bold': 'NotoSansThai-Bold', 'extension': '.ttf'},
                'default': {'regular': 'NotoSans-Regular', 'bold': 'NotoSans-Bold', 'extension': '.ttf'}
            }

            lang_code = language[:2] if language else 'en'
            font_config = font_mapping.get(lang_code, font_mapping['default'])

            regular_font_name = font_config['regular']
            bold_font_name = font_config['bold']
            extension = font_config['extension']

            regular_font_file = os.path.join(font_path, f"{regular_font_name}{extension}")
            bold_font_file = os.path.join(font_path, f"{bold_font_name}{extension}")

            fonts_registered = False

            if os.path.exists(regular_font_file):
                try:
                    if extension == '.otf':
                        try:
                            pdfmetrics.registerFont(TTFont(regular_font_name, regular_font_file))
                            base_font = regular_font_name
                        except:
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

            if os.path.exists(bold_font_file) and fonts_registered:
                try:
                    if extension == '.otf':
                        try:
                            pdfmetrics.registerFont(TTFont(bold_font_name, bold_font_file))
                            bold_font = bold_font_name
                        except:
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

        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                topMargin=1 * inch,
                                bottomMargin=1 * inch,
                                leftMargin=0.75 * inch,
                                rightMargin=0.75 * inch,
                                title='Mental Health Assessment Report',
                                author='Mentivio Clinical System',
                                subject='Clinical Mental Health Assessment',
                                creator='Mentivio v3.0',
                                keywords='mental health, assessment, clinical, report',
                                lang=language)

        styles = getSampleStyleSheet()

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

        emergency_style = ParagraphStyle(
            'Emergency',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=9,
            textColor=colors.red,
            backColor=colors.yellow,
            spaceBefore=10,
            spaceAfter=10,
            borderPadding=5,
            borderWidth=1,
            borderColor=colors.red,
            borderRadius=2
        )

        story = []

        title_text = pdf_translations.get('title', 'MENTAL HEALTH ASSESSMENT REPORT')
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 20))

        if safety_warnings and any('suicidal' in warning.lower() for warning in safety_warnings):
            emergency_text = pdf_translations.get('emergency_disclaimer',
                '**EMERGENCY NOTICE:** This assessment is NOT a substitute for professional medical advice. If you are experiencing a medical emergency, suicidal thoughts, or immediate danger, please call emergency services immediately.')
            story.append(Paragraph(emergency_text, emergency_style))
            story.append(Spacer(1, 10))

        assessment_details = pdf_translations.get('assessment_details', 'ASSESSMENT DETAILS')
        story.append(Paragraph(assessment_details, heading_style))

        meta_data = [
            [pdf_translations.get('assessment_id', 'Assessment ID:'), pdf_data.get('id', 'N/A')],
            [pdf_translations.get('assessment_started', 'Assessment Started:'), pdf_data.get('assessment_timestamp', 'N/A')],
            [pdf_translations.get('report_generated', 'Report Generated:'), pdf_data.get('timestamp', 'N/A')],
            [pdf_translations.get('assessment_timezone', 'Timezone:'), pdf_data.get('timezone', 'UTC')]
        ]

        meta_table = Table(meta_data, colWidths=[2 * inch, 4 * inch])
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

        patient_info_title = pdf_translations.get('patient_info', 'PATIENT INFORMATION')
        story.append(Paragraph(patient_info_title, heading_style))

        patient_data = [
            [pdf_translations.get('patient_name', 'Patient Name:'), patient_info.get('name', pdf_translations.get('not_provided', 'Not provided'))],
            [pdf_translations.get('patient_number', 'Patient Number:'), patient_info.get('number', pdf_translations.get('not_provided', 'Not provided'))],
            [pdf_translations.get('age', 'Age:'), patient_info.get('age', pdf_translations.get('not_provided', 'Not provided'))],
            [pdf_translations.get('gender_title', 'Gender:'), patient_info.get('gender', pdf_translations.get('not_provided', 'Not provided'))]
        ]

        patient_table = Table(patient_data, colWidths=[1.5 * inch, 4.5 * inch])
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

        clinical_results = pdf_translations.get('clinical_results', 'CLINICAL ASSESSMENT RESULTS')
        story.append(Paragraph(clinical_results, heading_style))

        confidence = confidence_percentage

        diagnosis_data = [
            [pdf_translations.get('primary_diagnosis', 'Primary Diagnosis:'), primary_diagnosis],
            [pdf_translations.get('confidence_level', 'Confidence Level:'), f"{confidence:.1f}%"],
            [pdf_translations.get('assessment_datetime', 'Assessment Date & Time:'), pdf_data.get('timestamp', 'N/A')]
        ]

        confidence_color = colors.HexColor('#10b981')
        if confidence < 70:
            confidence_color = colors.HexColor('#f59e0b')
        if confidence < 50:
            confidence_color = colors.HexColor('#ef4444')

        diagnosis_table = Table(diagnosis_data, colWidths=[2 * inch, 4 * inch])
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

        assessment_summary_title = pdf_translations.get('assessment_summary', 'Assessment Summary:')
        story.append(Paragraph(assessment_summary_title, heading_style))
        story.append(Paragraph(diagnosis_description, normal_style))
        story.append(Spacer(1, 20))

        differential_diagnoses = pdf_translations.get('differential_diagnoses', 'DIFFERENTIAL DIAGNOSES')
        story.append(Paragraph(differential_diagnoses, heading_style))

        if all_diagnoses and len(all_diagnoses) > 1:
            diagnoses_data = [[pdf_translations.get('diagnosis', 'Diagnosis'),
                               pdf_translations.get('probability', 'Probability')]]

            for diagnosis in all_diagnoses[1:5]:
                diagnosis_name = diagnosis.get('diagnosis', 'N/A')
                confidence_percent = diagnosis.get('confidence_percentage', 0)
                diagnoses_data.append([
                    diagnosis_name,
                    f"{confidence_percent:.1f}%"
                ])

            diagnoses_table = Table(diagnoses_data, colWidths=[4 * inch, 1.5 * inch])
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

        key_responses = pdf_translations.get('key_responses', 'ASSESSMENT QUESTIONS & ANSWERS')
        story.append(Paragraph(key_responses, heading_style))

        if questions_and_answers:
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

        important_disclaimer = pdf_translations.get('important_disclaimer', 'IMPORTANT MEDICAL DISCLAIMER')
        story.append(Paragraph(important_disclaimer, heading_style))
        disclaimer_text = pdf_translations.get('disclaimer_text',
            'This assessment is for informational purposes only and is NOT a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.')
        story.append(Paragraph(disclaimer_text, normal_style))
        story.append(Spacer(1, 10))

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


# Error handlers
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    else:
        try:
            return send_from_directory(app.static_folder, 'home.html')
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