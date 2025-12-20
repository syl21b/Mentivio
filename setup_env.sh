#!/bin/bash

echo "Setting up Mentivio Environment Variables"
echo "========================================="


SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(64))")
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ADMIN_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
PORT=${PORT:-5001}

ENVIRONMENT=${ENVIRONMENT:-development}

# Create .env file
cat > .env << EOF
# ==================== DATABASE CONFIGURATION ====================
DATABASE_URL=postgresql://neondb_owner:npg_lE1rHQG4AUfp@ep-icy-sea-aezfipy1-pooler.c-2.us-east-2.aws.neon.tech/assessment?sslmode=require&channel_binding=require

# ==================== SECURITY KEYS ====================
SECRET_KEY=$SECRET_KEY
ENCRYPTION_KEY=$ENCRYPTION_KEY
ADMIN_TOKEN=$ADMIN_TOKEN

# ==================== SECURITY SETTINGS ====================
SESSION_TIMEOUT=1800
CSRF_TOKEN_TIMEOUT=3600
MAX_FILE_SIZE=10485760
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60

# ==================== APPLICATION SETTINGS ====================
PORT=$PORT
ENVIRONMENT=$ENVIRONMENT
RENDER=false
LOG_LEVEL=INFO

# ==================== MODEL & AI SETTINGS ====================
CONFIDENCE_THRESHOLD=0.6
MODEL_INPUT_SANITIZATION=true
MODEL_OUTPUT_VALIDATION=true

# ==================== OPTIMIZATION SETTINGS ====================
MAX_INPUT_LENGTH=200
MAX_RESPONSES=30
MAX_ASSESSMENTS_PER_PATIENT=100
DATABASE_CONNECTION_TIMEOUT=30

# ==================== CORS & DOMAIN SETTINGS ====================
ALLOWED_ORIGINS=https://mentivio-web.onrender.com,http://localhost:3000,http://localhost:5001

# ==================== FEATURE FLAGS ====================
FEATURE_PDF_REPORT=true
FEATURE_INTELLIGENT_ENHANCER=true
FEATURE_TRANSLATION_CACHE=true
FEATURE_DB_COMPRESSION=true
EOF

echo "✅ .env file created successfully!"
echo "🔑 Secret Key: $SECRET_KEY"
echo "🔐 Encryption Key: $ENCRYPTION_KEY"
echo "🛡️  Admin Token: $ADMIN_TOKEN"
echo ""
echo "Next steps:"
echo "1. Update DATABASE_URL with your actual database connection"
echo "2. Set RENDER=true if deploying to Render"
echo "3. Run: source .env"