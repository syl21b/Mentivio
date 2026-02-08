# compliance_backend.py
from flask import Blueprint, request, jsonify
import os
import hashlib
import json
from datetime import datetime, timedelta
import logging
from functools import wraps

compliance_bp = Blueprint('compliance', __name__)

# Compliance status
COMPLIANCE_CONFIG = {
    'hipaa_compliant': os.environ.get('HIPAA_COMPLIANT', 'true').lower() == 'true',
    'gdpr_compliant': True,
    'soc2_certified': os.environ.get('SOC2_CERTIFIED', 'false').lower() == 'true',
    'data_retention_days': 30,
    'encryption_level': 'AES-256-GCM',
    'data_center_location': os.environ.get('DATA_CENTER_LOCATION', 'US-East-1'),
    'audit_logging': True
}

# Audit log storage (in production, use database)
audit_logs = []

def audit_log(action, user_id=None, details=None):
    """Log compliance-related actions"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': action,
        'user_id_hash': hash_user_id(user_id) if user_id else 'anonymous',
        'details': details,
        'ip_hash': hash_ip(request.remote_addr) if request.remote_addr else None,
        'user_agent': request.user_agent.string if request.user_agent else None
    }
    
    audit_logs.append(log_entry)
    
    # Keep only last 10,000 logs in memory (in production, use database)
    if len(audit_logs) > 10000:
        audit_logs.pop(0)
    
    return log_entry

def hash_user_id(user_id):
    """Create anonymous hash of user ID for auditing"""
    if not user_id:
        return 'anonymous'
    return hashlib.sha256(f"{user_id}-{os.environ.get('SALT', '')}".encode()).hexdigest()[:16]

def hash_ip(ip_address):
    """Create anonymous hash of IP address"""
    if not ip_address:
        return None
    return hashlib.sha256(f"{ip_address}-{os.environ.get('SALT', '')}".encode()).hexdigest()[:16]

def require_consent(f):
    """Decorator to check user consent"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        consent_header = request.headers.get('X-User-Consent')
        
        if not consent_header:
            return jsonify({
                'error': 'Consent required',
                'message': 'Please provide consent to use this service',
                'consent_url': '/api/compliance/consent'
            }), 403
        
        try:
            consent_data = json.loads(consent_header)
            if not consent_data.get('accepted'):
                return jsonify({'error': 'Consent not accepted'}), 403
        except:
            return jsonify({'error': 'Invalid consent header'}), 400
        
        return f(*args, **kwargs)
    return decorated_function

@compliance_bp.route('/api/compliance/status', methods=['GET'])
def get_compliance_status():
    """Return compliance status for frontend"""
    audit_log('compliance_status_check')
    
    return jsonify({
        **COMPLIANCE_CONFIG,
        'timestamp': datetime.utcnow().isoformat(),
        'api_version': '2.0',
        'features': {
            'data_encryption': True,
            'data_deletion': True,
            'data_export': True,
            'audit_trail': True,
            'crisis_escalation': True
        }
    })

@compliance_bp.route('/api/compliance/consent', methods=['POST'])
def handle_consent():
    """Handle user consent"""
    data = request.get_json()
    
    consent_data = {
        'accepted': data.get('accepted', False),
        'analytics': data.get('analytics', False),
        'local_storage': data.get('local_storage', False),
        'timestamp': datetime.utcnow().isoformat(),
        'ip_hash': hash_ip(request.remote_addr),
        'user_agent_hash': hashlib.sha256(
            (request.user_agent.string or '').encode()
        ).hexdigest()[:16] if request.user_agent else None
    }
    
    audit_log('consent_given', details=consent_data)
    
    return jsonify({
        'status': 'success',
        'consent_id': hashlib.md5(json.dumps(consent_data).encode()).hexdigest(),
        'message': 'Consent recorded',
        'data_retention_days': COMPLIANCE_CONFIG['data_retention_days']
    })

@compliance_bp.route('/api/compliance/export', methods=['POST'])
@require_consent
def export_user_data():
    """GDPR Right to Access - Export user data"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    # In production, fetch from database
    user_data = {
        'conversations': [],  # Fetch from DB
        'settings': {},       # Fetch from DB
        'consent_history': [] # Fetch from DB
    }
    
    audit_log('data_export', user_id)
    
    return jsonify({
        'data': user_data,
        'exported_at': datetime.utcnow().isoformat(),
        'format': 'json',
        'encryption_key': os.environ.get('EXPORT_ENCRYPTION_KEY', '')[:32]
    })

@compliance_bp.route('/api/compliance/delete', methods=['POST'])
@require_consent
def delete_user_data():
    """GDPR Right to be Forgotten - Delete user data"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    # In production:
    # 1. Anonymize conversations
    # 2. Delete personal data
    # 3. Keep audit logs (anonymized)
    
    audit_log('data_deletion', user_id, {'scope': 'all_data'})
    
    return jsonify({
        'status': 'success',
        'message': 'Data deletion scheduled',
        'deletion_id': hashlib.md5(f"{user_id}{datetime.utcnow()}".encode()).hexdigest(),
        'completion_time': (datetime.utcnow() + timedelta(hours=24)).isoformat()
    })

@compliance_bp.route('/api/compliance/audit', methods=['GET'])
def get_audit_logs():
    """Get audit logs (admin only)"""
    # Check admin authentication (implement properly)
    admin_key = request.headers.get('X-Admin-Key')
    
    if admin_key != os.environ.get('ADMIN_KEY'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'logs': audit_logs[-1000:],  # Last 1000 logs
        'total_count': len(audit_logs),
        'generated_at': datetime.utcnow().isoformat()
    })

@compliance_bp.route('/api/compliance/crisis-report', methods=['POST'])
def report_crisis_intervention():
    """Log crisis intervention for compliance reporting"""
    data = request.get_json()
    
    report = {
        'type': data.get('type', 'crisis_detected'),
        'severity': data.get('severity', 'high'),
        'language': data.get('language', 'en'),
        'resources_provided': data.get('resources', []),
        'timestamp': datetime.utcnow().isoformat(),
        'ip_hash': hash_ip(request.remote_addr),
        'user_agent_hash': hashlib.sha256(
            (request.user_agent.string or '').encode()
        ).hexdigest()[:16] if request.user_agent else None
    }
    
    audit_log('crisis_intervention', details=report)
    
    return jsonify({
        'status': 'reported',
        'report_id': hashlib.md5(json.dumps(report).encode()).hexdigest()
    })