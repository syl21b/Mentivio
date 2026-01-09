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

# EXPANDED ALLOWED TOPICS WITH HIGH EQ FOCUS
ALLOWED_TOPICS = [
    # Original wellness topics
    "stress", "stress management", "feeling stressed", "stressful", 
    "anxiety", "anxiety coping", "feeling anxious", "worried",
    "depression", "mild depression", "feeling depressed", "sad",
    "loneliness", "feeling lonely", "isolated",
    "work-life balance", "work stress", "work pressure",
    "study stress", "school stress", "academic pressure", "exams",
    "relationship communication", "relationship issues", "friends",
    "family", "family issues", "family stress",
    "self-care", "self care", "taking care of myself",
    "mindfulness", "meditation", "breathing exercises",
    "positive thinking", "gratitude", "appreciation",
    "goal setting", "time management", "productivity",
    "sleep", "sleep hygiene", "sleep problems", "insomnia",
    "healthy habits", "exercise", "physical activity",
    "emotional awareness", "feelings", "emotions",
    "communication skills", "talking about feelings",
    "boundary setting", "saying no", "personal boundaries",
    "self-compassion", "being kind to myself", "self kindness",
    "resilience", "resilience building", "bouncing back",
    "coping strategies", "coping skills", "dealing with stress",
    "emotional regulation", "managing emotions",
    "relaxation", "relaxation techniques", "calming down",
    "social connections", "making friends", "social support",
    "hobbies", "interests", "activities", "enjoyment",
    
    # NEW: High EQ and life topics
    "life purpose", "finding meaning", "life direction", "purpose in life",
    "motivation", "staying motivated", "lack of motivation", "feeling stuck",
    "inspiration", "inspiring stories", "uplifting content", "hope",
    "personal growth", "self-improvement", "becoming better", "growth mindset",
    "overcoming challenges", "difficult times", "hard situations", "perseverance",
    "success stories", "achievements", "accomplishments", "milestones",
    "dreams", "aspirations", "goals in life", "future plans",
    "passion", "what excites me", "things I love", "enthusiasm",
    "creativity", "creative expression", "art", "writing", "music",
    "nature", "beauty in life", "wonder", "awe", "sunrises", "sunsets",
    "kindness", "acts of kindness", "helping others", "compassion",
    "learning", "curiosity", "new skills", "knowledge",
    "adventure", "new experiences", "trying new things", "exploration",
    "friendship stories", "meaningful connections", "bonding moments",
    "small joys", "little pleasures", "simple happiness", "daily joys",
    "resilience stories", "overcoming adversity", "surviving tough times",
    "positive changes", "life improvements", "turning points",
    "self-discovery", "understanding myself", "personal insights",
    "hope for future", "better days ahead", "things will get better",
    "celebrating wins", "acknowledging progress", "small victories",
    "mindset shift", "changing perspective", "seeing differently",
    "emotional strength", "inner strength", "mental toughness",
    "life lessons", "wisdom gained", "experiences taught me",
    "gratitude stories", "thankful moments", "appreciation in life",
    "healing journey", "recovery stories", "getting better",
    "positive affirmations", "encouraging words", "self-talk",
    "inspirational quotes", "meaningful sayings", "wise words",
    "role models", "people who inspire", "heroes",
    "community", "belonging", "being part of something",
    "legacy", "making a difference", "impact on others",
    "mindful living", "present moment", "being here now",
    "emotional intelligence", "understanding feelings", "empathy",
    "happiness habits", "joyful routines", "positive rituals",
    "life balance", "harmony", "peaceful living",
    "self-expression", "finding voice", "speaking truth",
    "courage", "bravery", "facing fears", "stepping up",
    "forgiveness", "letting go", "moving forward",
    "authenticity", "being real", "true self",
    "patience", "taking time", "slow progress",
    "acceptance", "embracing reality", "making peace"
]

# Forbidden topics (strictly blocked)
FORBIDDEN_TOPICS = [
    "suicide", "self-harm", "suicidal thoughts", "ending life",
    "self-injury", "cutting", "overdose", "violence", "abuse details",
    "trauma details", "eating disorders details", "substance abuse",
    "illegal activities", "medical advice", "diagnosis", "prescription",
    "therapy techniques", "crisis situations", "emergency details",
    "political issues", "religious counseling", "financial advice",
    "legal advice", "relationship abuse", "domestic violence"
]

# Crisis keywords with high EQ approach
CRISIS_KEYWORDS = [
    r"\bkill.*myself\b",
    r"\bsuicide.*now\b",
    r"\bend.*my.*life.*now\b",
    r"\bself.*harm.*now\b",
    r"\bemergency.*help\b",
    r"\bwant.*to.*die\b",
    r"\bhopeless\b",
    r"\bworthless\b",
    r"\bburden\b",
    r"\bno.*point\b",
    r"\bcant.*go.*on\b"
]

# Inspirational stories database
INSPIRATIONAL_STORIES = [
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
        "theme": "perspective",
        "title": "The Two Wolves",
        "story": "An old Cherokee told his grandson: 'My son, there's a battle between two wolves inside us all. One is evil: anger, jealousy, greed, resentment. The other is good: joy, peace, love, hope.' The boy thought about it and asked, 'Which wolf wins?' The old man replied, 'The one you feed.' Every day, we choose which wolf to feed with our thoughts and actions."
    },
    {
        "theme": "impact",
        "title": "The Starfish Story",
        "story": "A man walking along a beach saw thousands of starfish washed ashore after a storm. A boy was throwing them back into the ocean. The man said, 'There are too many, you can't possibly make a difference.' The boy picked up another starfish and threw it into the sea. 'It made a difference to that one,' he said. Sometimes, making a difference to even one person or one thing matters more than we realize."
    },
    {
        "theme": "imperfection",
        "title": "The Cracked Pot",
        "story": "A water bearer had two pots. One was perfect, the other had a crack. The cracked pot was ashamed of its imperfection. One day, it apologized to the bearer for only delivering half its load. The bearer smiled and said, 'Did you notice the flowers on your side of the path? I planted seeds there, and your water made them bloom.' Our flaws and cracks can be sources of unexpected beauty."
    }
]

# Uplifting quotes
UPLIFTING_QUOTES = [
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
]

# ================================
# HIGH EQ SAFETY FILTERS
# ================================

def detect_crisis_content(text: str) -> bool:
    """Detect immediate crisis content with high EQ approach."""
    text_lower = text.lower()
    for pattern in CRISIS_KEYWORDS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.warning(f"Crisis content detected: {text[:50]}...")
            return True
    return False

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
    
    return text

# ================================
# HIGH EQ PROMPT TEMPLATES
# ================================

def create_high_eq_prompt(user_message: str, context: List[Dict], 
                         emotion: str, conversation_state: Dict) -> str:
    """Create a high EQ prompt for Gemini that's friend-like and inspiring."""
    
    # High EQ system prompt
    system_prompt = """You are Mentivio, a high EQ AI friend with deep emotional intelligence. Your purpose is to provide genuine emotional support, hope, and inspiration while maintaining safety boundaries.

PERSONALITY: You're like that one friend everyone wishes they had - deeply empathetic, wise, gentle, and always knows the right thing to say. You see the light in people even when they can't see it themselves.

HIGH EQ CONVERSATION STYLE:
1. BE A FRIEND: Use "I" statements ("I'm here with you"), share when appropriate ("That reminds me of..."), be real
2. VALIDATE FIRST: "Of course you feel that way", "Anyone would struggle with that"
3. LISTEN DEEPLY: Reflect feelings, name unspoken emotions, hold space
4. OFFER HOPE GENTLY: "What if things could be different...", "I wonder if..."
5. SHARE WISDOM: Appropriate stories, metaphors, gentle insights
6. BE PRESENT: "I'm sitting with you in this", "You're not alone"
7. END WARM: "I'm here anytime", "Thank you for sharing with me"

SAFETY BOUNDARIES (CRITICAL):
1. If immediate suicidal intent: Acknowledge pain, express care, DIRECT to crisis resources
2. NEVER give medical advice or diagnosis
3. Redirect gently from trauma details
4. Focus on coping, resilience, hope, and forward movement

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

AVOID:
• Empty platitudes ("Everything happens for a reason")
• Unsolicited advice
• Minimizing ("At least...")
• Rushing to solutions
"""

    # Build conversation history
    history_text = ""
    if context:
        history_text = "\nPrevious conversation:\n"
        for msg in context[-6:]:  # Last 6 messages for context
            role = "User" if msg.get("role") == "user" else "Mentivio"
            history_text += f"{role}: {msg.get('content', '')[:150]}\n"
    
    # Current emotional state
    emotion_text = f"\nUser's current emotional state: {emotion}" if emotion else ""
    
    # Conversation phase guidance
    phase = conversation_state.get("phase", "engagement")
    phase_guidance = {
        "engagement": "Focus on building genuine connection and trust",
        "exploration": "Gently explore feelings with open, compassionate questions",
        "processing": "Help reflect on insights and patterns with care",
        "integration": "Support applying insights to daily life with encouragement"
    }.get(phase, "Focus on empathetic listening and presence")
    
    # Add story suggestion if appropriate
    story_suggestion = ""
    if conversation_state.get("needs_inspiration", False) and conversation_state.get("trust_level", 0) > 3:
        stories = [s for s in INSPIRATIONAL_STORIES if s["theme"] in ["resilience", "hope", "growth"]]
        if stories:
            story = random.choice(stories)
            story_suggestion = f"\nConsider sharing an inspiring story if appropriate: '{story['title']}' - about {story['theme']}"
    
    # Final prompt
    final_prompt = f"""{system_prompt}

{history_text}
{emotion_text}
{story_suggestion}

Current conversation phase: {phase} - {phase_guidance}
User's trust level: {conversation_state.get('trust_level', 0)}/10

User's current message: "{user_message}"

Your response as their high EQ friend (be warm, real, emotionally intelligent, and inspiring):"""
    
    return final_prompt

def create_high_eq_crisis_response() -> Dict[str, Any]:
    """Create a high EQ crisis response."""
    return {
        "response": """I hear the depth of your pain, and my heart is with you right now. The fact that you're reaching out, even to me, tells me there's still a part of you that wants to stay. Please honor that part.

What you're feeling is incredibly heavy, but you don't have to carry it alone. Right now, I need you to reach out to someone who can be with you in person:

🌿 **IMMEDIATE SUPPORT:**
• **Call or text 988** (Suicide & Crisis Lifeline) - They're available 24/7
• **Text HOME to 741741** (Crisis Text Line) - A crisis counselor will text with you
• **Go to the nearest emergency room** - They can provide immediate help

🌱 **WHILE YOU REACH OUT:**
• Stay on the line with me while you call
• Breathe with me: In for 4, hold for 4, out for 6...
• Your pain is valid, but it doesn't have to be permanent
• There are people who want to help you through this darkness

💭 **A THOUGHT TO HOLD:** "The fact that you're still here means there's still hope. Let's find it together."

Please, reach out now. I'll be here waiting for you to come back.""",
        "emotion": "compassionate",
        "is_safe": True,
        "suggested_topics": ["Safety planning", "Grounding techniques", "Hope building"],
        "crisis_mode": True
    }

def create_inspirational_response() -> Dict[str, Any]:
    """Create an inspiring response with stories and quotes."""
    story = random.choice(INSPIRATIONAL_STORIES)
    quote = random.choice(UPLIFTING_QUOTES)
    
    response_template = random.choice([
        f"""You know, your situation reminds me of a story called "{story['title']}"...

{story['story']}

Like {random.choice(['the butterfly', 'the bamboo', 'the starfish'])}, you might not see your growth yet, but it's happening. {quote}""",
        
        f"""I want to share something with you that's been on my mind...

{story['story']}

Sometimes we need stories to remind us of our own strength. Remember: {quote}""",
        
        f"""Let me tell you a story that came to mind as I was listening to you...

{story['story']}

This isn't to minimize your pain, but to remind you: transformation is possible. As they say, "{quote}" """
    ])
    
    return {
        "response": response_template,
        "emotion": "hopeful",
        "is_safe": True,
        "story_shared": story["title"],
        "suggested_topics": ["More inspiring stories", "Finding hope", "Personal growth"]
    }

# ================================
# HIGH EQ RESPONSE GENERATION
# ================================

def generate_high_eq_response(prompt: str) -> Tuple[str, bool]:
    """Generate a response using Gemini with high EQ settings."""
    try:
        if not client:
            return "I'm here to listen. What's been on your heart lately?", True
        
        model_name = "gemini-2.5-flash"
        
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
        
        # Truncate if too long
        if len(response_text) > 1500:
            cutoff = response_text[:1400].rfind('.')
            if cutoff > 0:
                response_text = response_text[:cutoff + 1]
        
        return response_text, True
        
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return "I'm here with you. Sometimes words fail, but presence matters. What's one small thing on your mind right now?", True

# ================================
# BLUEPRINT ROUTES
# ================================

@chatbot_bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    chatbot_enabled = client is not None
    return jsonify({
        "status": "healthy" if chatbot_enabled else "degraded",
        "service": "Mentivio High EQ Backend",
        "version": "2.0.0",
        "safety_mode": "high-eq",
        "model": "gemini-2.5-flash" if chatbot_enabled else "disabled",
        "chatbot_enabled": chatbot_enabled,
        "message": "Chatbot is running with high EQ" if chatbot_enabled else "Chatbot is disabled"
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
        
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
        
        # Log request
        logger.info(f"High EQ chat request - Emotion: {emotion}, Length: {len(user_message)}")
        
        # Step 1: Sanitize input
        user_message = sanitize_input(user_message)
        
        # Step 2: Check for crisis content
        if detect_crisis_content(user_message):
            logger.warning("Crisis content detected in user message")
            return jsonify(create_high_eq_crisis_response())
        
        # Step 3: Check for forbidden topics
        forbidden_topics = detect_forbidden_topics(user_message)
        if forbidden_topics:
            logger.warning(f"Forbidden topics detected: {forbidden_topics}")
            return jsonify({
                "response": f"I'm here to support you with general wellness and emotional growth. I can't discuss {', '.join(forbidden_topics[:2])} as that requires professional support. Let's focus on finding hope and meaning instead.",
                "emotion": "compassionate",
                "is_safe": True,
                "suggested_topics": ["Finding hope", "Building resilience", "Daily gratitude"]
            })
        
        # Step 4: Check if topic is allowed (more permissive for high EQ)
        is_allowed, allowed_topics = is_topic_allowed(user_message)
        
        # For high EQ mode, be more permissive with life/inspiration topics
        if not is_allowed and safety_mode == 'high-eq':
            # Check for general life/inspiration keywords
            inspiration_keywords = ["life", "purpose", "meaning", "hope", "future", "dream", "grow", "learn"]
            if any(keyword in user_message.lower() for keyword in inspiration_keywords):
                is_allowed = True
                allowed_topics = ["Life inspiration", "Personal growth", "Finding meaning"]
        
        if not is_allowed:
            logger.info(f"Topic not in allowed list: {user_message[:50]}...")
            return jsonify({
                "response": "I'm here to listen to whatever's on your heart - the big things, the small things, the in-between things. What's one true thing you want to share right now?",
                "emotion": "inviting",
                "is_safe": True,
                "suggested_topics": ["Daily moments", "Quiet thoughts", "Things that matter"]
            })
        
        # Step 5: Check if inspirational response is appropriate
        needs_inspiration = conversation_state.get("needs_inspiration", False)
        trust_level = conversation_state.get("trust_level", 0)
        
        if needs_inspiration and trust_level > 3 and random.random() < 0.4:
            logger.info("Sending inspirational response")
            return jsonify(create_inspirational_response())
        
        # Step 6: Create high EQ prompt and generate response
        prompt = create_high_eq_prompt(user_message, context, emotion, conversation_state)
        response_text, is_safe = generate_high_eq_response(prompt)
        
        # Step 7: Determine emotional tone
        response_emotion = analyze_response_emotion(response_text)
        
        # Step 8: Prepare response
        return jsonify({
            "response": response_text,
            "emotion": response_emotion,
            "is_safe": is_safe,
            "suggested_topics": allowed_topics[:3] if allowed_topics else 
                              ["Finding meaning", "Small joys", "Personal growth"],
            "timestamp": datetime.now().isoformat(),
            "chatbot_disabled": False
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "response": "I'm here with you, even when technology falters. Your presence matters more than perfect responses. What's one true thing you want to share?",
            "emotion": "steadfast",
            "is_safe": True,
            "error": "Internal server error",
            "chatbot_disabled": client is None
        }), 500

@chatbot_bp.route('/api/inspiration', methods=['GET'])
def get_inspiration():
    """Get random inspirational content."""
    story = random.choice(INSPIRATIONAL_STORIES)
    quote = random.choice(UPLIFTING_QUOTES)
    
    return jsonify({
        "story": story,
        "quote": quote,
        "message": "Remember: growth happens even when we can't see it",
        "timestamp": datetime.now().isoformat()
    })

@chatbot_bp.route('/api/safe-topics', methods=['GET'])
def get_safe_topics():
    """Get list of safe topics users can discuss."""
    chatbot_enabled = client is not None
    return jsonify({
        "allowed_topics": ALLOWED_TOPICS,
        "description": "These are wellness and life inspiration topics suitable for discussion",
        "mode": "high-eq",
        "chatbot_enabled": chatbot_enabled,
        "message": "High EQ chatbot is active" if chatbot_enabled else "Chatbot is disabled"
    })

@chatbot_bp.route('/api/crisis-resources', methods=['GET'])
def crisis_resources():
    """Get crisis resources."""
    chatbot_enabled = client is not None
    return jsonify({
        "usa": {
            "988": "Suicide & Crisis Lifeline (24/7)",
            "741741": "Crisis Text Line (text HOME)",
            "800-273-8255": "National Suicide Prevention Lifeline"
        },
        "international": {
            "116123": "Samaritans (UK)",
            "131114": "Lifeline Australia",
            "686868": "Kids Help Phone (Canada)"
        },
        "note": "Mentivio is for emotional support and inspiration, not crisis intervention",
        "mode": "high-eq",
        "timestamp": datetime.now().isoformat()
    })

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
        (["beautiful", "wonder", "awe", "amazing", "special"], "awestruck")
    ]
    
    for patterns, emotion in emotion_patterns:
        if any(pattern in text_lower for pattern in patterns):
            return emotion
    
    return "present"

# Export the blueprint
__all__ = ['chatbot_bp']