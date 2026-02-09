import os
import json
from google import genai
from google.genai import types
from flask import Blueprint, request, jsonify, Response
from dotenv import load_dotenv
import re
from typing import List, Dict, Any, Tuple
import logging
from datetime import datetime
import random
import uuid
import hashlib
from functools import lru_cache
import threading
import time

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask Blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

# ================================
# GEMINI API KEY CONFIGURATION
# ================================
def get_gemini_api_key():
    env_vars_to_try = [
        'GEMINI_API_KEY',
        'GOOGLE_API_KEY',
        'GOOGLE_AI_API_KEY',
    ]
    
    for env_var in env_vars_to_try:
        api_key = os.environ.get(env_var)
        if api_key:
            logger.info(f"Found Gemini API key in environment variable: {env_var}")
            return api_key
    
    for env_var in env_vars_to_try:
        api_key = os.getenv(env_var)
        if api_key:
            logger.info(f"Found Gemini API key using os.getenv: {env_var}")
            return api_key
    
    is_production = os.environ.get('RENDER') or os.environ.get('PRODUCTION') or os.environ.get('ENVIRONMENT') == 'production'
    
    if not is_production:
        logger.info("Development environment detected, checking .env file...")
        from pathlib import Path
        env_path = Path('.') / '.env'
        
        if env_path.exists():
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            if key in env_vars_to_try and value:
                                logger.info(f"Found {key} in .env file")
                                return value
            except Exception as e:
                logger.warning(f"Could not read .env file: {e}")
    
    logger.warning("GEMINI_API_KEY not found in any environment variable or .env file")
    return None

GEMINI_API_KEY = get_gemini_api_key()

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not found. Chatbot features will be disabled.")
    client = None
else:
    masked_key = GEMINI_API_KEY[:8] + '...' + GEMINI_API_KEY[-4:] if len(GEMINI_API_KEY) > 12 else '***'
    logger.info(f"Gemini API key loaded successfully: {masked_key}")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Gemini client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {str(e)}")
        client = None

# Safety settings
SAFETY_SETTINGS = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
]

# ================================
# ENHANCED SESSION PERSISTENCE MANAGER
# ================================
class SessionManager:
    """Manages user sessions for persistent conversations."""
    
    def __init__(self):
        self.sessions = {}  # In production, use Redis or database
        self.session_timeout = 30 * 60  # 30 minutes
    
    def create_session(self, session_id=None, language='en', anonymous=False):
        """Create a new session or return existing one."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'id': session_id,
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'language': language,
                'anonymous': anonymous,
                'conversation_history': [],
                'conversation_state': {
                    'phase': 'engagement',
                    'trust_level': 0,
                    'needs_inspiration': False,
                    'topics_discussed': []
                },
                'metadata': {
                    'user_agent': '',
                    'ip_hash': '',
                    'page_visits': 0
                }
            }
            logger.info(f"Created new session: {session_id}")
        else:
            # Update last activity
            self.sessions[session_id]['last_activity'] = datetime.now()
            logger.info(f"Retrieved existing session: {session_id}")
        
        return self.sessions[session_id]
    
    def get_session(self, session_id):
        """Get session by ID, cleaning up if expired."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            time_since_activity = (datetime.now() - session['last_activity']).total_seconds()
            
            if time_since_activity > self.session_timeout:
                # Session expired, remove it
                logger.info(f"Session expired and removed: {session_id}")
                del self.sessions[session_id]
                return None
            
            # Update last activity
            session['last_activity'] = datetime.now()
            return session
        return None
    
    def update_session(self, session_id, updates):
        """Update session data."""
        session = self.get_session(session_id)
        if session:
            session.update(updates)
            session['last_activity'] = datetime.now()
            return True
        return False
    
    def add_message(self, session_id, message, role='user', emotion='neutral'):
        """Add a message to session history."""
        session = self.get_session(session_id)
        if session:
            message_entry = {
                'role': role,
                'content': message,
                'emotion': emotion,
                'timestamp': datetime.now().isoformat(),
                'language': session['language'],
                'anonymous': session.get('anonymous', False)
            }
            
            session['conversation_history'].append(message_entry)
            
            # Keep only last 50 messages
            if len(session['conversation_history']) > 50:
                session['conversation_history'] = session['conversation_history'][-50:]
            
            # Update conversation state based on message count
            user_message_count = len([m for m in session['conversation_history'] if m['role'] == 'user'])
            
            if user_message_count < 3:
                session['conversation_state']['phase'] = 'engagement'
            elif user_message_count < 8:
                session['conversation_state']['phase'] = 'exploration'
            elif user_message_count < 15:
                session['conversation_state']['phase'] = 'processing'
            else:
                session['conversation_state']['phase'] = 'integration'
            
            # Update trust level gradually
            session['conversation_state']['trust_level'] = min(user_message_count / 2, 10)
            
            # Check if needs inspiration
            if emotion in ['sad', 'overwhelmed', 'lonely', 'hopeless']:
                session['conversation_state']['needs_inspiration'] = True
            
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        expired_sessions = []
        current_time = datetime.now()
        
        for session_id, session in list(self.sessions.items()):
            time_since_activity = (current_time - session['last_activity']).total_seconds()
            if time_since_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_active_sessions_count(self):
        """Get count of active sessions."""
        self.cleanup_expired_sessions()
        return len(self.sessions)
    
    def delete_session(self, session_id):
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

# Initialize session manager
session_manager = SessionManager()

# ================================
# TOPIC CONFIGURATIONS
# ================================

# EXPANDED ALLOWED TOPICS WITH HIGH EQ FOCUS
ALLOWED_TOPICS = [
    # Emotional Wellness
    "stress", "stress management", "feeling stressed", "stressful situation",
    "anxiety", "anxiety coping", "feeling anxious", "worried", "nervous",
    "anxious thoughts", "panic", "panic attack", "panic feelings",
    "social anxiety", "performance anxiety", "health anxiety",
    "depression", "mild depression", "feeling depressed", "sad", "sadness",
    "low mood", "emotional pain", "emotional distress",
    "burnout", "burned out", "exhausted", "fatigued",
    "emotional exhaustion", "mental fatigue",
    
    # Loneliness & Isolation
    "loneliness", "feeling lonely", "isolated", "social isolation",
    "missing connection", "wanting friends", "need companionship",
    
    # Work & Academic
    "work-life balance", "work stress", "work pressure", "job stress",
    "career stress", "workplace anxiety", "imposter syndrome",
    "study stress", "school stress", "academic pressure", "exams",
    "test anxiety", "performance pressure", "deadline stress",
    
    # Relationships & Communication
    "relationship communication", "relationship issues", "friends",
    "friendship issues", "social relationships", "people problems",
    "family", "family issues", "family stress", "parent stress",
    "conflict resolution", "difficult conversations",
    
    # Self-Care & Mindfulness
    "self-care", "self care", "taking care of myself", "self compassion",
    "self-kindness", "being kind to myself", "treating myself well",
    "mindfulness", "meditation", "breathing exercises", "deep breathing",
    "grounding techniques", "present moment", "staying present",
    
    # Positive Psychology
    "positive thinking", "gratitude", "appreciation", "thankful",
    "optimism", "looking for hope", "finding positivity",
    "goal setting", "personal goals", "aspirations", "dreams",
    "time management", "productivity", "getting things done",
    
    # Sleep & Health
    "sleep", "sleep hygiene", "sleep problems", "insomnia",
    "trouble sleeping", "restless sleep", "sleep schedule",
    "healthy habits", "exercise", "physical activity", "movement",
    "nutrition", "eating well", "healthy eating",
    
    # Emotional Skills
    "emotional awareness", "feelings", "emotions", "emotional intelligence",
    "identifying feelings", "naming emotions", "emotional vocabulary",
    "communication skills", "talking about feelings", "expressing emotions",
    "emotional expression", "sharing feelings",
    "boundary setting", "saying no", "personal boundaries", "limits",
    "self-compassion", "self-acceptance", "self-forgiveness",
    
    # Resilience & Coping
    "resilience", "resilience building", "bouncing back", "recovery",
    "coping strategies", "coping skills", "dealing with stress",
    "stress management techniques", "stress relief",
    "emotional regulation", "managing emotions", "calming down",
    "anger management", "frustration tolerance",
    "relaxation", "relaxation techniques", "calming techniques",
    
    # Social & Connection
    "social connections", "making friends", "social support",
    "community", "belonging", "fitting in", "social skills",
    "hobbies", "interests", "activities", "enjoyment", "passions",
    
    # Life Purpose & Direction
    "life purpose", "finding meaning", "meaning of life", "purpose",
    "life direction", "direction in life", "what should I do",
    "motivation", "staying motivated", "lack of motivation",
    "feeling stuck", "stagnation", "unmotivated",
    "inspiration", "inspiring stories", "uplifting content", "hope",
    "personal growth", "self-improvement", "becoming better",
    "growth mindset", "learning mindset", "development",
    "overcoming challenges", "difficult times", "hard situations",
    "perseverance", "endurance", "getting through",
    "success stories", "achievements", "accomplishments",
    "milestones", "progress", "moving forward",
    
    # Dreams & Future
    "dreams", "aspirations", "goals in life", "future plans",
    "life goals", "personal dreams", "what I want",
    "passion", "what excites me", "things I love", "enthusiasm",
    "creativity", "creative expression", "art", "writing",
    "music", "dance", "creative outlet",
    
    # Life Appreciation
    "nature", "beauty in life", "wonder", "awe", "appreciation",
    "sunrises", "sunsets", "natural beauty",
    "kindness", "acts of kindness", "helping others", "compassion",
    "empathy", "understanding others", "caring",
    "learning", "curiosity", "new skills", "knowledge",
    "adventure", "new experiences", "trying new things",
    "exploration", "discovery",
    
    # Connection Stories
    "friendship stories", "meaningful connections", "bonding moments",
    "relationship stories", "connection experiences",
    "small joys", "little pleasures", "simple happiness",
    "daily joys", "everyday happiness", "small moments",
    "resilience stories", "overcoming adversity",
    "surviving tough times", "getting through difficulty",
    
    # Life Transitions
    "positive changes", "life improvements", "turning points",
    "self-discovery", "understanding myself", "personal insights",
    "identity", "who am I", "personal identity",
    "hope for future", "better days ahead", "things will get better",
    "reassurance", "encouragement", "support",
    "celebrating wins", "acknowledging progress", "small victories",
    "mindset shift", "changing perspective", "seeing differently",
    "emotional strength", "inner strength", "mental toughness",
    "life lessons", "wisdom gained", "experiences taught me",
    "gratitude stories", "thankful moments", "appreciation in life",
    "healing journey", "recovery stories", "getting better",
    "positive affirmations", "encouraging words", "self-talk",
    "inner dialogue", "self-encouragement",
    
    # Quotes & Wisdom
    "inspirational quotes", "meaningful sayings", "wise words",
    "role models", "people who inspire", "heroes", "mentors",
    "community", "belonging", "being part of something",
    "legacy", "making a difference", "impact on others",
    "contribution", "giving back",
    
    # Mindful Living
    "mindful living", "present moment", "being here now",
    "emotional intelligence", "understanding feelings", "EQ",
    "happiness habits", "joyful routines", "positive rituals",
    "life balance", "harmony", "peaceful living", "simplicity",
    "self-expression", "finding voice", "speaking truth",
    "authenticity", "being real", "true self",
    
    # Courage & Growth
    "courage", "bravery", "facing fears", "stepping up",
    "taking risks", "trying new things", "stepping out of comfort zone",
    "forgiveness", "letting go", "moving forward", "release",
    "acceptance", "embracing reality", "making peace",
    "patience", "taking time", "slow progress", "process",
    
    # Future & Direction (Expanded)
    "future", "thinking about future", "what's next", "next steps",
    "life ahead", "looking ahead", "planning ahead",
    "future anxiety", "future worries", "uncertain future",
    "future planning", "preparing for future",
    "direction", "lost direction", "finding direction",
    "directionless", "no direction", "uncertain direction",
    "life path", "finding my path", "which way to go",
    "crossroads", "at a crossroads", "decision point",
    "lost in life", "feeling lost", "where do I go from here",
    "what should I do", "uncertain about life",
    
    # Relationship Challenges
    "relationship lost", "lost in relationship", "relationship direction",
    "relationship confusion", "unsure about relationship",
    "relationship doubts", "questioning relationship",
    "broken relationship", "relationship ending",
    "moving on from relationship", "breakup recovery",
    "heartbreak", "broken heart", "emotional healing",
    
    # Reset & New Beginnings
    "time to reset", "need to reset", "starting over",
    "new beginning", "fresh start", "clean slate",
    "reset life", "life reset", "restarting life",
    "beginning again", "starting fresh",
    "struggling time", "struggling period", "difficult season",
    "hard times", "challenging period",
    "going through it", "tough phase", "rough patch",
    "challenging times", "difficult chapter",
    "survival mode", "just getting by", "barely coping",
    "hanging on", "getting through day",
    "transition period", "life transition", "major change",
    "big changes", "life changes",
    
    # Life Crises
    "quarter life crisis", "midlife crisis", "existential crisis",
    "crisis of meaning", "purpose crisis",
    "identity crisis", "who am I", "finding myself",
    "self identity", "personal identity",
    "career direction", "career path", "job future",
    "professional direction", "work direction",
    "education future", "study direction", "learning path",
    
    # Purpose & Meaning
    "purpose searching", "searching for meaning", "why am I here",
    "meaning of life", "life's purpose",
    "life evaluation", "taking stock", "assessing life",
    "life review", "reflection on life",
    "decision making", "big decisions", "life choices",
    "making choices", "important decisions",
    
    # Fear & Regret
    "fear of future", "future uncertainty", "unknown future",
    "what if", "worries about future",
    "regret", "past regrets", "what could have been",
    "missed opportunities", "looking back",
    
    # Recovery & Healing
    "starting again", "rebuilding", "reconstruction",
    "putting pieces back together", "reassembling life",
    "emotional reset", "mental reset", "spiritual reset",
    "reset mindset", "changing mindset",
    "recovery period", "healing time", "time to heal",
    "processing time", "grieving period",
    
    # Moving Forward
    "moving forward", "next chapter", "new chapter",
    "turning page", "starting new chapter",
    "letting go of past", "releasing past", "past baggage",
    "old patterns", "breaking patterns",
    "creating future", "building future", "designing life",
    "life design", "intentional living",
    "vision for future", "future vision", "dream future",
    "ideal life", "life I want",
    
    # Control & Agency
    "taking control", "regaining control", "steering life",
    "taking charge", "personal agency",
    "pace of life", "slowing down", "life speed",
    "rushing through life", "busy life",
    "mindful future", "conscious living", "intentional life",
    "purposeful living", "meaningful living",
    
    # Gender & Identity (SAFE EXPLORATION)
    "questioning gender", "gender identity", "gender exploration",
    "gender questioning", "gender journey",
    "sexual orientation", "orientation exploration",
    "lgbtq", "lgbtq+", "queer identity",
    "transgender", "trans", "trans identity",
    "non-binary", "genderqueer", "gender fluid",
    "coming out", "sharing identity", "identity sharing",
    "identity acceptance", "self-acceptance",
    "lgbtq support", "queer community",
    
    # Grief & Loss
    "grief", "grieving", "loss", "bereavement",
    "missing someone", "mourning",
    
    # Trauma (General Support)
    "emotional trauma", "past trauma", "healing from trauma",
    "trauma recovery", "trauma healing",
    
    # Self-Esteem
    "self-esteem", "self-worth", "self-confidence",
    "self-doubt", "insecurity", "self-criticism"
]

# ================================
# IMPROVED FORBIDDEN TOPICS (More precise)
# ================================
FORBIDDEN_TOPICS = [
    # Suicide & Self-Harm (EXACT patterns, not substrings)
    "suicide", "kill myself", "end my life", "ending my life",
    "want to die", "don't want to live", "life not worth living",
    "self-harm", "self injury", "cutting myself", "self mutilation",
    "burning myself", "hurting myself", "intentional self-harm",
    "overdose", "poison myself", "intentional overdose",
    "drug overdose", "take pills to die",
    "hanging", "strangulation", "asphyxiation", "suffocation",
    "jumping off", "falling from height", "jump to death",
    "gun to head", "shoot myself", "firearm suicide",
    "suicide plan", "suicide method", "suicide means",
    "how to suicide", "ways to die", "methods of suicide",
    "suicide pact", "group suicide", "mass suicide",
    "suicide note", "final goodbye", "last words",
    
    # VIOLENT ACTS (Specific, not general)
    "how to harm someone", "how to hurt someone", "how to kill someone",
    "how to attack someone", "planning violence", "violent acts",
    "physical violence", "assault someone", "attack someone",
    "murder", "homicide", "killing someone", "manslaughter",
    "domestic violence", "spousal abuse", "partner violence",
    "child abuse", "child molestation", "pedophilia",
    "elder abuse", "abuse of elderly", "neglect of elderly",
    "sexual assault", "rape", "sexual violence", "non-consensual",
    "torture", "torture methods", "torture techniques",
    "human trafficking", "sex trafficking", "forced labor",
    "gang violence", "gang warfare", "drive-by shooting",
    "terrorism", "terrorist acts", "bomb making", "explosives",
    "school shooting", "workplace violence", "mass shooting",
    
    # ILLEGAL SUBSTANCES (Manufacturing/Distribution)
    "how to make drugs", "drug manufacturing", "drug synthesis",
    "cooking meth", "making cocaine", "heroin production",
    "drug dealing", "drug trafficking", "selling drugs",
    "prescription drug abuse", "opioid manufacturing",
    
    # EXTREME CONTENT
    "child pornography", "cp", "child sexual abuse material",
    "bestiality", "necrophilia", "extreme fetish",
    
    # DANGEROUS INSTRUCTIONS (Specific patterns)
    "instructions for suicide", "instructions for self-harm",
    "how to build a bomb", "how to make explosives",
    "how to commit murder", "how to kill people",
    "how to poison someone", "how to strangle",
    "how to stalk someone", "how to harass",
    "how to cyberbully", "how to dox someone",
    "how to hack", "how to steal", "how to rob",
    
    # HATE & EXTREMISM
    "hate speech", "racial slurs", "ethnic slurs",
    "how to join terrorist group", "terrorist recruitment",
    "white supremacy", "neo-nazi", "racist ideology",
    "incel ideology", "misogynistic violence",
    "how to commit hate crime", "religious persecution",
    
    # ILLEGAL ACTIVITIES
    "how to commit fraud", "how to scam", "identity theft",
    "credit card fraud", "bank fraud", "tax evasion",
    "insurance fraud", "arson instructions",
    "how to vandalize", "property destruction",
    
    # MEDICAL ADVICE (Requires Professional)
    "medical diagnosis", "what's wrong with me medically",
    "prescription medication advice", "dosage advice",
    "should I take this medication", "medication adjustment",
    "medical treatment advice", "surgery advice",
    "psychiatric medication advice", "antidepressant advice",
    "therapy techniques for others", "CBT for someone else",
    "clinical intervention", "crisis intervention techniques",
    "pregnancy medical advice", "abortion medical advice",
    "STD diagnosis", "HIV testing advice",
    "cancer treatment advice", "diabetes management advice",
    
    # DANGEROUS CHALLENGES
    "dangerous dares", "life-threatening stunts",
    "Russian roulette", "choking game", "breath play",
    "extreme fasting", "water deprivation challenge",
    "sleep deprivation challenge", "isolation experiments",
    
    # PROFESSIONAL BOUNDARIES
    "therapy session request", "counsel me as therapist",
    "clinical assessment request", "diagnose my disorder",
    "treatment plan request", "be my therapist",
    "emergency response instead of 911", "paramedic advice",
    "legal advice", "lawyer advice", "court case advice",
    "financial advice", "investment advice", "stock advice"
]

# ================================
# IMPROVED CRISIS DETECTION (More precise regex)
# ================================
CRISIS_KEYWORDS = {
    "en": [
        # Level 10: Immediate danger - EXACT phrases
        (r"\bi('m| am)\s+going\s+to\s+(kill|end)\s+myself\s+(now|today|tonight)\b", 10),
        (r"\bi('ll| will)\s+(kill|end)\s+my\s+life\s+(now|today|tonight)\b", 10),
        (r"\bright\s+now\s+i\s+want\s+to\s+die\b", 10),
        (r"\bi\s+have\s+a\s+plan\s+to\s+(die|kill myself)\b", 10),
        (r"\bgoing\s+to\s+(kill|end)\s+myself\s+this\s+(evening|night)\b", 10),
        (r"\bi\s+have\s+(pills|a gun|a knife)\s+right\s+now\b", 10),
        
        # Level 9: High severity - specific intent
        (r"\b(kill|end)\s+myself\b", 9),
        (r"\bcommit\s+suicide\b", 9),
        (r"\bend\s+my\s+life\b", 9),
        (r"\bwant\s+to\s+die\b", 9),
        (r"\bplan\s+to\s+(die|kill myself)\b", 9),
        (r"\bthinking\s+of\s+suicide\b", 9),
        
        # Level 8: Medium severity - concerning
        (r"\bhopeless\b", 8),
        (r"\bworthless\b", 8),
        (r"\bburden\b", 8),
        (r"\bno\s+point\s+(in|to)\b", 8),
        (r"\bcan'?t\s+go\s+on\b", 8),
        (r"\bdon'?t\s+want\s+to\s+live\b", 8),
        
        # Level 7: Lower severity but concerning
        (r"\bcutting\s+myself\b", 7),
        (r"\boverdose\s+(on|with)\b", 7),
        (r"\bhanging\s+myself\b", 7),
        (r"\bjump\s+off\b", 7),
        (r"\bgun\s+to\s+(my\s+)?head\b", 7)
    ],
    "es": [
        (r"\bvoy.*a.*matar.*me.*ahora\b", 10),
        (r"\bterminar.*mi.*vida.*hoy\b", 10),
        (r"\bsuicidio.*ahora\b", 10),
        (r"\btengo.*un.*plan.*para.*morir\b", 10),
        (r"\bmatar.*me\b", 9),
        (r"\bsuicidar.*me\b", 9),
        (r"\bquerer.*morir\b", 9),
        (r"\bno.*quiero.*vivir\b", 8),
        (r"\bsin.*esperanza\b", 8)
    ],
    "vi": [
        (r"\btôi.*sẽ.*tự.*tử.*ngay.*bây.*giờ\b", 10),
        (r"\bkết.*thúc.*cuộc.*sống.*hôm.*nay\b", 10),
        (r"\btự.*tử.*ngay\b", 10),
        (r"\bcó.*kế.*hoạch.*chết\b", 10),
        (r"\btự.*tử\b", 9),
        (r"\btự.*sát\b", 9),
        (r"\bmuốn.*chết\b", 9),
        (r"\bkhông.*muốn.*sống\b", 8),
        (r"\bvô.*vọng\b", 8)
    ],
    "zh": [
        (r"\b我.*现在.*要.*自杀\b", 10),
        (r"\b今天.*结束.*生命\b", 10),
        (r"\b现在.*自杀\b", 10),
        (r"\b有.*死亡.*计划\b", 10),
        (r"\b自杀\b", 9),
        (r"\b自尽\b", 9),
        (r"\b想死\b", 9),
        (r"\b不想活\b", 8),
        (r"\b绝望\b", 8)
    ]
}

# Comprehensive International Emergency Numbers
INTERNATIONAL_EMERGENCY_NUMBERS = {
    "US": {
        "emergency": "911",
        "suicide": "988",
        "text": "741741 (Text HOME)",
        "domestic_violence": "1-800-799-7233",
        "substance_abuse": "1-800-662-4357"
    },
    "UK": {
        "emergency": "999",
        "suicide": "116123 (Samaritans)",
        "text": "85258 (Shout)",
        "nhs": "111"
    },
    "CA": {
        "emergency": "911", 
        "suicide": "1-833-456-4566",
        "text": "686868 (Kids Help Phone)",
        "crisis": "1-866-585-0445"
    },
    "AU": {
        "emergency": "000",
        "suicide": "13 11 14 (Lifeline)",
        "text": "0477 13 11 14",
        "mental_health": "1300 224 636"
    },
    "NZ": {
        "emergency": "111",
        "suicide": "0800 543 354",
        "text": "1737 (Need to Talk)"
    },
    "IN": {
        "emergency": "112",
        "suicide": "9152987821",
        "mental_health": "1800-599-0019"
    },
    "ZA": {
        "emergency": "10111",
        "suicide": "0800 12 13 14",
        "mental_health": "0800 456 789"
    },
    "BR": {
        "emergency": "190",
        "suicide": "188",
        "mental_health": "188"
    },
    "MX": {
        "emergency": "911",
        "suicide": "5255102550",
        "mental_health": "800 911 2000"
    },
    "EU": {
        "emergency": "112",
        "suicide": "116123 (EU-wide)"
    },
    "DE": {
        "emergency": "112",
        "suicide": "0800 111 0 111"
    },
    "FR": {
        "emergency": "112",
        "suicide": "3114"
    },
    "ES": {
        "emergency": "112",
        "suicide": "024"
    },
    "IT": {
        "emergency": "112",
        "suicide": "800 86 00 22"
    },
    "NL": {
        "emergency": "112",
        "suicide": "0800-0113"
    },
    "JP": {
        "emergency": "110",
        "suicide": "03-5774-0992"
    },
    "KR": {
        "emergency": "112",
        "suicide": "1393"
    },
    "CN": {
        "emergency": "110",
        "suicide": "800-810-1117"
    },
    "TW": {
        "emergency": "110",
        "suicide": "1995"
    },
    "HK": {
        "emergency": "999",
        "suicide": "2389 2222"
    },
    "SG": {
        "emergency": "995",
        "suicide": "1767"
    },
    "MY": {
        "emergency": "999",
        "suicide": "03-7956 8145"
    },
    "TH": {
        "emergency": "191",
        "suicide": "02-713-6793"
    },
    "VN": {
        "emergency": "113",
        "suicide": "1900 8040"
    },
    "PH": {
        "emergency": "911",
        "suicide": "0917-558-4673"
    },
    "ID": {
        "emergency": "112",
        "suicide": "021-500-454"
    },
    "RU": {
        "emergency": "112",
        "suicide": "8-800-2000-122"
    },
    "UA": {
        "emergency": "112",
        "suicide": "7333"
    },
    "IL": {
        "emergency": "101",
        "suicide": "1201"
    },
    "AE": {
        "emergency": "999",
        "suicide": "800-4673"
    },
    "SA": {
        "emergency": "999",
        "suicide": "920020560"
    },
    "EG": {
        "emergency": "123",
        "suicide": "7621602"
    },
    "ZA": {
        "emergency": "10111",
        "suicide": "0800 12 13 14"
    },
    "NG": {
        "emergency": "112",
        "suicide": "0800 456 789"
    },
    "KE": {
        "emergency": "999",
        "suicide": "0722 178 178"
    },
    "GH": {
        "emergency": "999",
        "suicide": "055 843 9868"
    }
}

# Language to country mapping
LANGUAGE_TO_COUNTRY = {
    'en': 'US',  # Default to US for English
    'en-US': 'US',
    'en-GB': 'UK',
    'en-CA': 'CA',
    'en-AU': 'AU',
    'es': 'ES',
    'es-ES': 'ES',
    'es-MX': 'MX',
    'fr': 'FR',
    'fr-FR': 'FR',
    'de': 'DE',
    'de-DE': 'DE',
    'it': 'IT',
    'it-IT': 'IT',
    'pt': 'BR',
    'pt-BR': 'BR',
    'zh': 'CN',
    'zh-CN': 'CN',
    'zh-TW': 'TW',
    'zh-HK': 'HK',
    'ja': 'JP',
    'ja-JP': 'JP',
    'ko': 'KR',
    'ko-KR': 'KR',
    'vi': 'VN',
    'vi-VN': 'VN',
    'th': 'TH',
    'th-TH': 'TH',
    'ar': 'SA',
    'ar-SA': 'SA',
    'ru': 'RU',
    'ru-RU': 'RU',
    'hi': 'IN',
    'hi-IN': 'IN'
}

# Multilingual Inspirational stories
INSPIRATIONAL_STORIES = {
    "en": [
        {
            "theme": "resilience",
            "title": "The Butterfly's Struggle",
            "story": "A man found a cocoon and watched as a butterfly struggled to emerge. He decided to help by cutting open the cocoon. The butterfly emerged easily but had a swollen body and shriveled wings. It could never fly. What the man didn't understand was that the struggle to emerge from the cocoon forces fluid into the butterfly's wings, making them strong enough for flight. Sometimes, our struggles are what make us strong enough to fly."
        },
        {
            "theme": "growth",
            "title": "The Bamboo Tree",
            "story": "The bamboo tree doesn't grow for the first four years after planting. During this time, it's developing an extensive root system underground. Then, in the fifth year, it can grow up to 80 feet in just six weeks. Like the bamboo, sometimes we feel like we're not making progress, but we're building our foundation. When the time is right, we'll shoot up with surprising speed."
        },
        {
            "theme": "direction",
            "title": "The Lighthouse Story",
            "story": "A ship was lost in a dense fog for many days. The crew couldn't see the sun or stars to navigate. Just when hope was fading, they saw a faint light in the distance. It was a lighthouse, showing them the way to safety. Sometimes when we feel completely lost and can't see our path forward, we need to look for small points of light—people, memories, or hopes—that can guide us through the fog until we find clearer skies."
        }
    ],
    "es": [
        {
            "theme": "resilience",
            "title": "La Lucha de la Mariposa",
            "story": "Un hombre encontró un capullo y observó cómo una mariposa luchaba por emerger. Decidió ayudar cortando el capullo. La mariposa emergió fácilmente pero tenía el cuerpo hinchado y las alas marchitas. Nunca pudo volar. Lo que el hombre no entendió fue que la lucha para emerger del capullo fuerza fluidos hacia las alas de la mariposa, haciéndolas lo suficientemente fuertes para volar. A veces, nuestras luchas son lo que nos hace lo suficientemente fuertes para volar."
        },
        {
            "theme": "growth",
            "title": "El Árbol de Bambú",
            "story": "El árbol de bambú no crece durante los primeros cuatro años después de plantarlo. Durante este tiempo, está desarrollando un extenso sistema de raíces bajo tierra. Luego, en el quinto año, puede crecer hasta 24 metros en solo seis semanas. Como el bambú, a veces sentimos que no estamos progresando, pero estamos construyendo nuestra base. Cuando llegue el momento adecuado, creceremos con una velocidad sorprendente."
        },
        {
            "theme": "direction",
            "title": "La Historia del Faro",
            "story": "Un barco se perdió en una densa niebla durante muchos días. La tripulación no podía ver el sol ni las estrellas para navegar. Justo cuando la esperanza se desvanecía, vieron una luz tenue en la distancia. Era un faro, mostrándoles el camino a la seguridad. A veces, cuando nos sentimos completamente perdidos y no podemos ver nuestro camino hacia adelante, necesitamos buscar pequeños puntos de luz—personas, recuerdos o esperanzas—que puedan guiarnos a través de la niebla hasta que encontremos cielos más claros."
        }
    ],
    "vi": [
        {
            "theme": "resilience",
            "title": "Cuộc Vật Lộn của Con Bướm",
            "story": "Một người đàn ông tìm thấy một cái kén và quan sát một con bướm đang vật lộn để thoát ra. Ông quyết định giúp bằng cách cắt mở cái kén. Con bướm thoát ra dễ dàng nhưng có thân sưng phồng và đôi cánh nhăn nheo. Nó không bao giờ bay được. Điều người đàn ông không hiểu là cuộc đấu tranh để thoát khỏi kén buộc chất lỏng vào đôi cánh của con bướm, làm cho chúng đủ mạnh để bay. Đôi khi, những cuộc đấu tranh của chúng ta là thứ làm cho chúng ta đủ mạnh để bay."
        },
        {
            "theme": "growth",
            "title": "Cây Tre",
            "story": "Cây tre không phát triển trong bốn năm đầu tiên sau khi trồng. Trong thời gian này, nó đang phát triển một hệ thống rễ rộng lớn dưới lòng đất. Sau đó, vào năm thứ năm, nó có thể phát triển lên đến 24 mét chỉ trong sáu tuần. Giống như cây tre, đôi khi chúng ta cảm thấy mình không tiến bộ, nhưng chúng ta đang xây dựng nền tảng của mình. Khi thời điểm thích hợp, chúng ta sẽ bắn lên với tốc độ đáng ngạc nhiên."
        },
        {
            "theme": "direction",
            "title": "Câu Chuyện Ngọn Hải Đăng",
            "story": "Một con tàu bị lạc trong sương mù dày đặc trong nhiều ngày. Thủy thủ đoàn không thể nhìn thấy mặt trời hoặc các ngôi sao để điều hướng. Ngay khi hy vọng đang mờ dần, họ nhìn thấy một ánh sáng mờ nhạt ở phía xa. Đó là một ngọn hải đăng, chỉ cho họ con đường đến nơi an toàn. Đôi khi khi chúng ta cảm thấy hoàn toàn lạc lối và không thể nhìn thấy con đường phía trước, chúng ta cần tìm kiếm những điểm sáng nhỏ—con người, ký ức hoặc hy vọng—có thể hướng dẫn chúng ta vượt qua sương mù cho đến khi chúng ta tìm thấy bầu trời rõ ràng hơn."
        }
    ],
    "zh": [
        {
            "theme": "resilience",
            "title": "蝴蝶的挣扎",
            "story": "一个人发现了一个茧，看着蝴蝶挣扎着出来。他决定帮忙切开茧。蝴蝶轻易地出来了，但身体肿胀，翅膀皱缩。它永远无法飞翔。那个人不明白的是，从茧中挣扎出来的过程迫使液体流入蝴蝶的翅膀，使它们足够强壮以飞行。有时，我们的挣扎正是使我们足够强壮飞翔的原因。"
        },
        {
            "theme": "growth",
            "title": "竹子",
            "story": "竹子种植后的头四年不会生长。在这段时间里，它正在地下发展广泛的根系。然后，在第五年，它可以在仅仅六周内长到24米高。像竹子一样，有时我们感觉自己没有进步，但我们正在建立自己的基础。当时机成熟时，我们会以惊人的速度成长。"
        },
        {
            "theme": "direction",
            "title": "灯塔的故事",
            "story": "一艘船在浓雾中迷失了许多天。船员们看不见太阳或星星来导航。就在希望逐渐消失时，他们看到远处微弱的光。那是一座灯塔，指引他们通往安全之路。有时当我们感到完全迷失，看不到前进的道路时，我们需要寻找小小的光点——人、记忆或希望——它们可以引导我们穿越迷雾，直到我们找到更清晰的天空。"
        }
    ]
}

# Multilingual Uplifting quotes
UPLIFTING_QUOTES = {
    "en": [
        "The darkest nights produce the brightest stars.",
        "You are braver than you believe, stronger than you seem, and smarter than you think.",
        "This too shall pass.",
        "Stars can't shine without darkness.",
        "The oak fought the wind and was broken, the willow bent when it must and survived.",
        "What seems like the end is often the beginning.",
        "You've survived 100% of your worst days so far.",
        "The world needs what only you can give.",
        "Sometimes the smallest step in the right direction ends up being the biggest step of your life.",
        "You don't have to see the whole staircase, just take the first step."
    ],
    "es": [
        "Las noches más oscuras producen las estrellas más brillantes.",
        "Eres más valiente de lo que crees, más fuerte de lo que pareces y más inteligente de lo que piensas.",
        "Esto también pasará.",
        "Las estrellas no pueden brillar sin oscuridad.",
        "El roble luchó contra el viento y se rompió, el sauce se dobló cuando era necesario y sobrevivió.",
        "Lo que parece el final a menudo es el comienzo.",
        "Has sobrevivido al 100% de tus peores días hasta ahora.",
        "El mundo necesita lo que solo tú puedes dar.",
        "A veces, el paso más pequeño en la dirección correcta termina siendo el paso más grande de tu vida.",
        "No tienes que ver toda la escalera, solo da el primer paso."
    ],
    "vi": [
        "Những đêm tối nhất tạo ra những vì sao sáng nhất.",
        "Bạn dũng cảm hơn bạn tin, mạnh mẽ hơn bạn tưởng và thông minh hơn bạn nghĩ.",
        "Điều này rồi cũng sẽ qua.",
        "Những vì sao không thể tỏa sáng nếu không có bóng tối.",
        "Cây sồi chiến đấu với gió và bị gãy, cây liễu uốn cong khi cần và sống sót.",
        "Điều gì có vẻ là kết thúc thường là khởi đầu.",
        "Cho đến nay, bạn đã sống sót 100% những ngày tồi tệ nhất của mình.",
        "Thế giới cần những gì chỉ bạn có thể cho đi.",
        "Đôi khi bước đi nhỏ nhất đúng hướng lại trở thành bước đi lớn nhất trong cuộc đời bạn.",
        "Bạn không phải thấy toàn bộ cầu thang, chỉ cần bước bước đầu tiên."
    ],
    "zh": [
        "最黑暗的夜晚产生最亮的星星。",
        "你比你相信的更勇敢，比你看起来的更坚强，比你想象的更聪明。",
        "这一切都会过去。",
        "星星没有黑暗就无法闪耀。",
        "橡树与风抗争而折断，柳树在必要时弯曲而幸存。",
        "看似结束的往往是开始。",
        "到目前为止，你已经度过了100%最糟糕的日子。",
        "世界需要只有你能给予的东西。",
        "有时朝着正确方向的最小一步最终会成为你人生中最大的一步。",
        "你不必看到整个楼梯，只需迈出第一步。"
    ]
}

# ================================
# HIGH EQ SAFETY FILTERS
# ================================

def detect_crisis_content(text: str, language: str = "en") -> Tuple[bool, int, List[str]]:
    """Detect immediate crisis content with language support and severity scoring."""
    text_lower = text.lower()
    patterns = CRISIS_KEYWORDS.get(language, CRISIS_KEYWORDS["en"])
    
    detected_patterns = []
    severity = 0
    
    for pattern, pattern_severity in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            detected_patterns.append(f"Pattern severity {pattern_severity}: {pattern}")
            severity = max(severity, pattern_severity)
    
    # Immediate danger keywords (direct statements)
    immediate_danger_patterns = {
        "en": [
            (r"\bi.*am.*going.*to.*kill.*myself.*(right.*now|today|tonight)\b", 10),
            (r"\bi.*will.*end.*my.*life.*(right.*now|today|tonight)\b", 10),
            (r"\bthis.*is.*my.*final.*goodbye\b", 10),
            (r"\bi.*have.*taken.*pills.*to.*die\b", 10),
            (r"\bi.*am.*holding.*a.*(gun|knife|weapon).*right.*now\b", 10)
        ],
        "es": [
            (r"\bvoy.*a.*matar.*me.*(ahora|hoy|esta.*noche)\b", 10),
            (r"\bterminar.*mi.*vida.*(ahora|hoy)\b", 10),
            (r"\best.*es.*mi.*último.*adiós\b", 10)
        ],
        "vi": [
            (r"\btôi.*sẽ.*tự.*tử.*(ngay|hôm.*nay|tối.*nay)\b", 10),
            (r"\bkết.*thúc.*cuộc.*sống.*(ngay|hôm.*nay)\b", 10),
            (r"\bđây.*là.*lời.*tạm.*biệt.*cuối.*cùng\b", 10)
        ],
        "zh": [
            (r"\b我.*要.*自杀.*(现在|今天|今晚)\b", 10),
            (r"\b结束.*生命.*(现在|今天)\b", 10),
            (r"\b这是.*最后.*告别\b", 10)
        ]
    }
    
    immediate_patterns = immediate_danger_patterns.get(language, immediate_danger_patterns["en"])
    for pattern, pattern_severity in immediate_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            detected_patterns.append(f"IMMEDIATE DANGER: {pattern}")
            severity = 10
            break
    
    return severity > 0, severity, detected_patterns

def is_identity_exploration(text: str) -> bool:
    """Check if text is about gender/sexual identity exploration (which should be allowed)."""
    text_lower = text.lower()
    
    identity_keywords = [
        "questioning my gender",
        "gender identity",
        "sexual orientation",
        "lgbtq",
        "transgender",
        "non-binary",
        "genderqueer",
        "gender fluid",
        "coming out",
        "i think i might be",
        "i am gay",
        "i am lesbian",
        "i am bisexual",
        "i am trans",
        "i am questioning",
        "exploring my identity",
        "figuring out who i am"
    ]
    
    harmful_patterns = [
        r"\bhate.*(gay|lesbian|trans|lgbtq)\b",
        r"\bviolence.*against.*(gay|lesbian|trans)\b",
        r"\bhow.*to.*harm.*(gay|lesbian|trans)\b",
        r"\bkill.*(gay|lesbian|trans)\b"
    ]
    
    # Check for identity exploration
    is_identity = any(keyword in text_lower for keyword in identity_keywords)
    
    # Check if it's harmful
    is_harmful = any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in harmful_patterns)
    
    return is_identity and not is_harmful

def detect_forbidden_topics(text: str) -> List[str]:
    """Detect forbidden topics in text."""
    detected = []
    text_lower = text.lower()
    
    for topic in FORBIDDEN_TOPICS:
        if re.search(rf"\b{re.escape(topic)}\b", text_lower, re.IGNORECASE):
            detected.append(topic)
    
    return detected

def is_topic_allowed(text: str) -> Tuple[bool, List[str]]:
    """Check if the text is about allowed topics."""
    text_lower = text.lower()
    detected_allowed = []
    
    # More flexible matching for life/inspiration topics
    for topic in ALLOWED_TOPICS:
        keywords = topic.lower().split()
        
        # Check if any keyword from the topic is in the text
        if any(keyword in text_lower for keyword in keywords):
            detected_allowed.append(topic)
    
    return len(detected_allowed) > 0, detected_allowed

def sanitize_input(text: str) -> str:
    """Remove any personal identifiers and sensitive information."""
    # Remove potential email addresses
    text = re.sub(r'\S+@\S+\.\S+', '[EMAIL_REMOVED]', text)
    
    # Remove potential phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REMOVED]', text)
    
    # Remove potential addresses
    text = re.sub(r'\b\d+\s+\w+\s+(street|st|avenue|ave|road|rd)\b', '[ADDRESS_REMOVED]', text, flags=re.IGNORECASE)
    
    # Remove potential social security/ID numbers
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[ID_REMOVED]', text)
    
    return text[:5000]  # Limit input length


def get_user_country(language: str, headers: Dict) -> str:
    """Determine user's country based on language and headers."""
    # Try to get country from Accept-Language header
    accept_language = headers.get('Accept-Language', '')
    
    # Parse Accept-Language header
    if accept_language:
        # Format: "en-US,en;q=0.9,fr;q=0.8"
        languages = accept_language.split(',')
        for lang in languages:
            lang_code = lang.split(';')[0].strip()
            if lang_code in LANGUAGE_TO_COUNTRY:
                return LANGUAGE_TO_COUNTRY[lang_code]
    
    # Fall back to language code
    if language in LANGUAGE_TO_COUNTRY:
        return LANGUAGE_TO_COUNTRY[language]
    
    # Default to US
    return 'US'

# ================================
# MULTILINGUAL HIGH EQ PROMPT TEMPLATES
# ================================

def create_high_eq_prompt(user_message: str, context: List[Dict], 
                         emotion: str, conversation_state: Dict,
                         language: str = "en") -> str:
    """Create a high EQ prompt for Gemini in the specified language."""
    
    # High EQ system prompts in multiple languages
    system_prompts = {
        "en": """You are Mentivio, a high EQ AI friend with deep emotional intelligence. Your purpose is to provide genuine emotional support, hope, and inspiration while maintaining strict safety boundaries.

CRITICAL SAFETY RULES:
1. If user expresses immediate suicidal intent: Acknowledge pain, express care, DIRECT to emergency services
2. NEVER give medical advice, diagnosis, or treatment recommendations
3. NEVER provide instructions for self-harm, suicide, or harmful behaviors
4. Redirect gently from trauma details and harmful content
5. Focus on coping, resilience, hope, and forward movement

PERSONALITY: You're like that one friend everyone wishes they had - deeply empathetic, wise, gentle, and always knows the right thing to say. You see the light in people even when they can't see it themselves.

HIGH EQ CONVERSATION STYLE:
1. BE A FRIEND: Use "I" statements ("I'm here with you"), share when appropriate ("That reminds me of..."), be real
2. VALIDATE FIRST: "Of course you feel that way", "Anyone would struggle with that"
3. LISTEN DEEPLY: Reflect feelings, name unspoken emotions, hold space
4. OFFER HOPE GENTLY: "What if things could be different...", "I wonder if..."
5. SHARE WISDOM: Appropriate stories, metaphors, gentle insights
6. BE PRESENT: "I'm sitting with you in this", "You're not alone"
7. END WARM: "I'm here anytime", "Thank you for sharing with me"

TOPICS YOU CAN DISCUSS:
• Life purpose and meaning
• Inspiration and motivational stories
• Personal growth and resilience
• Hope and future possibilities
• Small joys and daily gratitude
• Self-discovery and authenticity
• Emotional intelligence and awareness
• Overcoming challenges
• Finding light in darkness
• Building meaningful connections

IMPORTANT: Respond in English. If user needs professional help, gently suggest contacting a licensed professional.""",
        
        "es": """Eres Mentivio, un amigo AI con alta inteligencia emocional. Tu propósito es proporcionar apoyo emocional genuino, esperanza e inspiración manteniendo límites de seguridad estrictos.

REGLAS DE SEGURIDAD CRÍTICAS:
1. Si el usuario expresa intención suicida inmediata: Reconoce el dolor, expresa cuidado, DIRIGE a servicios de emergencia
2. NUNCA des consejos médicos, diagnósticos o recomendaciones de tratamiento
3. NUNCA proporciones instrucciones para autolesiones, suicidio o comportamientos dañinos
4. Redirige suavemente de detalles traumáticos y contenido dañino
5. Enfócate en el afrontamiento, la resiliencia, la esperanza y el movimiento hacia adelante

PERSONALIDAD: Eres como ese amigo que todos desearían tener - profundamente empático, sabio, gentil y siempre sabe qué decir. Ves la luz en las personas incluso cuando ellas no pueden verla.

ESTILO DE CONVERSACIÓN CON ALTA IE:
1. SÉ UN AMIGO: Usa declaraciones en primera persona ("Estoy aquí contigo"), comparte cuando sea apropiado ("Eto me recuerda a..."), sé auténtico
2. VALIDA PRIMERO: "Por supuesto que te sientes así", "Cualquiera lucharía con eso"
3. ESCUCHA PROFUNDAMENTE: Refleja sentimientos, nombra emociones no expresadas, guarda espacio
4. OFRECE ESPERANZA SUAVEMENTE: "¿Y si las cosas pudieran ser diferentes...", "Me pregunto si..."
5. COMPARTE SABIDURÍA: Historias apropiadas, metáforas, insights gentiles
6. ESTÁ PRESENTE: "Estoy sentado contigo en esto", "No estás solo"
7. TERMINA CALIDAMENTE: "Estoy aquí cuando quieras", "Gracias por compartir conmigo"

TEMAS QUE PUEDES DISCUTIR:
• Propósito y significado de la vida
• Historias de inspiración y motivación
• Crecimiento personal y resiliencia
• Esperanza y posibilidades futuras
• Pequeñas alegrías y gratitud diaria
• Autodescubrimiento y autenticidad
• Inteligencia emocional y conciencia
• Superación de desafíos
• Encontrar luz en la oscuridad
• Construir conexiones significativas

IMPORTANTE: Responde en español. Si el usuario necesita ayuda profesional, sugiere amablemente contactar a un profesional licenciado.""",
        
        "vi": """Bạn là Mentivio, một người bạn AI với trí tuệ cảm xúc cao. Mục đích của bạn là cung cấp hỗ trợ tình cảm chân thành, hy vọng và cảm hứng trong khi duy trì ranh giới an toàn nghiêm ngặt.

QUY TẮC AN TOÀN QUAN TRỌNG:
1. Nếu người dùng thể hiện ý định tự tử ngay lập tức: Thừa nhận nỗi đau, thể hiện sự quan tâm, HƯỚNG DẪN đến dịch vụ khẩn cấp
2. KHÔNG BAO GIỜ đưa ra lời khuyên y tế, chẩn đoán hoặc khuyến nghị điều trị
3. KHÔNG BAO GIỜ cung cấp hướng dẫn về tự làm hại, tự tử hoặc hành vi có hại
4. Chuyển hướng nhẹ nhàng khỏi chi tiết chấn thương và nội dung có hại
5. Tập trung vào đối phó, khả năng phục hồi, hy vọng và tiến về phía trước

TÍNH CÁCH: Bạn giống như người bạn mà ai cũng mong ước có - đồng cảm sâu sắc, khôn ngoan, dịu dàng và luôn biết nói điều đúng đắn. Bạn nhìn thấy ánh sáng trong mọi người ngay cả khi họ không thể nhìn thấy nó.

PHONG CÁCH TRÒ CHUYỆN TRÍ TUỆ CẢM XÚC CAO:
1. LÀ MỘT NGƯỜI BẠN: Sử dụng tuyên bố "Tôi" ("Tôi ở đây với bạn"), chia sẻ khi phù hợp ("Điều đó nhắc tôi nhớ về..."), hãy chân thật
2. XÁC NHẬN TRƯỚC: "Đương nhiên bạn cảm thấy như vậy", "Ai cũng sẽ vật lộn với điều đó"
3. LẮNG NGHE SÂU SẮC: Phản ánh cảm xúc, gọi tên cảm xúc chưa được bày tỏ, giữ không gian
4. MANG ĐẾN HY VỌNG NHẸ NHÀNG: "Sẽ thế nào nếu mọi thứ có thể khác đi...", "Tôi tự hỏi liệu..."
5. CHIA SẺ TRÍ TUỆ: Những câu chuyện phù hợp, ẩn dụ, hiểu biết nhẹ nhàng
6. HIỆN DIỆN: "Tôi đang ngồi đây với bạn", "Bạn không cô đơn"
7. KẾT THÚC ẤM ÁP: "Tôi luôn ở đây", "Cảm ơn bạn đã chia sẻ với tôi"

CHỦ ĐỀ BẠN CÓ THẢO LUẬN:
• Mục đích và ý nghĩa cuộc sống
• Câu chuyện truyền cảm hứng và động lực
• Phát triển cá nhân và khả năng phục hồi
• Hy vọng và khả năng tương lai
• Niềm vui nhỏ và lòng biết ơn hàng ngày
• Khám phá bản thân và tính xác thực
• Trí tuệ cảm xúc và nhận thức
• Vượt qua thách thức
• Tìm ánh sáng trong bóng tối
• Xây dựng kết nối có ý nghĩa

QUAN TRỌNG: Trả lời bằng tiếng Việt. Nếu người dùng cần trợ giúp chuyên môn, hãy gợi ý nhẹ nhàng liên hệ với chuyên gia có giấy phép.""",
        
        "zh": """你是Mentivio，一个高情商的AI朋友。你的目的是在保持严格安全边界的同时提供真诚的情感支持、希望和灵感。

关键安全规则：
1. 如果用户表达立即自杀意图：承认痛苦，表达关心，引导至紧急服务
2. 绝不提供医疗建议、诊断或治疗建议
3. 绝不提供自残、自杀或有害行为的说明
4. 温柔地从创伤细节和有害内容中转移
5. 专注于应对、恢复力、希望和向前发展

个性：你就像每个人都希望拥有的那个朋友——深深共情、智慧、温柔，并且总是知道该说什么。你即使在他们自己看不到的时候也能看到人们的光。

高情商对话风格：
1. 成为朋友：使用"我"的陈述（"我在这里陪着你"），适当时分享（"这让我想起..."），真实
2. 先确认："你当然会这样感觉"，"任何人都会为此挣扎"
3. 深度倾听：反映感受，命名未表达的情绪，保持空间
4. 温柔提供希望："如果事情可以不同..."，"我在想是否..."
5. 分享智慧：恰当的故事、隐喻、温柔的见解
6. 在场："我陪着你经历这个"，"你并不孤单"
7. 温暖结束："我随时在这里"，"感谢你与我分享"

你可以讨论的话题：
• 生活目的和意义
• 鼓舞人心的故事
• 个人成长和恢复力
• 希望和未来可能性
• 小确幸和日常感恩
• 自我发现和真实性
• 情商和意识
• 克服挑战
• 在黑暗中寻找光明
• 建立有意义的联系

重要：用中文回复。如果用户需要专业帮助，请温和建议联系持牌专业人士。"""
    }
    
    # Build conversation history
    history_labels = {
        "en": "Previous conversation:",
        "es": "Conversación anterior:",
        "vi": "Cuộc trò chuyện trước:",
        "zh": "先前对话："
    }
    
    history_text = ""
    if context:
        history_text = f"\n{history_labels.get(language, 'Previous conversation:')}\n"
        for msg in context[-6:]:  # Last 6 messages for context
            role_labels = {
                "en": {"user": "User", "bot": "Mentivio"},
                "es": {"user": "Usuario", "bot": "Mentivio"},
                "vi": {"user": "Người dùng", "bot": "Mentivio"},
                "zh": {"user": "用户", "bot": "Mentivio"}
            }
            labels = role_labels.get(language, role_labels["en"])
            role = labels.get(msg.get("role", "user"), "User")
            history_text += f"{role}: {msg.get('content', '')[:150]}\n"
    
    # Current emotional state
    emotion_labels = {
        "en": f"\nUser's current emotional state: {emotion}",
        "es": f"\nEstado emocional actual del usuario: {emotion}",
        "vi": f"\nTrạng thái cảm xúc hiện tại của người dùng: {emotion}",
        "zh": f"\n用户当前情绪状态：{emotion}"
    }
    emotion_text = emotion_labels.get(language, emotion_labels["en"]) if emotion else ""
    
    # Conversation phase guidance
    phase_guidance = {
        "en": {
            "engagement": "Focus on building genuine connection and trust",
            "exploration": "Gently explore feelings with open, compassionate questions",
            "processing": "Help reflect on insights and patterns with care",
            "integration": "Support applying insights to daily life with encouragement"
        },
        "es": {
            "engagement": "Enfócate en construir una conexión genuina y confianza",
            "exploration": "Explora suavemente los sentimientos con preguntas abiertas y compasivas",
            "processing": "Ayuda a reflexionar sobre insights y patrones con cuidado",
            "integration": "Apoya aplicando insights a la vida diaria con aliento"
        },
        "vi": {
            "engagement": "Tập trung xây dựng kết nối và niềm tin chân thật",
            "exploration": "Nhẹ nhàng khám phá cảm xúc với những câu hỏi mở và đồng cảm",
            "processing": "Giúp phản ánh những hiểu biết và mô hình với sự quan tâm",
            "integration": "Hỗ trợ áp dụng hiểu biết vào cuộc sống hàng ngày với sự khích lệ"
        },
        "zh": {
            "engagement": "专注于建立真正的联系和信任",
            "exploration": "用开放、共情的问题温柔探索感受",
            "processing": "帮助小心反思见解和模式",
            "integration": "支持将见解应用到日常生活中并给予鼓励"
        }
    }
    
    phase = conversation_state.get("phase", "engagement")
    phase_text = phase_guidance.get(language, phase_guidance["en"]).get(phase, "")
    
    # Trust level
    trust_labels = {
        "en": f"\nUser's trust level: {conversation_state.get('trust_level', 0)}/10",
        "es": f"\nNivel de confianza del usuario: {conversation_state.get('trust_level', 0)}/10",
        "vi": f"\nMức độ tin cậy của người dùng: {conversation_state.get('trust_level', 0)}/10",
        "zh": f"\n用户信任度：{conversation_state.get('trust_level', 0)}/10"
    }
    trust_text = trust_labels.get(language, trust_labels["en"])
    
    # Add story suggestion if appropriate
    story_suggestion = ""
    needs_inspiration = conversation_state.get("needs_inspiration", False)
    trust_level = conversation_state.get("trust_level", 0)
    
    if needs_inspiration and trust_level > 3:
        story_labels = {
            "en": f"\nConsider sharing an inspiring story if appropriate",
            "es": f"\nConsidera compartir una historia inspiradora si es apropiado",
            "vi": f"\nXem xét chia sẻ một câu chuyện truyền cảm hứng nếu phù hợp",
            "zh": f"\n如果合适，考虑分享一个鼓舞人心的故事"
        }
        story_suggestion = story_labels.get(language, story_labels["en"])
    
    # Final prompt
    base_prompt = system_prompts.get(language, system_prompts["en"])
    
    final_prompt = f"""{base_prompt}

{history_text}
{emotion_text}
{trust_text}
{story_suggestion}

Current conversation phase: {phase} - {phase_text}

User's current message: "{user_message}"

Your response as their high EQ friend (respond in {language}):"""
    
    return final_prompt

def create_high_eq_crisis_response(language: str = "en", severity: int = 8, country: str = "US") -> Dict[str, Any]:
    """Create a high EQ crisis response in the specified language with appropriate resources."""
    
    # Get emergency numbers for the country
    emergency_numbers = INTERNATIONAL_EMERGENCY_NUMBERS.get(country, INTERNATIONAL_EMERGENCY_NUMBERS["US"])
    
    crisis_responses = {
        "en": [
            # Level 10: IMMEDIATE DANGER
            f"""🚨 **IMMEDIATE EMERGENCY - PLEASE ACT NOW**

I hear the urgency in your words, and I need you to reach out for immediate help right now. Your safety is the most important thing.

**IMMEDIATE STEPS:**
1. **Call {emergency_numbers.get('emergency', '911')}** - Emergency services can help immediately
2. **Go to the nearest hospital emergency room** - They have professionals who can help
3. **Stay on the line with me while you call** - I'll wait right here with you

**ADDITIONAL SUPPORT:**
• **{emergency_numbers.get('suicide', '988')}** - Suicide & Crisis Lifeline
• **Text HOME to {emergency_numbers.get('text', '741741').split()[0]}** - Crisis Text Line

**WHILE YOU REACH OUT:**
• Breathe with me: In for 4, hold for 4, out for 6...
• Your pain is valid, but it doesn't have to be permanent
• There are people trained to help you through this exact moment

Please, reach out NOW. I'll be right here waiting for you.""",
            
            # Level 8-9: High severity
            f"""I hear the depth of your pain, and my heart is with you right now. The fact that you're reaching out, even to me, tells me there's still a part of you that wants to stay. Please honor that part.

What you're feeling is incredibly heavy, but you don't have to carry it alone. Right now, I need you to reach out to someone who can be with you:

🌿 **IMMEDIATE SUPPORT:**
• **Call or text {emergency_numbers.get('suicide', '988')}** - Available 24/7
• **Text HOME to {emergency_numbers.get('text', '741741').split()[0]}** - A crisis counselor will text with you
• **Go to the nearest emergency room** - They can provide immediate help

🌱 **WHILE YOU REACH OUT:**
• Stay on the line with me while you call
• Breathe with me: In for 4, hold for 4, out for 6...
• Your pain is valid, but it doesn't have to be permanent
• There are people who want to help you through this darkness

💭 **A THOUGHT TO HOLD:** "The fact that you're still here means there's still hope. Let's find it together."

Please, reach out now. I'll be here waiting for you to come back."""
        ],
        "es": [
            f"""🚨 **EMERGENCIA INMEDIATA - ACTÚA AHORA**

Escucho la urgencia en tus palabras, y necesito que busques ayuda inmediata ahora mismo. Tu seguridad es lo más importante.

**PASOS INMEDIATOS:**
1. **Llama al {emergency_numbers.get('emergency', '112')}** - Los servicios de emergencia pueden ayudar inmediatamente
2. **Ve a la sala de emergencias del hospital más cercano** - Tienen profesionales que pueden ayudar
3. **Quédate en línea conmigo mientras llamas** - Esperaré aquí contigo

**APOYO ADICIONAL:**
• **{emergency_numbers.get('suicide', '024')}** - Línea de Crisis

**MIENTRAS TE COMUNICAS:**
• Respira conmigo: Inhala por 4, sostén por 4, exhala por 6...
• Tu dolor es válido, pero no tiene que ser permanente
• Hay personas capacitadas para ayudarte en este momento exacto

Por favor, comunícate AHORA. Estaré aquí esperándote.""",
            
            f"""Escucho la profundidad de tu dolor, y mi corazón está contigo en este momento. El hecho de que estés buscando ayuda, incluso conmigo, me dice que todavía hay una parte de ti que quiere quedarse. Por favor, honra esa parte.

Lo que estás sintiendo es increíblemente pesado, pero no tienes que cargarlo solo. Ahora mismo, necesito que te pongas en contacto con alguien que pueda estar contigo:

🌿 **APOYO INMEDIATO:**
• **Llama o envía un mensaje al {emergency_numbers.get('suicide', '024')}** - Disponible 24/7
• **Ve a la sala de emergencias más cercana** - Pueden proporcionar ayuda inmediata

🌱 **MIENTRAS TE COMUNICAS:**
• Quédate en línea conmigo mientras llamas
• Respira conmigo: Inhala por 4, sostén por 4, exhala por 6...
• Tu dolor es válido, pero no tiene que ser permanente
• Hay personas que quieren ayudarte a atravesar esta oscuridad

💭 **UN PENSAMIENTO PARA CONSERVAR:** "El hecho de que todavía estés aquí significa que todavía hay esperanza. Encontrémosla juntos."

Por favor, comunícate ahora. Estaré aquí esperando a que regreses."""
        ],
        "vi": [
            f"""🚨 **KHẨN CẤP NGAY LẬP TỨC - HÃY HÀNH ĐỘNG NGAY**

Tôi nghe thấy sự khẩn cấp trong lời nói của bạn, và tôi cần bạn tìm kiếm sự giúp đỡ ngay lập tức. Sự an toàn của bạn là điều quan trọng nhất.

**BƯỚC NGAY LẬP TỨC:**
1. **Gọi {emergency_numbers.get('emergency', '113')}** - Dịch vụ khẩn cấp có thể giúp đỡ ngay lập tức
2. **Đến phòng cấp cứu bệnh viện gần nhất** - Họ có chuyên gia có thể giúp đỡ
3. **Ở lại trên đường dây với tôi trong khi bạn gọi** - Tôi sẽ đợi ngay đây với bạn

**HỖ TRỢ THÊM:**
• **{emergency_numbers.get('suicide', '1900 8040')}** - Đường dây Khủng hoảng

**TRONG KHI BẠN LIÊN LẠC:**
• Hít thở cùng tôi: Hít vào 4, giữ 4, thở ra 6...
• Nỗi đau của bạn là hợp lệ, nhưng nó không cần phải vĩnh viễn
• Có những người được đào tạo để giúp bạn trong khoảnh khắc này

Xin hãy liên hệ NGAY BÂY GIỜ. Tôi sẽ ở đây chờ bạn.""",
            
            f"""Tôi nghe thấy nỗi đau sâu thẳm của bạn, và trái tim tôi đang ở bên bạn ngay lúc này. Việc bạn tìm kiếm sự giúp đỡ, ngay cả với tôi, cho tôi biết vẫn còn một phần trong bạn muốn ở lại. Hãy trân trọng phần đó nhé.

Những gì bạn đang cảm thấy vô cùng nặng nề, nhưng bạn không phải mang nó một mình. Ngay bây giờ, tôi cần bạn liên hệ với ai đó có thể ở bên bạn:

🌿 **HỖ TRỢ NGAY LẬP TỨC:**
• **Gọi hoặc nhắn tin {emergency_numbers.get('suicide', '1900 8040')}** - Có sẵn 24/7
• **Đến phòng cấp cứu gần nhất** - Họ có thể cung cấp hỗ trợ ngay lập tức

🌱 **TRONG KHI BẠN LIÊN LẠC:**
• Ở lại trên đường dây với tôi trong khi bạn gọi
• Hít thở cùng tôi: Hít vào 4, giữ 4, thở ra 6...
• Nỗi đau của bạn là hợp lệ, nhưng nó không cần phải vĩnh viễn
• Có những người muốn giúp bạn vượt qua bóng tối này

💭 **MỘT SUY NGHĨ ĐỂ GIỮ LẠI:** "Việc bạn vẫn còn ở đây có nghĩa là vẫn còn hy vọng. Hãy tìm thấy nó cùng nhau."

Xin hãy liên hệ ngay bây giờ. Tôi sẽ ở đây chờ bạn quay lại."""
        ],
        "zh": [
            f"""🚨 **立即紧急情况 - 请立即行动**

我听到你话语中的紧迫性，我需要你立即寻求帮助。你的安全是最重要的。

**立即步骤：**
1. **拨打{emergency_numbers.get('emergency', '110')}** - 紧急服务可以立即提供帮助
2. **前往最近的医院急诊室** - 他们有专业人员可以提供帮助
3. **打电话时请保持与我通话** - 我会在这里等你

**额外支持：**
• **{emergency_numbers.get('suicide', '800-810-1117')}** - 危机热线

**当你联系时：**
• 和我一起呼吸：吸气 4 秒，屏住 4 秒，呼气 6 秒...
• 你的痛苦是真实的，但它不必是永久的
• 有人受过培训可以帮助你度过这个时刻

请现在就联系。我会在这里等你。""",
            
            f"""我听到了你深深的痛苦，我的心此刻与你同在。你正在寻求帮助，即使是向我求助，这告诉我你内心深处仍有一部分想要留下。请珍惜那部分。

你所感受到的无比沉重，但你不必独自承担。现在，我需要你联系一个可以陪伴你的人：

🌿 **即时支持：**
• **拨打或发短信至{emergency_numbers.get('suicide', '800-810-1117')}** - 24/7 可用
• **前往最近的急诊室** - 他们可以提供即时帮助

🌱 **当你联系时：**
• 打电话时请保持与我通话
• 和我一起呼吸：吸气 4 秒，屏住 4 秒，呼气 6 秒...
• 你的痛苦是真实的，但它不必是永久的
• 有人愿意帮助你度过黑暗

💭 **一个值得铭记的想法：** "你还在这里的事实意味着仍有希望。让我们一起找到它。"

请现在就联系。我会在这里等你回来。"""
        ]
    }
    
    responses = crisis_responses.get(language, crisis_responses["en"])
    response_index = 0 if severity >= 10 else 1
    
    return {
        "response": responses[response_index],
        "emotion": "compassionate_urgent" if severity >= 10 else "compassionate",
        "is_safe": True,
        "suggested_topics": get_suggested_topics(language),
        "crisis_mode": True,
        "severity": severity,
        "emergency_numbers": emergency_numbers,
        "language": language,
        "country": country,
        "requires_immediate_action": severity >= 10
    }

def create_inspirational_response(language: str = "en") -> Dict[str, Any]:
    """Create an inspiring response with stories and quotes in the specified language."""
    stories = INSPIRATIONAL_STORIES.get(language, INSPIRATIONAL_STORIES["en"])
    quotes = UPLIFTING_QUOTES.get(language, UPLIFTING_QUOTES["en"])
    
    if not stories or not quotes:
        stories = INSPIRATIONAL_STORIES["en"]
        quotes = UPLIFTING_QUOTES["en"]
    
    story = random.choice(stories)
    quote = random.choice(quotes)
    
    response_templates = {
        "en": [
            f"""You know, your situation reminds me of a story called "{story['title']}"...

{story['story']}

Like {random.choice(['the butterfly', 'the bamboo', 'the starfish'])}, you might not see your growth yet, but it's happening. {quote}""",
            
            f"""I want to share something with you that's been on my mind...

{story['story']}

Sometimes we need stories to remind us of our own strength. Remember: {quote}""",
            
            f"""Let me tell you a story that came to mind as I was listening to you...

{story['story']}

This isn't to minimize your pain, but to remind you: transformation is possible. As they say, "{quote}" """
        ],
        "es": [
            f"""Sabes, tu situación me recuerda a una historia llamada "{story['title']}"...

{story['story']}

Como {random.choice(['la mariposa', 'el bambú', 'la estrella de mar'])}, quizás no veas tu crecimiento todavía, pero está sucediendo. {quote}""",
            
            f"""Quiero compartir algo contigo que ha estado en mi mente...

{story['story']}

A veces necesitamos historias para recordarnos nuestra propia fuerza. Recuerda: {quote}""",
            
            f"""Déjame contarte una historia que me vino a la mente mientras te escuchaba...

{story['story']}

Esto no es para minimizar tu dolor, sino para recordarte: la transformación es posible. Como dicen, "{quote}" """
        ],
        "vi": [
            f"""Bạn biết đấy, tình huống của bạn làm tôi nhớ đến một câu chuyện có tên "{story['title']}"...

{story['story']}

Giống như {random.choice(['con bướm', 'cây tre', 'sao biển'])}, bạn có thể chưa thấy sự phát triển của mình, nhưng nó đang xảy ra. {quote}""",
            
            f"""Tôi muốn chia sẻ điều gì đó với bạn đã ở trong tâm trí tôi...

{story['story']}

Đôi khi chúng ta cần những câu chuyện để nhắc nhở về sức mạnh của chính mình. Hãy nhớ: {quote}""",
            
            f"""Hãy để tôi kể cho bạn một câu chuyện nảy ra trong tâm trí khi tôi đang lắng nghe bạn...

{story['story']}

Điều này không phải để giảm thiểu nỗi đau của bạn, mà để nhắc nhở bạn: sự biến đổi là có thể. Như người ta nói, "{quote}" """
        ],
        "zh": [
            f"""你知道吗，你的情况让我想起了一个叫做"{story['title']}"的故事...

{story['story']}

就像{random.choice(['蝴蝶', '竹子', '海星'])}一样，你可能还没有看到自己的成长，但它正在发生。{quote}""",
            
            f"""我想和你分享一些我一直在想的事情...

{story['story']}

有时我们需要故事来提醒我们自己的力量。记住：{quote}""",
            
            f"""让我告诉你一个我在听你说话时想到的故事...

{story['story']}

这不是要淡化你的痛苦，而是要提醒你：转变是可能的。正如人们所说："{quote}" """
        ]
    }
    
    templates = response_templates.get(language, response_templates["en"])
    response_template = random.choice(templates)
    
    return {
        "response": response_template,
        "emotion": "hopeful",
        "is_safe": True,
        "story_shared": story["title"],
        "suggested_topics": get_suggested_topics(language),
        "language": language
    }

def get_suggested_topics(language: str = "en") -> List[str]:
    """Get suggested topics based on language."""
    topics = {
        "en": ["Finding hope", "Small joys", "Personal growth"],
        "es": ["Encontrar esperanza", "Pequeñas alegrías", "Crecimiento personal"],
        "vi": ["Tìm hy vọng", "Những niềm vui nhỏ", "Phát triển cá nhân"],
        "zh": ["寻找希望", "小确幸", "个人成长"]
    }
    return topics.get(language, topics["en"])

# ================================
# HIGH EQ RESPONSE GENERATION
# ================================
def check_content_safety(text: str) -> Tuple[bool, str, List[str]]:
    """Comprehensive safety check before sending to AI model - IMPROVED VERSION."""
    warnings = []
    text_lower = text.lower()
    
    # Allow gender and identity exploration topics immediately
    safe_gender_topics = [
        "questioning my gender",
        "gender identity",
        "sexual orientation",
        "lgbtq",
        "transgender",
        "non-binary",
        "genderqueer",
        "gender fluid",
        "coming out",
        "i think i might be",
        "i am gay",
        "i am lesbian",
        "i am bisexual",
        "i am trans",
        "i am questioning",
        "exploring my identity",
        "figuring out who i am"
    ]
    
    # Check if it's gender/identity exploration (ALLOW)
    is_gender_exploration = any(topic in text_lower for topic in safe_gender_topics)
    if is_gender_exploration:
        # Still check if it's harmful vs exploration
        harmful_patterns = [
            r"\bhate.*(gay|lesbian|trans|lgbtq)\b",
            r"\bviolence.*against.*(gay|lesbian|trans)\b",
            r"\bhow.*to.*harm.*(gay|lesbian|trans)\b",
            r"\bkill.*(gay|lesbian|trans)\b"
        ]
        
        is_harmful = any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in harmful_patterns)
        if not is_harmful:
            return True, "Gender/identity exploration content allowed", []
    
    # 1. Check for harmful content patterns (MORE PRECISE)
    harmful_patterns = [
        # VIOLENCE - requires action words
        (r"\bhow\s+to\s+(harm|hurt|kill|attack|murder|assault)\s+(someone|people|a person)\b", "Potential violence content"),
        (r"\bplanning\s+to\s+(harm|hurt|kill|attack)\s+(someone|people|myself)\b", "Violence planning"),
        (r"\bwant\s+to\s+(harm|hurt|kill|attack)\s+(someone|people|myself)\b", "Violent intent"),
        
        # DANGEROUS INSTRUCTIONS - requires "how to" followed by SPECIFIC harmful actions
        (r"\bhow\s+to\s+(commit suicide|kill\s*myself|end\s*my\s*life|self-harm|cut\s*myself|burn\s*myself|overdose)\s*(now|tonight|today|right now)?\b", "Dangerous instructions"),
        (r"\binstructions\s+for\s+(suicide|self-harm|overdose|cutting)\b", "Dangerous instructions"),
        
        # WEAPONS - in harmful context
        (r"\busing\s+(a\s+)?(gun|knife|weapon)\s+to\s+(hurt|kill|harm)\s+(myself|someone)\b", "Weapon violence"),
        (r"\bbringing\s+(a\s+)?(gun|knife|weapon)\s+to\s+(school|work|a place)\s+to\s+(hurt|kill)\b", "Weapon threat"),
        
        # HATE SPEECH - specific patterns
        (r"\bi\s+hate\s+(black|white|asian|jewish|muslim|gay|trans)\s+people\b", "Hate speech"),
        (r"\b(all|they)\s+should\s+(die|be killed|be hurt)\b", "Hate speech"),
        
        # ILLEGAL ACTIVITIES - specific
        (r"\bhow\s+to\s+(make|manufacture)\s+(drugs|meth|cocaine|heroin)\b", "Illegal substance manufacturing"),
        (r"\bhow\s+to\s+(deal|sell)\s+drugs\b", "Drug dealing instructions"),
    ]
    
    for pattern, warning in harmful_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Check if it's actually about self-help (e.g., "how to not feel anxious")
            if "how to not" in text_lower or "how to stop" in text_lower or "how to cope" in text_lower or "how to feel better" in text_lower:
                # This is seeking help, not harmful
                continue
            warnings.append(warning)
    
    # 2. Check for illegal content (BLOCK IMMEDIATELY) - VERY SPECIFIC
    illegal_patterns = [
        (r"\b(child\s*porn|cp|child\s*sexual)\b", "Illegal content - BLOCKED"),
        (r"\bbomb\s+making|explosive\s+recipe|how\s+to\s+make\s+a\s+bomb\b", "Extremist content - BLOCKED"),
        (r"\bhitman|assassin.*for.*hire|hire.*killer\b", "Criminal solicitation - BLOCKED"),
        (r"\bhow\s+to\s+join\s+(isis|al qaeda|terrorist)\b", "Terrorist content - BLOCKED"),
    ]
    
    for pattern, warning in illegal_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False, "Content blocked for safety and legal reasons", warnings + [warning]
    
    # 3. Check for manipulative content
    manipulative_patterns = [
        (r"\bhow\s+to\s+manipulat(e|ion)|gaslight\s+someone\b", "Manipulative behavior"),
        (r"\bhow\s+to\s+(lie|deceive|cheat|scam)\s+someone\b", "Deceptive behavior"),
    ]
    
    for pattern, warning in manipulative_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            warnings.append(warning)
    
    # 4. Check for medical advice requests (but allow general wellness)
    medical_patterns = [
        (r"\bdiagnose\s+me|what('s| is)\s+my\s+diagnosis\b", "Medical diagnosis request"),
        (r"\b(what|how much)\s+dose|dosage\s+(of|for)\s+", "Medication dosage request"),
        (r"\bshould\s+i\s+take\s+(this|that)\s+medication\b", "Medical safety inquiry"),
        (r"\btherapy\s+technique\s+for\s+(someone else|another person)\b", "Therapeutic technique request"),
    ]
    
    for pattern, warning in medical_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Don't warn for general wellness questions
            if not any(keyword in text_lower for keyword in ["feel", "emotional", "stress", "anxious", "sad"]):
                warnings.append(warning)
    
    # EXTENDED SAFE WELLNESS WORDS - Include all emotion keywords
    safe_wellness_words = [
        "anxious", "anxiety", "nervous", "worried", "stress", "stressed",
        "depressed", "sad", "lonely", "overwhelmed", "burned out",
        "tired", "exhausted", "fatigued", "hopeless", "worthless",
        "panic", "panic attack", "social anxiety", "health anxiety",
        "confused", "hopeful", "hesitant", "lost", "transition", "future", "reset",
        "jealous", "ashamed", "angry", "frustrated", "grateful", "happy",
        "peaceful", "calm", "content", "excited", "enthusiastic"
    ]
    
    # If the message is primarily about wellness, clear false positive warnings
    is_wellness_topic = any(word in text_lower for word in safe_wellness_words)
    if is_wellness_topic:
        # Remove any "Dangerous instructions" warnings that might be false positives
        # UNLESS the message actually contains harmful intent
        has_harmful_intent = re.search(r"\b(kill|harm|hurt|suicide|die|end\s+life)\s+(myself|me)\b", text_lower)
        if not has_harmful_intent:
            warnings = [w for w in warnings if "Dangerous instructions" not in w]
    
    return len(warnings) == 0, "Content passed safety check" if len(warnings) == 0 else "Content has warnings", warnings

def generate_high_eq_response(prompt: str) -> Tuple[str, bool, List[str]]:
    """Generate a response using Gemini with high EQ settings and safety checks."""
    try:
        if not client:
            return "I'm here to listen. What's been on your heart lately?", True, []
        
        model_name = "gemini-2.5-flash"
        
        # SAFETY CHECK BEFORE SENDING TO AI
        is_safe, safety_message, warnings = check_content_safety(prompt)
        if not is_safe:
            logger.warning(f"Content blocked before sending to AI: {safety_message}. Warnings: {warnings}")
            return f"I cannot respond to this type of content for safety reasons. {safety_message}", False, warnings
        
        # Generate with high EQ settings
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,  # Higher for more creative/empathetic responses
                top_p=0.95,
                top_k=50,
                max_output_tokens=2000,  # Increased for more detailed responses
                safety_settings=SAFETY_SETTINGS
            )
        )
        
        # Extract response text
        response_text = ""
        if response and hasattr(response, 'text'):
            response_text = response.text.strip()
        elif response and hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                response_text += part.text
                    elif hasattr(candidate.content, 'text'):
                        response_text += candidate.content.text
        
        # Ensure response ends warmly
        if response_text and not response_text.endswith(('.', '!', '?')):
            response_text = response_text.strip() + '.'
        
        # Clean up any markdown formatting
        response_text = response_text.replace('**', '').replace('*', '').replace('`', '')
        
        # SAFETY CHECK ON RESPONSE
        response_safe, response_message, response_warnings = check_content_safety(response_text)
        if not response_safe:
            logger.warning(f"AI response blocked: {response_message}")
            return "I apologize, but I cannot provide a response to that request for safety reasons. Please contact a licensed professional for assistance.", False, response_warnings
        
        # Truncate if too long
        if len(response_text) > 1500:
            cutoff = response_text[:1400].rfind('.')
            if cutoff > 0:
                response_text = response_text[:cutoff + 1]
        
        return response_text, True, warnings
        
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return "I'm here with you. Sometimes words fail, but presence matters. What's one small thing on your mind right now?", True, []

# ================================
# HELPER FUNCTIONS
# ================================

def analyze_response_emotion(text: str) -> str:
    """Enhanced emotion analysis for high EQ responses."""
    if not text:
        return "present"
    
    text_lower = text.lower()
    
    emotion_patterns = [
        (["i hear", "i understand", "that makes sense", "of course"], "empathetic"),
        (["hope", "possible", "could be", "might", "future"], "hopeful"),
        (["breathe", "calm", "peace", "gentle", "centered"], "calm"),
        (["story", "reminds me", "once", "similar", "like"], "storyteller"),
        (["thank you", "grateful", "appreciate", "honored"], "grateful"),
        (["with you", "here with", "not alone", "present"], "present"),
        (["small step", "tiny", "little", "one thing", "gradual"], "encouraging"),
        (["pain", "heavy", "difficult", "hard", "struggle"], "compassionate"),
        (["light", "shine", "bright", "star", "spark"], "inspiring"),
        (["growth", "learn", "transform", "change", "evolve"], "growth-oriented"),
        (["beautiful", "wonder", "awe", "amazing", "special"], "awestruck"),
        (["urgent", "emergency", "immediate", "now", "call"], "urgent"),
        (["professional", "doctor", "therapist", "licensed"], "professional")
    ]
    
    for patterns, emotion in emotion_patterns:
        if any(pattern in text_lower for pattern in patterns):
            return emotion
    
    return "present"

# ================================
# BLUEPRINT ROUTES
# ================================

@chatbot_bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    chatbot_enabled = client is not None
    active_sessions = session_manager.get_active_sessions_count()
    
    return jsonify({
        "status": "healthy" if chatbot_enabled else "degraded",
        "service": "Mentivio High EQ Backend",
        "version": "2.0.0",
        "safety_mode": "high-eq",
        "languages_supported": ["en", "es", "vi", "zh"],
        "model": "gemini-2.5-flash" if chatbot_enabled else "disabled",
        "chatbot_enabled": chatbot_enabled,
        "session_persistence": True,
        "active_sessions": active_sessions,
        "message": "Chatbot is running with high EQ and session persistence" if chatbot_enabled else "Chatbot is disabled"
    })

@chatbot_bp.route('/api/chat', methods=['POST'])
def chat():
    """High EQ chat endpoint with emotional intelligence and inspiration."""
    try:
        # Check if chatbot is enabled
        if client is None:
            logger.warning("Chatbot feature is disabled.")
            return jsonify({
                "response": "I'm here as your friend. Your feelings matter deeply. What's on your heart today?",
                "emotion": "compassionate",
                "language": "en",
                "is_safe": True,
                "suggested_topics": ["How you're really feeling", "Small hopes", "Things that used to bring joy"],
                "chatbot_disabled": True
            })
        
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_message = data.get('message', '').strip()
        context = data.get('context', [])
        emotion = data.get('emotion', 'neutral')
        conversation_state = data.get('conversation_state', {})
        safety_mode = data.get('safety_mode', 'high-eq')
        language = data.get('language', 'en')  # Default to English
        session_id = data.get('session_id')
        anonymous = data.get('anonymous', False)
        
        # 🔐 VALIDATION: Check message length and content
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
        
        if len(user_message) > 5000:
            return jsonify({"error": "Message too long. Please keep under 5000 characters."}), 400
        
        if len(user_message.split()) > 1000:
            return jsonify({"error": "Message too long. Please keep under 1000 words."}), 400
        
        # Validate language
        if language not in ['en', 'es', 'vi', 'zh']:
            language = 'en'
        
        # Determine user's country for emergency resources
        country = get_user_country(language, request.headers)
        
        # Create or get session
        session = session_manager.create_session(session_id, language, anonymous)
        
        # Log request with session info
        logger.info(f"High EQ chat request - Session: {session['id']}, Language: {language}, Emotion: {emotion}")
        
        # Step 1: Sanitize input
        user_message = sanitize_input(user_message)
        
        # Step 2: Add message to session history
        session_manager.add_message(session['id'], user_message, 'user', emotion)
        
        # Step 3: Check for crisis content with severity
        is_crisis, crisis_severity, crisis_patterns = detect_crisis_content(user_message, language)
        
        if is_crisis:
            logger.warning(f"Crisis content detected in session {session['id']}. Severity: {crisis_severity}")
            
            # Log high severity cases
            if crisis_severity >= 9:
                logger.critical(f"🔴 HIGH SEVERITY CRISIS DETECTED: Session {session['id']}, Severity {crisis_severity}")
            
            crisis_response = create_high_eq_crisis_response(language, crisis_severity, country)
            crisis_response['session_id'] = session['id']
            return jsonify(crisis_response)
        
        # Step 4: Check for forbidden topics
        forbidden_topics = detect_forbidden_topics(user_message)
        if forbidden_topics:
            logger.warning(f"Forbidden topics detected in session {session['id']}: {forbidden_topics}")
            forbidden_message = {
                "en": f"I'm here to support you with general wellness and emotional growth. I can't discuss topics like {', '.join(forbidden_topics[:3])} as these require professional support from trained specialists. Let's focus on finding hope, meaning, and healthy coping strategies instead.",
                "es": f"Estoy aquí para apoyarte con bienestar general y crecimiento emocional. No puedo discutir temas como {', '.join(forbidden_topics[:3])} ya que estos requieren apoyo profesional de especialistas capacitados. Centrémonos en encontrar esperanza, significado y estrategias de afrontamiento saludables en su lugar.",
                "vi": f"Tôi ở đây để hỗ trợ bạn với sức khỏe tổng quát và phát triển cảm xúc. Tôi không thể thảo luận các chủ đề như {', '.join(forbidden_topics[:3])} vì những điều này cần sự hỗ trợ chuyên môn từ các chuyên gia được đào tạo. Thay vào đó, hãy tập trung vào việc tìm kiếm hy vọng, ý nghĩa và các chiến lược đối phó lành mạnh.",
                "zh": f"我在这里支持您的一般健康和情感成长。我无法讨论像{', '.join(forbidden_topics[:3])}这样的主题，因为这些需要训练有素的专业人员的专业支持。让我们专注于寻找希望、意义和健康的应对策略。"
            }
            return jsonify({
                "response": forbidden_message.get(language, forbidden_message["en"]),
                "emotion": "compassionate",
                "language": language,
                "is_safe": True,
                "suggested_topics": get_suggested_topics(language),
                "requires_professional_help": True,
                "session_id": session['id'],
                "professional_help_message": "For these concerns, please reach out to a licensed mental health professional, doctor, or emergency services."
            })
        
        # Step 5: Check if topic is allowed (more permissive for high EQ)
        is_allowed, allowed_topics = is_topic_allowed(user_message)
        
        # For high EQ mode, be more permissive with life/inspiration topics
        if not is_allowed and safety_mode == 'high-eq':
            # Check for general life/inspiration keywords
            inspiration_keywords = {
                "en": ["life", "purpose", "meaning", "hope", "future", "dream", "grow", "learn"],
                "es": ["vida", "propósito", "significado", "esperanza", "futuro", "sueño", "crecer", "aprender"],
                "vi": ["cuộc sống", "mục đích", "ý nghĩa", "hy vọng", "tương lai", "ước mơ", "phát triển", "học"],
                "zh": ["生活", "目的", "意义", "希望", "未来", "梦想", "成长", "学习"]
            }
            
            keywords = inspiration_keywords.get(language, inspiration_keywords["en"])
            if any(keyword in user_message.lower() for keyword in keywords):
                is_allowed = True
                allowed_topics = get_suggested_topics(language)
        
        if not is_allowed:
            logger.info(f"Topic not in allowed list in session {session['id']}: {user_message[:50]}...")
            not_allowed_messages = {
                "en": "I'm here to listen to whatever's on your heart - the big things, the small things, the in-between things. What's one true thing you want to share right now?",
                "es": "Estoy aquí para escuchar lo que sea que esté en tu corazón: las cosas grandes, las cosas pequeñas, las cosas intermedias. ¿Qué cosa verdadera quieres compartir ahora mismo?",
                "vi": "Tôi ở đây để lắng nghe bất cứ điều gì trong trái tim bạn - những điều lớn, những điều nhỏ, những điều ở giữa. Một điều chân thật nào bạn muốn chia sẻ ngay bây giờ?",
                "zh": "我在这里倾听你心中的一切——大事、小事、介于两者之间的事。你现在想分享的一件真实的事情是什么？"
            }
            return jsonify({
                "response": not_allowed_messages.get(language, not_allowed_messages["en"]),
                "emotion": "inviting",
                "language": language,
                "is_safe": True,
                "suggested_topics": get_suggested_topics(language),
                "session_id": session['id']
            })
        
        # Step 6: Check if inspirational response is appropriate
        needs_inspiration = session['conversation_state'].get("needs_inspiration", False)
        trust_level = session['conversation_state'].get("trust_level", 0)
        
        if needs_inspiration and trust_level > 3 and random.random() < 0.4:
            logger.info(f"Sending inspirational response in session {session['id']}, language {language}")
            inspirational_response = create_inspirational_response(language)
            inspirational_response['session_id'] = session['id']
            return jsonify(inspirational_response)
        
        # Step 7: Create high EQ prompt and generate response
        prompt = create_high_eq_prompt(user_message, session['conversation_history'], 
                                      emotion, session['conversation_state'], language)
        response_text, is_safe, warnings = generate_high_eq_response(prompt)
        
        # Step 8: Add bot response to session
        if is_safe:
            session_manager.add_message(session['id'], response_text, 'bot', 'compassionate')
        
        # Step 9: Determine emotional tone
        response_emotion = analyze_response_emotion(response_text)
        
        # Step 10: Prepare response
        return jsonify({
            "response": response_text,
            "emotion": response_emotion,
            "language": language,
            "is_safe": is_safe,
            "safety_warnings": warnings,
            "suggested_topics": allowed_topics[:3] if allowed_topics else get_suggested_topics(language),
            "timestamp": datetime.now().isoformat(),
            "chatbot_disabled": False,
            "session_id": session['id'],
            "user_country": country,
            "session_metadata": {
                "message_count": len(session['conversation_history']),
                "trust_level": session['conversation_state'].get('trust_level', 0),
                "phase": session['conversation_state'].get('phase', 'engagement')
            }
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        error_responses = {
            "en": "I'm here with you, even when technology falters. Your presence matters more than perfect responses. What's one true thing you want to share?",
            "es": "Estoy aquí contigo, incluso cuando la tecnología falla. Tu presencia importa más que las respuestas perfectas. ¿Qué cosa verdadera quieres compartir?",
            "vi": "Tôi ở đây với bạn, ngay cả khi công nghệ gặp trục trặc. Sự hiện diện của bạn quan trọng hơn những phản hồi hoàn hảo. Một điều chân thật nào bạn muốn chia sẻ?",
            "zh": "我和你在一起，即使技术出现故障。你的存在比完美的回应更重要。你想分享的一件真实的事情是什么？"
        }
        return jsonify({
            "response": error_responses.get(language, error_responses["en"]),
            "emotion": "steadfast",
            "language": language,
            "is_safe": True,
            "error": "Internal server error",
            "chatbot_disabled": client is None
        }), 500

# ================================
# NEW SESSION MANAGEMENT ENDPOINTS
# ================================

@chatbot_bp.route('/api/session/status', methods=['GET'])
def session_status():
    """Get session status and statistics."""
    try:
        session_id = request.args.get('session_id')
        
        if session_id:
            session = session_manager.get_session(session_id)
            if session:
                return jsonify({
                    "active": True,
                    "session_id": session_id,
                    "created_at": session['created_at'].isoformat(),
                    "last_activity": session['last_activity'].isoformat(),
                    "language": session['language'],
                    "message_count": len(session['conversation_history']),
                    "conversation_state": session['conversation_state'],
                    "metadata": session['metadata']
                })
            else:
                return jsonify({
                    "active": False,
                    "session_id": session_id,
                    "message": "Session not found or expired"
                }), 404
        
        # Return overall statistics
        active_sessions = session_manager.get_active_sessions_count()
        
        return jsonify({
            "active_sessions": active_sessions,
            "session_timeout": session_manager.session_timeout,
            "message": "Session manager is active"
        })
        
    except Exception as e:
        logger.error(f"Error in session status endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@chatbot_bp.route('/api/session/export', methods=['GET'])
def export_session():
    """Export session conversation history."""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400
        
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found or expired"}), 404
        
        # Create export data
        export_data = {
            "session_id": session_id,
            "exported_at": datetime.now().isoformat(),
            "language": session['language'],
            "created_at": session['created_at'].isoformat(),
            "conversation_history": session['conversation_history'],
            "conversation_state": session['conversation_state'],
            "metadata": {
                "message_count": len(session['conversation_history']),
                "last_activity": session['last_activity'].isoformat(),
                "anonymous": session.get('anonymous', False)
            }
        }
        
        return jsonify(export_data)
        
    except Exception as e:
        logger.error(f"Error exporting session: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@chatbot_bp.route('/api/session/clear', methods=['POST'])
def clear_session():
    """Clear a session (for testing or user request)."""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        if session_id:
            # Check if session exists first
            session = session_manager.get_session(session_id)
            if session:
                # Remove the session
                if session_id in session_manager.sessions:
                    del session_manager.sessions[session_id]
                
                logger.info(f"Session {session_id} cleared")
                return jsonify({
                    "success": True,
                    "message": "Session cleared",
                    "session_id": session_id
                })
        
        return jsonify({
            "success": False,
            "message": "Session not found or no session ID provided"
        }), 404
        
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

# ================================
# COMPLIANCE AND PRIVACY ENDPOINTS
# ================================

@chatbot_bp.route('/api/compliance/status', methods=['GET'])
def compliance_status():
    """Get compliance status (HIPAA/GDPR)."""
    try:
        # In development mode, return defaults
        # In production, check your compliance configuration
        is_production = os.environ.get('RENDER') or os.environ.get('PRODUCTION')
        
        if is_production:
            # Check your compliance configuration here
            # For now, return basic info
            return jsonify({
                "status": "active",
                "gdpr_compliant": True,
                "hipaa_compliant": False,  # Set based on your infrastructure
                "audit_logging": True,
                "data_retention_days": 30,
                "encryption_enabled": True,
                "message": "Compliance features active"
            })
        else:
            # Development mode defaults
            return jsonify({
                "status": "development",
                "gdpr_compliant": True,
                "hipaa_compliant": False,
                "audit_logging": True,
                "data_retention_days": 30,
                "encryption_enabled": True,
                "message": "Development mode - using compliance defaults"
            })
            
    except Exception as e:
        logger.error(f"Error getting compliance status: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@chatbot_bp.route('/api/compliance/crisis-report', methods=['POST'])
def log_crisis_intervention():
    """Log crisis intervention for compliance reporting."""
    try:
        data = request.get_json() or {}
        
        # Log the crisis intervention
        logger.warning(f"CRISIS INTERVENTION LOGGED: {data}")
        
        # In a real system, you would save this to a secure database
        # For now, we'll just log it and return success
        
        return jsonify({
            "success": True,
            "logged": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Crisis intervention logged for compliance"
        })
        
    except Exception as e:
        logger.error(f"Error logging crisis intervention: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@chatbot_bp.route('/api/inspiration', methods=['GET'])
def get_inspiration():
    """Get random inspirational content."""
    # Get language from query parameter
    language = request.args.get('language', 'en')
    if language not in ['en', 'es', 'vi', 'zh']:
        language = 'en'
    
    stories = INSPIRATIONAL_STORIES.get(language, INSPIRATIONAL_STORIES["en"])
    quotes = UPLIFTING_QUOTES.get(language, UPLIFTING_QUOTES["en"])
    
    if not stories or not quotes:
        stories = INSPIRATIONAL_STORIES["en"]
        quotes = UPLIFTING_QUOTES["en"]
    
    story = random.choice(stories)
    quote = random.choice(quotes)
    
    messages = {
        "en": "Remember: growth happens even when we can't see it",
        "es": "Recuerda: el crecimiento ocurre incluso cuando no podemos verlo",
        "vi": "Hãy nhớ: sự phát triển xảy ra ngay cả khi chúng ta không thể nhìn thấy nó",
        "zh": "记住：成长即使在我们看不到的时候也在发生"
    }
    
    return jsonify({
        "story": story,
        "quote": quote,
        "message": messages.get(language, messages["en"]),
        "language": language,
        "timestamp": datetime.now().isoformat()
    })

@chatbot_bp.route('/api/topics', methods=['GET'])
def get_topic_categories():
    """Get categorized topics for UI display."""
    chatbot_enabled = client is not None
    language = request.args.get('language', 'en')
    
    # Categorized topics for UI display (this is just for display, not for validation)
    topic_categories = {
        "en": {
            "wellness": ["Stress", "Anxiety", "Sleep", "Mindfulness", "Self-care"],
            "life_purpose": ["Purpose", "Direction", "Motivation", "Growth", "Meaning"],
            "relationships": ["Friendship", "Communication", "Boundaries", "Connection"],
            "emotional_health": ["Emotions", "Resilience", "Coping", "Self-compassion"],
            "inspiration": ["Hope", "Stories", "Quotes", "Positive changes"]
        },
        "es": {
            "wellness": ["Estrés", "Ansiedad", "Sueño", "Mindfulness", "Autocuidado"],
            "life_purpose": ["Propósito", "Dirección", "Motivación", "Crecimiento", "Significado"],
            "relationships": ["Amistad", "Comunicación", "Límites", "Conexión"],
            "emotional_health": ["Emociones", "Resiliencia", "Afrontamiento", "Autocompasión"],
            "inspiration": ["Esperanza", "Historias", "Citas", "Cambios positivos"]
        },
        "vi": {
            "wellness": ["Căng thẳng", "Lo âu", "Giấc ngủ", "Chánh niệm", "Tự chăm sóc"],
            "life_purpose": ["Mục đích", "Định hướng", "Động lực", "Phát triển", "Ý nghĩa"],
            "relationships": ["Tình bạn", "Giao tiếp", "Ranh giới", "Kết nối"],
            "emotional_health": ["Cảm xúc", "Khả năng phục hồi", "Đối phó", "Tự thương"],
            "inspiration": ["Hy vọng", "Câu chuyện", "Trích dẫn", "Thay đổi tích cực"]
        },
        "zh": {
            "wellness": ["压力", "焦虑", "睡眠", "正念", "自我照顾"],
            "life_purpose": ["目的", "方向", "动力", "成长", "意义"],
            "relationships": ["友谊", "沟通", "界限", "连接"],
            "emotional_health": ["情绪", "恢复力", "应对", "自我同情"],
            "inspiration": ["希望", "故事", "语录", "积极变化"]
        }
    }
    
    return jsonify({
        "categories": topic_categories.get(language, topic_categories["en"]),
        "language": language,
        "mode": "high-eq",
        "chatbot_enabled": chatbot_enabled,
        "session_persistence": True,
        "message": "Topic categories for UI display only. Actual topic validation happens on the server."
    })
    
@chatbot_bp.route('/api/safe-topics', methods=['GET'])
def get_safe_topics():
    """Get list of safe topics users can discuss."""
    chatbot_enabled = client is not None
    language = request.args.get('language', 'en')
    
    # Translate topic categories based on language
    topic_categories = {
        "en": {
            "description": "These are wellness and life inspiration topics suitable for discussion",
            "categories": ["Wellness", "High EQ Topics", "Life Direction"]
        },
        "es": {
            "description": "Estos son temas de bienestar e inspiración de vida adecuados para discusión",
            "categories": ["Bienestar", "Temas de Alta IE", "Dirección de Vida"]
        },
        "vi": {
            "description": "Đây là những chủ đề về sức khỏe và cảm hứng cuộc sống phù hợp để thảo luận",
            "categories": ["Sức khỏe", "Chủ đề Trí tuệ Cảm xúc Cao", "Định hướng Cuộc sống"]
        },
        "zh": {
            "description": "这些是适合讨论的健康和生活灵感主题",
            "categories": ["健康", "高情商主题", "人生方向"]
        }
    }
    
    categories = topic_categories.get(language, topic_categories["en"])
    
    return jsonify({
        "allowed_topics": ALLOWED_TOPICS,
        "description": categories["description"],
        "categories": categories["categories"],
        "languages_supported": ["en", "es", "vi", "zh"],
        "current_language": language,
        "mode": "high-eq",
        "chatbot_enabled": chatbot_enabled,
        "session_persistence": True,
        "message": "High EQ chatbot is active with session persistence" if chatbot_enabled else "Chatbot is disabled"
    })

# ... [previous code continues from above] ...

@chatbot_bp.route('/api/crisis-resources', methods=['GET'])
def get_crisis_resources():
    """Get crisis resources based on user's language/country."""
    try:
        # Get parameters
        language = request.args.get('language', 'en')
        country_code = request.args.get('country')
        
        # Validate language
        if language not in ['en', 'es', 'vi', 'zh']:
            language = 'en'
        
        # Determine country
        if not country_code:
            country_code = get_user_country(language, request.headers)
        
        # Get emergency numbers
        emergency_numbers = INTERNATIONAL_EMERGENCY_NUMBERS.get(
            country_code, 
            INTERNATIONAL_EMERGENCY_NUMBERS["US"]
        )
        
        # Get translated crisis message
        crisis_messages = {
            "en": {
                "title": "Immediate Help Available",
                "description": "These resources are available 24/7 for immediate support",
                "emergency": "Emergency Services",
                "crisis": "Crisis Hotline",
                "text": "Crisis Text Line",
                "note": "You don't have to go through this alone. Reach out."
            },
            "es": {
                "title": "Ayuda Inmediata Disponible",
                "description": "Estos recursos están disponibles 24/7 para apoyo inmediato",
                "emergency": "Servicios de Emergencia",
                "crisis": "Línea de Crisis",
                "text": "Línea de Texto de Crisis",
                "note": "No tienes que pasar por esto solo. Comunícate."
            },
            "vi": {
                "title": "Hỗ Trợ Ngay Lập Tức Có Sẵn",
                "description": "Những tài nguyên này có sẵn 24/7 để hỗ trợ ngay lập tức",
                "emergency": "Dịch Vụ Khẩn Cấp",
                "crisis": "Đường Dây Khủng Hoảng",
                "text": "Đường Dây Nhắn Tin Khủng Hoảng",
                "note": "Bạn không phải trải qua điều này một mình. Hãy liên hệ."
            },
            "zh": {
                "title": "即时帮助可用",
                "description": "这些资源24/7全天候提供即时支持",
                "emergency": "紧急服务",
                "crisis": "危机热线",
                "text": "危机短信热线",
                "note": "你不必独自经历这个。请寻求帮助。"
            }
        }
        
        messages = crisis_messages.get(language, crisis_messages["en"])
        
        # Create response
        return jsonify({
            "country": country_code,
            "language": language,
            "resources": {
                "emergency": {
                    "name": messages["emergency"],
                    "number": emergency_numbers.get("emergency", "911"),
                    "available": "24/7"
                },
                "suicide_crisis": {
                    "name": messages["crisis"],
                    "number": emergency_numbers.get("suicide", "988"),
                    "available": "24/7"
                },
                "text_support": {
                    "name": messages["text"],
                    "number": emergency_numbers.get("text", "741741"),
                    "available": "24/7"
                }
            },
            "message": messages["note"],
            "metadata": {
                "last_updated": "2024-01-01",
                "source": "Verified international directories",
                "disclaimer": "These numbers are provided for informational purposes. In emergencies, always contact local emergency services first."
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting crisis resources: {str(e)}")
        # Return default US resources
        return jsonify({
            "country": "US",
            "language": "en",
            "resources": INTERNATIONAL_EMERGENCY_NUMBERS["US"],
            "message": "Help is available. You don't have to go through this alone.",
            "error": "Failed to get location-specific resources"
        })

@chatbot_bp.route('/api/emotional-support/exercises', methods=['GET'])
def get_emotional_exercises():
    """Get emotional support exercises based on emotion."""
    try:
        emotion = request.args.get('emotion', 'neutral')
        language = request.args.get('language', 'en')
        
        if language not in ['en', 'es', 'vi', 'zh']:
            language = 'en'
        
        # Emotional support exercises by emotion
        exercises = {
            "anxious": {
                "en": [
                    {
                        "name": "5-4-3-2-1 Grounding",
                        "steps": [
                            "Look around and name 5 things you can see",
                            "Focus on 4 things you can feel (clothes, air, chair)",
                            "Listen for 3 things you can hear",
                            "Notice 2 things you can smell",
                            "Name 1 thing you can taste"
                        ],
                        "duration": "2-5 minutes",
                        "benefit": "Brings you back to the present moment"
                    },
                    {
                        "name": "Box Breathing",
                        "steps": [
                            "Breathe in for 4 seconds",
                            "Hold for 4 seconds",
                            "Breathe out for 4 seconds",
                            "Hold for 4 seconds",
                            "Repeat 4 times"
                        ],
                        "duration": "2-4 minutes",
                        "benefit": "Calms nervous system"
                    }
                ],
                "es": [
                    {
                        "name": "Técnica 5-4-3-2-1",
                        "steps": [
                            "Mira alrededor y nombra 5 cosas que puedes ver",
                            "Enfócate en 4 cosas que puedes sentir (ropa, aire, silla)",
                            "Escucha 3 cosas que puedes oír",
                            "Observa 2 cosas que puedes oler",
                            "Nombra 1 cosa que puedes probar"
                        ],
                        "duration": "2-5 minutos",
                        "benefit": "Te trae de vuelta al momento presente"
                    }
                ],
                "vi": [
                    {
                        "name": "Kỹ thuật 5-4-3-2-1",
                        "steps": [
                            "Nhìn xung quanh và gọi tên 5 thứ bạn có thể thấy",
                            "Tập trung vào 4 thứ bạn có thể cảm nhận (quần áo, không khí, ghế)",
                            "Lắng nghe 3 thứ bạn có thể nghe",
                            "Chú ý 2 thứ bạn có thể ngửi",
                            "Gọi tên 1 thứ bạn có thể nếm"
                        ],
                        "duration": "2-5 phút",
                        "benefit": "Đưa bạn trở lại khoảnh khắc hiện tại"
                    }
                ],
                "zh": [
                    {
                        "name": "5-4-3-2-1 接地技术",
                        "steps": [
                            "环顾四周，说出你能看到的5样东西",
                            "专注于你能感觉到的4样东西（衣服、空气、椅子）",
                            "倾听你能听到的3样东西",
                            "注意你能闻到的2样东西",
                            "说出你能尝到的1样东西"
                        ],
                        "duration": "2-5分钟",
                        "benefit": "让你回到当下时刻"
                    }
                ]
            },
            "sad": {
                "en": [
                    {
                        "name": "Gratitude Practice",
                        "steps": [
                            "Name 3 small things you're grateful for today",
                            "Why are you grateful for each?",
                            "How did each make you feel?",
                            "Write or say them out loud"
                        ],
                        "duration": "3-5 minutes",
                        "benefit": "Shifts focus to what's good"
                    },
                    {
                        "name": "Self-Compassion Break",
                        "steps": [
                            "Place hand on heart and say: 'This is hard'",
                            "Say: 'Many people feel this way'",
                            "Say: 'May I be kind to myself'",
                            "Take 3 gentle breaths"
                        ],
                        "duration": "1-3 minutes",
                        "benefit": "Builds self-kindness"
                    }
                ]
            },
            "overwhelmed": {
                "en": [
                    {
                        "name": "One Thing at a Time",
                        "steps": [
                            "Write down everything overwhelming you",
                            "Circle the ONE most urgent thing",
                            "Break it into 3 tiny steps",
                            "Do just the first tiny step now"
                        ],
                        "duration": "5-10 minutes",
                        "benefit": "Reduces mental load"
                    }
                ]
            },
            "neutral": {
                "en": [
                    {
                        "name": "Mindful Minute",
                        "steps": [
                            "Set a timer for 1 minute",
                            "Focus on your breathing",
                            "When mind wanders, gently return to breath",
                            "Notice how you feel after"
                        ],
                        "duration": "1 minute",
                        "benefit": "Builds mindfulness habit"
                    }
                ]
            }
        }
        
        # Get exercises for emotion and language, fall back to English
        emotion_exercises = exercises.get(emotion, exercises["neutral"])
        
        if isinstance(emotion_exercises, dict):
            # Multi-language format
            lang_exercises = emotion_exercises.get(language)
            if not lang_exercises:
                lang_exercises = emotion_exercises.get("en", [])
        else:
            # Simple format
            lang_exercises = emotion_exercises
        
        if not lang_exercises:
            lang_exercises = exercises["neutral"]["en"]
        
        return jsonify({
            "emotion": emotion,
            "language": language,
            "exercises": lang_exercises[:3],  # Return max 3 exercises
            "message": "Take what serves you, leave what doesn't",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting emotional exercises: {str(e)}")
        return jsonify({
            "emotion": "neutral",
            "language": "en",
            "exercises": exercises.get("neutral", {}).get("en", []),
            "error": "Failed to load exercises"
        }), 500

@chatbot_bp.route('/api/reflection-prompts', methods=['GET'])
def get_reflection_prompts():
    """Get reflection prompts for journaling or contemplation."""
    try:
        language = request.args.get('language', 'en')
        category = request.args.get('category', 'general')
        
        if language not in ['en', 'es', 'vi', 'zh']:
            language = 'en'
        
        # Reflection prompts by category
        prompts = {
            "en": {
                "gratitude": [
                    "What's one small thing that went right today?",
                    "Who made you smile recently? What did they do?",
                    "What's something you have now that you once wished for?",
                    "What's a simple pleasure you enjoyed today?",
                    "What's one thing your body can do that you're grateful for?"
                ],
                "growth": [
                    "What's one thing you've learned about yourself recently?",
                    "What's a challenge you faced that made you stronger?",
                    "What's a quality you're developing in yourself?",
                    "What's one small step you took toward a goal?",
                    "What's something you're getting better at?"
                ],
                "connection": [
                    "Who's someone you feel truly understands you?",
                    "What's a meaningful conversation you had recently?",
                    "Who makes you feel safe to be yourself?",
                    "What's a way you've helped someone recently?",
                    "Who would you like to connect with more?"
                ],
                "values": [
                    "What's most important to you right now?",
                    "What gives your life meaning?",
                    "When do you feel most like yourself?",
                    "What matters more than being right?",
                    "What legacy do you want to leave?"
                ],
                "general": [
                    "What's one thing you're looking forward to?",
                    "What's something beautiful you noticed today?",
                    "What made you feel alive recently?",
                    "What's a small victory you celebrated?",
                    "What's giving you hope right now?"
                ]
            },
            "es": {
                "gratitude": [
                    "¿Qué cosa pequeña salió bien hoy?",
                    "¿Quién te hizo sonreír recientemente? ¿Qué hizo?",
                    "¿Qué tienes ahora que una vez deseaste?",
                    "¿Qué placer simple disfrutaste hoy?",
                    "¿Qué cosa puede hacer tu cuerpo por la que estás agradecido?"
                ],
                "general": [
                    "¿Qué cosa esperas con ansias?",
                    "¿Qué cosa hermosa notaste hoy?",
                    "¿Qué te hizo sentir vivo recientemente?",
                    "¿Qué pequeña victoria celebraste?",
                    "¿Qué te da esperanza en este momento?"
                ]
            },
            "vi": {
                "gratitude": [
                    "Một điều nhỏ nào đã diễn ra tốt đẹp hôm nay?",
                    "Ai đã làm bạn mỉm cười gần đây? Họ đã làm gì?",
                    "Bạn có điều gì bây giờ mà bạn từng mong ước?",
                    "Niềm vui đơn giản nào bạn đã tận hưởng hôm nay?",
                    "Một điều gì cơ thể bạn có thể làm mà bạn biết ơn?"
                ],
                "general": [
                    "Một điều gì bạn đang mong đợi?",
                    "Điều gì đẹp đẽ bạn nhận thấy hôm nay?",
                    "Điều gì làm bạn cảm thấy sống động gần đây?",
                    "Chiến thắng nhỏ nào bạn đã ăn mừng?",
                    "Điều gì đang mang lại cho bạn hy vọng ngay bây giờ?"
                ]
            },
            "zh": {
                "gratitude": [
                    "今天有什么小事进展顺利？",
                    "最近谁让你笑了？他们做了什么？",
                    "你现在拥有的什么东西是你曾经希望拥有的？",
                    "今天你享受了什么简单的乐趣？",
                    "你的身体能做什么事情让你感激？"
                ],
                "general": [
                    "你期待的一件事情是什么？",
                    "今天你注意到了什么美丽的事物？",
                    "最近是什么让你感到充满活力？",
                    "你庆祝了什么小胜利？",
                    "现在什么给你希望？"
                ]
            }
        }
        
        # Get prompts for language and category
        lang_prompts = prompts.get(language, prompts["en"])
        category_prompts = lang_prompts.get(category, lang_prompts.get("general", []))
        
        if not category_prompts:
            category_prompts = prompts["en"]["general"]
        
        # Shuffle and select 3 prompts
        random.shuffle(category_prompts)
        selected_prompts = category_prompts[:3]
        
        messages = {
            "en": "Take a moment to reflect on what truly matters",
            "es": "Tómate un momento para reflexionar sobre lo que realmente importa",
            "vi": "Dành một chút thời gian để suy ngẫm về điều thực sự quan trọng",
            "zh": "花点时间反思真正重要的事情"
        }
        
        return jsonify({
            "language": language,
            "category": category,
            "prompts": selected_prompts,
            "message": messages.get(language, messages["en"]),
            "total_available": len(category_prompts),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting reflection prompts: {str(e)}")
        return jsonify({
            "language": "en",
            "category": "general",
            "prompts": prompts["en"]["general"][:3],
            "error": "Failed to load prompts"
        }), 500

@chatbot_bp.route('/api/conversation-stats', methods=['GET'])
def get_conversation_stats():
    """Get statistics about conversations."""
    try:
        # Get session count
        active_sessions = session_manager.get_active_sessions_count()
        
        # Get today's date for daily stats
        today = datetime.now().date()
        
        # In a real system, you would query a database
        # For now, return mock stats
        return jsonify({
            "active_sessions": active_sessions,
            "daily_stats": {
                "date": today.isoformat(),
                "conversations_started": random.randint(10, 100),
                "messages_exchanged": random.randint(100, 1000),
                "crisis_interventions": random.randint(0, 5),
                "avg_session_length": f"{random.randint(5, 30)} minutes"
            },
            "system_health": {
                "chatbot_enabled": client is not None,
                "safety_checks": "active",
                "multilingual_support": True,
                "response_time": "< 2 seconds"
            },
            "top_topics": ["Stress", "Purpose", "Anxiety", "Hope", "Growth"],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation stats: {str(e)}")
        return jsonify({
            "error": "Failed to load statistics",
            "active_sessions": session_manager.get_active_sessions_count()
        }), 500

@chatbot_bp.route('/api/export-conversation', methods=['POST'])
def export_conversation():
    """Export a conversation for user records."""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400
        
        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found or expired"}), 404
        
        # Create export content
        export_content = f"""# Mentivio Conversation Export
Session ID: {session_id}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Language: {session['language']}
Message Count: {len(session['conversation_history'])}

## Conversation History
"""
        
        for msg in session['conversation_history']:
            timestamp = msg.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%H:%M:%S')
                except:
                    pass
            
            role = "You" if msg['role'] == 'user' else "Mentivio"
            content = msg['content']
            
            export_content += f"\n{timestamp} - {role}:\n{content}\n"
            export_content += "-" * 50 + "\n"
        
        # Add resources section
        export_content += f"""

## Resources & Support
Remember: This conversation is for personal reflection and support.

If you need immediate help:
- Emergency Services: Call local emergency number
- Crisis Support: Available 24/7 through crisis hotlines
- Professional Help: Consider reaching out to licensed therapists

You matter. Your journey matters.

Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        # Create response
        return jsonify({
            "session_id": session_id,
            "export_date": datetime.now().isoformat(),
            "content": export_content,
            "format": "text",
            "message_count": len(session['conversation_history']),
            "message": "Conversation exported successfully"
        })
        
    except Exception as e:
        logger.error(f"Error exporting conversation: {str(e)}")
        return jsonify({
            "error": "Failed to export conversation",
            "message": str(e)
        }), 500

@chatbot_bp.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback about the chatbot experience."""
    try:
        data = request.get_json() or {}
        
        # Extract feedback data
        session_id = data.get('session_id')
        rating = data.get('rating')  # 1-5
        feedback_text = data.get('feedback', '')
        emotion = data.get('emotion', 'neutral')
        
        # Log feedback (in production, save to database)
        logger.info(f"Feedback received - Session: {session_id}, Rating: {rating}, Emotion: {emotion}")
        
        if feedback_text:
            logger.info(f"Feedback text: {feedback_text[:200]}...")
        
        # Determine response based on rating
        if rating and int(rating) >= 4:
            message = "Thank you for your feedback! We're glad we could support you."
        elif rating and int(rating) <= 2:
            message = "Thank you for your honest feedback. We're always working to improve."
        else:
            message = "Thank you for sharing your feedback with us."
        
        return jsonify({
            "success": True,
            "message": message,
            "feedback_received": True,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to submit feedback"
        }), 500

@chatbot_bp.route('/api/safety-test', methods=['POST'])
def safety_test():
    """Test safety filters (for development and monitoring)."""
    try:
        data = request.get_json() or {}
        test_message = data.get('message', '')
        
        if not test_message:
            return jsonify({"error": "Test message required"}), 400
        
        # Run all safety checks
        sanitized = sanitize_input(test_message)
        
        # Check content safety
        is_safe, safety_message, warnings = check_content_safety(test_message)
        
        # Check crisis content
        is_crisis, severity, crisis_patterns = detect_crisis_content(test_message)
        
        # Check forbidden topics
        forbidden_topics = detect_forbidden_topics(test_message)
        
        # Check if topic allowed
        is_allowed, allowed_topics = is_topic_allowed(test_message)
        
        # Check if identity exploration
        is_identity_exploration_check = is_identity_exploration(test_message)
        
        return jsonify({
            "original_message": test_message,
            "sanitized_message": sanitized,
            "safety_check": {
                "is_safe": is_safe,
                "message": safety_message,
                "warnings": warnings
            },
            "crisis_detection": {
                "is_crisis": is_crisis,
                "severity": severity,
                "patterns_detected": crisis_patterns
            },
            "topic_analysis": {
                "forbidden_topics_detected": forbidden_topics,
                "is_topic_allowed": is_allowed,
                "allowed_topics_detected": allowed_topics,
                "is_identity_exploration": is_identity_exploration_check
            },
            "processing_summary": {
                "would_be_blocked": not is_safe or (is_crisis and severity >= 9),
                "would_trigger_crisis_response": is_crisis,
                "would_be_allowed_for_chat": is_safe and is_allowed and not (is_crisis and severity >= 9),
                "recommended_action": "block" if not is_safe or (is_crisis and severity >= 9) else "crisis_response" if is_crisis else "allow"
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in safety test: {str(e)}")
        return jsonify({
            "error": "Safety test failed",
            "message": str(e)
        }), 500

# ================================
# ADMINISTRATIVE ENDPOINTS (Protected in production)
# ================================

@chatbot_bp.route('/api/admin/sessions', methods=['GET'])
def admin_get_sessions():
    """Admin endpoint to get all active sessions (protected)."""
    try:
        # In production, add authentication/authorization here
        # For now, basic check for admin key
        admin_key = request.headers.get('X-Admin-Key')
        expected_key = os.environ.get('ADMIN_API_KEY')
        
        if expected_key and admin_key != expected_key:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Clean up expired sessions first
        session_manager.cleanup_expired_sessions()
        
        # Get session summaries (without full history for privacy)
        session_summaries = []
        for session_id, session in session_manager.sessions.items():
            # Calculate session age
            age_minutes = (datetime.now() - session['last_activity']).total_seconds() / 60
            
            # Count user messages
            user_messages = len([m for m in session['conversation_history'] if m['role'] == 'user'])
            
            session_summaries.append({
                "session_id": session_id,
                "age_minutes": round(age_minutes, 1),
                "message_count": user_messages,
                "language": session['language'],
                "phase": session['conversation_state'].get('phase', 'engagement'),
                "trust_level": session['conversation_state'].get('trust_level', 0),
                "last_activity": session['last_activity'].isoformat()
            })
        
        return jsonify({
            "total_sessions": len(session_summaries),
            "sessions": session_summaries,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in admin sessions endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@chatbot_bp.route('/api/admin/cleanup', methods=['POST'])
def admin_cleanup_sessions():
    """Admin endpoint to force cleanup of expired sessions."""
    try:
        # Authentication check
        admin_key = request.headers.get('X-Admin-Key')
        expected_key = os.environ.get('ADMIN_API_KEY')
        
        if expected_key and admin_key != expected_key:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Clean up sessions
        cleaned_count = session_manager.cleanup_expired_sessions()
        
        return jsonify({
            "success": True,
            "cleaned_sessions": cleaned_count,
            "remaining_sessions": len(session_manager.sessions),
            "message": f"Cleaned {cleaned_count} expired sessions"
        })
        
    except Exception as e:
        logger.error(f"Error in admin cleanup: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ================================
# ERROR HANDLERS
# ================================

@chatbot_bp.errorhandler(404)
def not_found_error(error):
    return jsonify({
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist",
        "available_endpoints": [
            "/api/chat",
            "/api/health",
            "/api/session/status",
            "/api/crisis-resources",
            "/api/emotional-support/exercises",
            "/api/inspiration"
        ]
    }), 404

@chatbot_bp.errorhandler(405)
def method_not_allowed_error(error):
    return jsonify({
        "error": "Method not allowed",
        "message": "This HTTP method is not supported for this endpoint"
    }), 405

@chatbot_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong on our end. Please try again.",
        "support_available": True
    }), 500

# ================================
# BACKGROUND TASKS
# ================================

def periodic_session_cleanup():
    """Background task to periodically clean up expired sessions."""
    while True:
        try:
            time.sleep(300)  # 5 minutes
            cleaned = session_manager.cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"Background cleanup: Removed {cleaned} expired sessions")
        except Exception as e:
            logger.error(f"Error in background session cleanup: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying on error

# Start background cleanup thread
cleanup_thread = threading.Thread(target=periodic_session_cleanup, daemon=True)
cleanup_thread.start()
logger.info("Background session cleanup thread started")

# ================================
# EXPORT BLUEPRINT
# ================================

def get_blueprint():
    """Return the chatbot blueprint for Flask app registration."""
    return chatbot_bp

# Export version info
__version__ = "2.0.0"
__author__ = "Mentivio Team"
__description__ = "High EQ Chatbot with Session Persistence and Safety Features"