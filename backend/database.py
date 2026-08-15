import os
import json
import logging
import psycopg
from psycopg.rows import dict_row
import psycopg_pool
import sqlite3
from typing import Dict, List, Tuple, Optional, Any
from functools import lru_cache

from security import SecurityUtils

logger = logging.getLogger(__name__)

# Global connection pool
connection_pool = None

def init_connection_pool():
    """Initialize PostgreSQL connection pool."""
    global connection_pool
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.warning("DATABASE_URL not set, connection pool disabled")
            return
        
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        # Tuned pool: min 1, max 5 – adjust based on your concurrency needs
        connection_pool = psycopg_pool.ConnectionPool(
            database_url,
            min_size=1,
            max_size=5,
            max_idle=300,          # 5 minutes idle timeout
            max_lifetime=3600,      # 1 hour max connection lifetime
            open=False,
            kwargs={"row_factory": dict_row}
        )
        connection_pool.open()
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        connection_pool = None

def get_postgres_connection():
    """Get a database connection from the pool, or fallback to direct connection."""
    global connection_pool
    if connection_pool:
        try:
            return connection_pool.getconn()
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            # fall through to direct connection
    return get_postgres_connection_direct()

def get_postgres_connection_direct():
    """Direct connection (fallback if pool not available)."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        conn = psycopg.connect(database_url, row_factory=dict_row)
        return conn
    except Exception as e:
        logger.error(f"Direct PostgreSQL connection failed: {e}")
        # SQLite fallback
        try:
            sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mental_health_assessments.db')
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row
            logger.info("SQLite fallback connection successful")
            return conn
        except Exception as sqlite_error:
            logger.error(f"SQLite fallback also failed: {sqlite_error}")
            raise e

def close_connection(conn):
    """Return connection to pool or close it."""
    global connection_pool
    if connection_pool and hasattr(conn, 'pgconn'):  # it's a psycopg connection from pool
        connection_pool.putconn(conn)
    elif conn:
        conn.close()

def init_database():
    """Initialize database with required tables and indexes."""
    conn = None
    try:
        conn = get_postgres_connection()
        with conn.cursor() as cur:
            # ... (assessments table remains unchanged) ...

            # ------------------------------------------------------------
            # 2. MOOD MESSAGES TABLE (with name, age, location_name)
            # ------------------------------------------------------------
            cur.execute('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'mood_messages'
                );
            ''')
            mood_table_exists = cur.fetchone()['exists']
            
            if not mood_table_exists:
                cur.execute('''
                    CREATE TABLE mood_messages (
                        id TEXT PRIMARY KEY,
                        lat REAL NOT NULL,
                        lng REAL NOT NULL,
                        emoji TEXT NOT NULL,
                        text TEXT NOT NULL,
                        name TEXT,
                        age INT,
                        location_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cur.execute('CREATE INDEX idx_mood_created ON mood_messages(created_at DESC)')
                logger.info("Created mood_messages table with name, age, location_name")
            else:
                # Add new columns if they don't exist
                for col in ['name', 'age', 'location_name']:
                    cur.execute(f'''
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'mood_messages' AND column_name = '{col}';
                    ''')
                    if not cur.fetchone():
                        if col == 'age':
                            cur.execute(f'ALTER TABLE mood_messages ADD COLUMN {col} INT;')
                        else:
                            cur.execute(f'ALTER TABLE mood_messages ADD COLUMN {col} TEXT;')
                        logger.info(f"Added column {col} to mood_messages")
                
                # Ensure index exists
                cur.execute('''
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = 'mood_messages' AND indexname = 'idx_mood_created';
                ''')
                if not cur.fetchone():
                    cur.execute('CREATE INDEX idx_mood_created ON mood_messages(created_at DESC)')
                    logger.info("Added index idx_mood_created to mood_messages")

        conn.commit()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    finally:
        if conn:
            close_connection(conn)
            
@lru_cache(maxsize=128)
def convert_to_canonical_key(diagnosis_text: str) -> str:
    """Convert any diagnosis text back to its canonical key (cached)."""
    canonical_keys = ['Normal', 'Bipolar Type-1', 'Bipolar Type-2', 'Depression']

    if diagnosis_text in canonical_keys:
        return diagnosis_text

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

        coded_responses = sanitized_data.get('coded_responses', {})

        logger.info(f"Database save - Coded responses: {json.dumps(coded_responses)[:200]}")

        # Serialize JSON once
        all_diagnoses_json = json.dumps(canonical_diagnoses)
        coded_responses_json = json.dumps(coded_responses)
        processing_json = json.dumps(sanitized_data.get('processing_details', {}))
        technical_json = json.dumps(sanitized_data.get('technical_details', {}))
        clinical_json = json.dumps(sanitized_data.get('clinical_insights', {}))

        conn = get_postgres_connection()

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
                all_diagnoses_json,
                coded_responses_json,
                processing_json,
                technical_json,
                clinical_json
            ))

        conn.commit()
        close_connection(conn)

        logger.info(f"Successfully saved assessment {sanitized_data.get('id')}")
        return True

    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        if conn:
            try:
                conn.rollback()
                close_connection(conn)
            except:
                pass
        return False


def load_assessments_from_db(patient_number: str = None) -> Dict[str, List[Dict[str, Any]]]:
    """Load assessments from database (explicit columns)."""
    try:
        conn = get_postgres_connection()

        with conn.cursor() as cur:
            if patient_number:
                cur.execute('''
                    SELECT id, assessment_timestamp, report_timestamp, timezone,
                           patient_name, patient_number, patient_age, patient_gender,
                           primary_diagnosis, confidence, confidence_percentage,
                           all_diagnoses_json, coded_responses_json,
                           processing_details_json, technical_details_json, clinical_insights_json
                    FROM assessments 
                    WHERE patient_number ILIKE %s 
                    ORDER BY report_timestamp DESC
                ''', (f'%{patient_number}%',))
            else:
                cur.execute('''
                    SELECT id, assessment_timestamp, report_timestamp, timezone,
                           patient_name, patient_number, patient_age, patient_gender,
                           primary_diagnosis, confidence, confidence_percentage,
                           all_diagnoses_json, coded_responses_json,
                           processing_details_json, technical_details_json, clinical_insights_json
                    FROM assessments 
                    ORDER BY report_timestamp DESC
                ''')

            rows = cur.fetchall()

        close_connection(conn)

        assessments_by_patient: Dict[str, List[Dict[str, Any]]] = {}

        for row in rows:
            row_dict = dict(row)

            patient_num = row_dict['patient_number']
            if patient_num not in assessments_by_patient:
                assessments_by_patient[patient_num] = []

            # JSON fields are already parsed as dicts because of JSONB + dict_row
            all_diagnoses_canonical = row_dict['all_diagnoses_json'] or []
            coded_responses = row_dict['coded_responses_json'] or {}
            processing_details = row_dict['processing_details_json'] or {}
            technical_details = row_dict['technical_details_json'] or {}
            clinical_insights = row_dict['clinical_insights_json'] or {}

            primary_diagnosis_canonical = row_dict['primary_diagnosis']

            if primary_diagnosis_canonical not in ['Normal', 'Bipolar Type-1', 'Bipolar Type-2', 'Depression']:
                primary_diagnosis_canonical = convert_to_canonical_key(primary_diagnosis_canonical)

            primary_diagnosis = primary_diagnosis_canonical

            assessments = []
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

            assessment = {
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
    """Load a single specific assessment from database (explicit columns)."""
    try:
        conn = get_postgres_connection()

        with conn.cursor() as cur:
            cur.execute('''
                SELECT id, assessment_timestamp, report_timestamp, timezone,
                       patient_name, patient_number, patient_age, patient_gender,
                       primary_diagnosis, confidence, confidence_percentage,
                       all_diagnoses_json, coded_responses_json,
                       processing_details_json, technical_details_json, clinical_insights_json
                FROM assessments 
                WHERE patient_number = %s AND id = %s AND patient_name = %s
            ''', (patient_number, assessment_id, patient_name))

            row = cur.fetchone()

            if not row:
                close_connection(conn)
                return None

        row_dict = dict(row)
        close_connection(conn)

        if not row_dict:
            return None

        # JSON fields automatically parsed
        coded_responses = row_dict['coded_responses_json'] or {}
        all_diagnoses = row_dict['all_diagnoses_json'] or []
        processing_details = row_dict['processing_details_json'] or {}
        technical_details = row_dict['technical_details_json'] or {}
        clinical_insights = row_dict['clinical_insights_json'] or {}

        primary_diagnosis = row_dict.get('primary_diagnosis', '')

        if primary_diagnosis not in ['Normal', 'Bipolar Type-1', 'Bipolar Type-2', 'Depression']:
            primary_diagnosis = convert_to_canonical_key(primary_diagnosis)

        assessments = []
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

        assessment = {
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
            close_connection(conn)
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
        close_connection(conn)

        return True

    except Exception as e:
        logger.error(f"Error deleting from database: {e}")
        return False

def close_connection_pool():
    """Close the global connection pool (used at shutdown)."""
    global connection_pool
    if connection_pool:
        try:
            connection_pool.close()
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")
        finally:
            connection_pool = None

