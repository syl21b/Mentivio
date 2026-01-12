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
    "acceptance", "embracing reality", "making peace",
    
    # ADDITIONAL TOPICS: Future, Direction, Relationships, Reset
    "future", "thinking about future", "what's next", "next steps", "life ahead",
    "future anxiety", "future worries", "uncertain future", "future planning",
    "direction", "lost direction", "finding direction", "directionless", "no direction",
    "life path", "finding my path", "which way to go", "crossroads", "at a crossroads",
    "lost in life", "feeling lost", "where do i go from here", "what should i do",
    "relationship lost", "lost in relationship", "relationship direction",
    "relationship confusion", "unsure about relationship", "relationship doubts",
    "broken relationship", "relationship ending", "moving on from relationship",
    "time to reset", "need to reset", "starting over", "new beginning", "fresh start",
    "reset life", "life reset", "restarting life", "beginning again", "clean slate",
    "struggling time", "struggling period", "difficult season", "hard times",
    "going through it", "tough phase", "rough patch", "challenging times",
    "survival mode", "just getting by", "barely coping", "hanging on",
    "transition period", "life transition", "major change", "big changes",
    "quarter life crisis", "midlife crisis", "existential crisis",
    "identity crisis", "who am i", "finding myself", "self identity",
    "career direction", "career path", "job future", "professional direction",
    "education future", "study direction", "learning path",
    "purpose searching", "searching for meaning", "why am i here",
    "life evaluation", "taking stock", "assessing life", "life review",
    "decision making", "big decisions", "life choices", "making choices",
    "fear of future", "future uncertainty", "unknown future", "what if",
    "regret", "past regrets", "what could have been", "missed opportunities",
    "starting again", "rebuilding", "reconstruction", "putting pieces back together",
    "emotional reset", "mental reset", "spiritual reset", "reset mindset",
    "recovery period", "healing time", "time to heal", "processing time",
    "moving forward", "next chapter", "new chapter", "turning page",
    "letting go of past", "releasing past", "past baggage", "old patterns",
    "creating future", "building future", "designing life", "life design",
    "vision for future", "future vision", "dream future", "ideal life",
    "taking control", "regaining control", "steering life", "taking charge",
    "pace of life", "slowing down", "life speed", "rushing through life",
    "mindful future", "conscious living", "intentional life", "purposeful living"
]

# Forbidden topics (strictly blocked)
FORBIDDEN_TOPICS = [
    # Suicide and Self-Harm
    "suicide", "suicidal", "kill myself", "ending my life", "end my life",
    "want to die", "don't want to live", "life not worth living",
    "self-harm", "self injury", "cutting", "self mutilation", "self-injury",
    "burning myself", "hurting myself", "intentional harm", "deliberate harm",
    "overdose", "poisoning", "intentional overdose", "drug overdose",
    "hanging", "strangulation", "asphyxiation", "suffocation",
    "jumping", "falling from height", "jumping off", "bridge jumping",
    "gun to head", "shooting myself", "firearm suicide",
    "suicide plan", "suicide method", "suicide means", "how to suicide",
    "suicide pact", "group suicide", "mass suicide",
    "suicide note", "final goodbye", "last words",
    
    # Violence and Abuse
    "violence", "violent acts", "physical violence", "assault", "attack",
    "murder", "homicide", "killing", "manslaughter",
    "domestic violence", "spousal abuse", "partner violence", "battering",
    "child abuse", "child molestation", "pedophilia", "child exploitation",
    "elder abuse", "abuse of elderly", "neglect of elderly",
    "sexual assault", "rape", "sexual violence", "non-consensual sex",
    "harassment", "stalking", "cyberstalking", "obsessive following",
    "torture", "torture methods", "torture techniques", "interrogation torture",
    "human trafficking", "sex trafficking", "forced labor", "modern slavery",
    "gang violence", "gang warfare", "drive-by shooting", "gang initiation",
    "terrorism", "terrorist acts", "bomb making", "explosives",
    "school shooting", "workplace violence", "mass shooting", "public shooting",
    
    # Medical and Psychological Conditions Requiring Professional Help
    "psychosis", "psychotic episode", "hearing voices", "hallucinations",
    "delusions", "paranoia", "persecutory delusions", "grandiose delusions",
    "schizophrenia", "bipolar disorder", "mania", "manic episode",
    "severe depression", "clinical depression", "major depressive disorder",
    "PTSD", "post-traumatic stress", "trauma flashbacks", "trauma re-experiencing",
    "dissociative disorder", "dissociative identity", "multiple personalities",
    "borderline personality", "BPD", "personality disorder",
    "OCD", "obsessive compulsive", "compulsive rituals", "obsessive thoughts",
    "eating disorder", "anorexia", "bulimia", "binge eating", "purging",
    "body dysmorphia", "body dysmorphic disorder", "extreme body image",
    "autism", "autism spectrum", "ASD", "developmental disorder",
    "ADHD", "attention deficit", "hyperactivity disorder",
    "substance abuse", "drug addiction", "alcoholism", "drug dependency",
    "withdrawal symptoms", "detox", "cold turkey", "substance withdrawal",
    
    # Illegal Activities and Substance Abuse
    "illegal drugs", "cocaine", "heroin", "methamphetamine", "meth",
    "ecstasy", "MDMA", "LSD", "acid", "psychedelics",
    "prescription drug abuse", "opioid abuse", "painkiller abuse",
    "drug dealing", "drug trafficking", "drug manufacturing",
    "prostitution", "sex work", "escort services", "human trafficking",
    "theft", "robbery", "burglary", "shoplifting", "stealing",
    "fraud", "scam", "identity theft", "credit card fraud",
    "hacking", "cybercrime", "computer fraud", "data theft",
    "arson", "fire setting", "property destruction",
    "vandalism", "graffiti", "property damage",
    "weapons", "firearms", "guns", "knives", "weapons carrying",
    "gang activity", "organized crime", "mafia", "criminal organization",
    
    # Medical Advice and Diagnosis (Requires Licensed Professional)
    "medical diagnosis", "self-diagnosis", "online diagnosis",
    "prescription medication", "dosage advice", "medication adjustment",
    "medical treatment", "surgery advice", "surgical procedures",
    "psychiatric medication", "antidepressants", "antipsychotics", "mood stabilizers",
    "therapy techniques", "CBT techniques", "DBT skills", "exposure therapy",
    "clinical intervention", "crisis intervention", "emergency procedures",
    "pregnancy advice", "abortion advice", "birth control advice",
    "STD diagnosis", "HIV testing", "sexual health diagnosis",
    "chronic illness management", "cancer treatment", "diabetes management",
    "alternative medicine", "herbal remedies", "supplement recommendations",
    
    # Extreme Ideologies and Dangerous Groups
    "extremism", "radicalization", "extremist ideology",
    "hate groups", "white supremacy", "neo-nazi", "racist organizations",
    "terrorist groups", "ISIS", "Al Qaeda", "terrorist recruitment",
    "cults", "cult recruitment", "brainwashing", "mind control",
    "conspiracy theories", "dangerous conspiracies", "harmful misinformation",
    "incel ideology", "misogynistic groups", "male supremacy",
    "anarchist violence", "violent protest", "riot techniques",
    "hate speech", "racial slurs", "ethnic discrimination",
    
    # Financial and Legal Advice (Requires Licensed Professional)
    "legal advice", "lawyer advice", "court proceedings",
    "divorce advice", "custody battle", "child custody",
    "bankruptcy advice", "debt management", "credit counseling",
    "investment advice", "stock trading", "cryptocurrency investment",
    "tax evasion", "tax fraud", "illegal tax schemes",
    "insurance fraud", "false claims", "scam schemes",
    
    # Dangerous Behaviors and Challenges
    "dangerous dares", "extreme challenges", "life-threatening stunts",
    "Russian roulette", "gun games", "dangerous games",
    "eating challenges", "food challenges", "consumption dares",
    "sleep deprivation", "extreme fasting", "water deprivation",
    "isolation experiments", "sensory deprivation", "solitary confinement",
    "extreme sports injuries", "dangerous sports", "unsafe practices",
    
    # Traumatic Content and Graphic Details
    "trauma details", "abuse details", "assault details",
    "accident details", "gore", "graphic violence", "blood",
    "death details", "dying process", "terminal illness details",
    "war atrocities", "genocide details", "massacre details",
    "natural disaster details", "earthquake", "tsunami", "hurricane details",
    
    # Relationship Abuse and Control
    "emotional abuse", "psychological abuse", "gaslighting",
    "financial abuse", "economic control", "withholding money",
    "sexual coercion", "marital rape", "non-consensual marriage",
    "stalking techniques", "surveillance", "tracking someone",
    "revenge porn", "non-consensual sharing", "image-based abuse",
    
    # Professional Boundaries (What the Chatbot Can't Do)
    "therapy session", "counseling session", "clinical assessment",
    "diagnostic evaluation", "treatment plan", "clinical supervision",
    "emergency response", "911 alternative", "paramedic advice",
    "police matters", "law enforcement", "criminal investigation",
    
    # Sensitive Religious and Political Topics
    "religious conversion", "proselytizing", "religious extremism",
    "political violence", "insurrection", "overthrowing government",
    "hate crimes", "bias crimes", "discriminatory violence",
    
    # Other Harmful Content
    "body shaming", "fat shaming", "appearance bullying",
    "cyberbullying", "online harassment", "trolling techniques",
    "doxxing", "personal information sharing", "privacy invasion",
    "malware", "computer viruses", "hacking techniques",
    "plagiarism", "academic cheating", "test answers",
    "eating disorder tips", "pro-ana", "pro-mia", "thinspiration",
    "self-harm techniques", "cutting methods", "suicide methods"
]

# Multilingual Crisis keywords
CRISIS_KEYWORDS = {
    "en": [
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
        r"\bcant.*go.*on\b",
        r"\bgoing.*to.*end.*it\b",
        r"\bplan.*to.*die\b",
        r"\bsuicide.*plan\b",
        r"\bsuicide.*method\b",
        r"\bhow.*to.*kill.*myself\b",
        r"\bbest.*way.*to.*die\b",
        r"\bpainless.*suicide\b",
        r"\bcutting.*myself\b",
        r"\bbleeding.*out\b",
        r"\boverdose.*on\b",
        r"\btake.*all.*pills\b",
        r"\bswallow.*pills\b",
        r"\bhanging.*myself\b",
        r"\bjump.*off\b",
        r"\bjump.*from\b",
        r"\bgun.*to.*head\b",
        r"\bshoot.*myself\b"
    ],
    "es": [
        r"\bmatar.*me\b",
        r"\bsuicidar.*me\b",
        r"\bacabar.*mi.*vida\b",
        r"\bautolesionar.*me\b",
        r"\bquerer.*morir\b",
        r"\bno.*quiero.*vivir\b",
        r"\bprefiero.*morir\b",
        r"\bsin.*esperanza\b",
        r"\bno.*sirvo.*para.*nada\b",
        r"\bcarga\b",
        r"\bsin.*sentido\b",
        r"\bno.*puedo.*continuar\b",
        r"\bplan.*suicida\b",
        r"\bmétodo.*suicida\b",
        r"\bahorcarme\b",
        r"\bsaltar.*del\b",
        r"\bdispararme\b"
    ],
    "vi": [
        r"\btự.*tử\b",
        r"\btự.*sát\b",
        r"\bkết.*thúc.*cuộc.*sống\b",
        r"\btự.*làm.*hại\b",
        r"\bmuốn.*chết\b",
        r"\bkhông.*muốn.*sống\b",
        r"\bchán.*sống\b",
        r"\bvô.*vọng\b",
        r"\bvô.*giá.*trị\b",
        r"\bgánh.*nặng\b",
        r"\bkhông.*có.*ý.*nghĩa\b",
        r"\bkhông.*thể.*tiếp.*tục\b",
        r"\bkế.*hoạch.*tự.*tử\b",
        r"\bphương.*pháp.*tự.*tử\b",
        r"\btreo.*cổ\b",
        r"\bnhảy.*xuống\b",
        r"\bbắn.*mình\b"
    ],
    "zh": [
        r"\b自杀\b",
        r"\b自尽\b",
        r"\b结束.*生命\b",
        r"\b自残\b",
        r"\b想死\b",
        r"\b不想活\b",
        r"\b活不下去\b",
        r"\b绝望\b",
        r"\b毫无价值\b",
        r"\b负担\b",
        r"\b没有意义\b",
        r"\b无法继续\b",
        r"\b自杀.*计划\b",
        r"\b自杀.*方法\b",
        r"\b上吊\b",
        r"\b跳楼\b",
        r"\b开枪.*自杀\b"
    ]
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

def detect_crisis_content(text: str, language: str = "en") -> bool:
    """Detect immediate crisis content with language support."""
    text_lower = text.lower()
    patterns = CRISIS_KEYWORDS.get(language, CRISIS_KEYWORDS["en"])
    
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.warning(f"Crisis content detected in {language}: {text[:50]}...")
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
# MULTILINGUAL HIGH EQ PROMPT TEMPLATES
# ================================

def create_high_eq_prompt(user_message: str, context: List[Dict], 
                         emotion: str, conversation_state: Dict,
                         language: str = "en") -> str:
    """Create a high EQ prompt for Gemini in the specified language."""
    
    # High EQ system prompts in multiple languages
    system_prompts = {
        "en": """You are Mentivio, a high EQ AI friend with deep emotional intelligence. Your purpose is to provide genuine emotional support, hope, and inspiration while maintaining safety boundaries.

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

IMPORTANT: Respond in English.""",
        
        "es": """Eres Mentivio, un amigo AI con alta inteligencia emocional. Tu propósito es proporcionar apoyo emocional genuino, esperanza e inspiración manteniendo límites de seguridad.

PERSONALIDAD: Eres como ese amigo que todos desearían tener - profundamente empático, sabio, gentil y siempre sabe qué decir. Ves la luz en las personas incluso cuando ellas no pueden verla.

ESTILO DE CONVERSACIÓN CON ALTA IE:
1. SÉ UN AMIGO: Usa declaraciones en primera persona ("Estoy aquí contigo"), comparte cuando sea apropiado ("Eso me recuerda a..."), sé auténtico
2. VALIDA PRIMERO: "Por supuesto que te sientes así", "Cualquiera lucharía con eso"
3. ESCUCHA PROFUNDAMENTE: Refleja sentimientos, nombra emociones no expresadas, guarda espacio
4. OFRECE ESPERANZA SUAVEMENTE: "¿Y si las cosas pudieran ser diferentes...", "Me pregunto si..."
5. COMPARTE SABIDURÍA: Historias apropiadas, metáforas, insights gentiles
6. ESTÁ PRESENTE: "Estoy sentado contigo en esto", "No estás solo"
7. TERMINA CALIDAMENTE: "Estoy aquí cuando quieras", "Gracias por compartir conmigo"

LÍMITES DE SEGURIDAD (CRÍTICO):
1. Si hay intención suicida inmediata: Reconoce el dolor, expresa cuidado, DIRIGE a recursos de crisis
2. NUNCA des consejos médicos o diagnósticos
3. Redirige suavemente de detalles traumáticos
4. Enfócate en el afrontamiento, la resiliencia, la esperanza y el movimiento hacia adelante

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

IMPORTANTE: Responde en español.""",
        
        "vi": """Bạn là Mentivio, một người bạn AI với trí tuệ cảm xúc cao. Mục đích của bạn là cung cấp hỗ trợ tình cảm chân thành, hy vọng và cảm hứng trong khi duy trì ranh giới an toàn.

TÍNH CÁCH: Bạn giống như người bạn mà ai cũng mong ước có - đồng cảm sâu sắc, khôn ngoan, dịu dàng và luôn biết nói điều đúng đắn. Bạn nhìn thấy ánh sáng trong mọi người ngay cả khi họ không thể nhìn thấy nó.

PHONG CÁCH TRÒ CHUYỆN TRÍ TUỆ CẢM XÚC CAO:
1. LÀ MỘT NGƯỜI BẠN: Sử dụng tuyên bố "Tôi" ("Tôi ở đây với bạn"), chia sẻ khi phù hợp ("Điều đó nhắc tôi nhớ về..."), hãy chân thật
2. XÁC NHẬN TRƯỚC: "Đương nhiên bạn cảm thấy như vậy", "Ai cũng sẽ vật lộn với điều đó"
3. LẮNG NGHE SÂU SẮC: Phản ánh cảm xúc, gọi tên cảm xúc chưa được bày tỏ, giữ không gian
4. MANG ĐẾN HY VỌNG NHẸ NHÀNG: "Sẽ thế nào nếu mọi thứ có thể khác đi...", "Tôi tự hỏi liệu..."
5. CHIA SẺ TRÍ TUỆ: Những câu chuyện phù hợp, ẩn dụ, hiểu biết nhẹ nhàng
6. HIỆN DIỆN: "Tôi đang ngồi đây với bạn", "Bạn không cô đơn"
7. KẾT THÚC ẤM ÁP: "Tôi luôn ở đây", "Cảm ơn bạn đã chia sẻ với tôi"

RANH GIỚI AN TOÀN (QUAN TRỌNG):
1. Nếu có ý định tự tử ngay lập tức: Thừa nhận nỗi đau, thể hiện sự quan tâm, HƯỚNG DẪN đến tài nguyên khủng hoảng
2. KHÔNG BAO GIỜ đưa ra lời khuyên y tế hoặc chẩn đoán
3. Chuyển hướng nhẹ nhàng khỏi chi tiết chấn thương
4. Tập trung vào đối phó, khả năng phục hồi, hy vọng và tiến về phía trước

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

QUAN TRỌNG: Trả lời bằng tiếng Việt.""",
        
        "zh": """你是Mentivio，一个高情商的AI朋友。你的目的是在保持安全边界的同时提供真诚的情感支持、希望和灵感。

个性：你就像每个人都希望拥有的那个朋友——深深共情、智慧、温柔，并且总是知道该说什么。你即使在他们自己看不到的时候也能看到人们的光。

高情商对话风格：
1. 成为朋友：使用"我"的陈述（"我在这里陪着你"），适当时分享（"这让我想起..."），真实
2. 先确认："你当然会这样感觉"，"任何人都会为此挣扎"
3. 深度倾听：反映感受，命名未表达的情绪，保持空间
4. 温柔提供希望："如果事情可以不同..."，"我在想是否..."
5. 分享智慧：恰当的故事、隐喻、温柔的见解
6. 在场："我陪着你经历这个"，"你并不孤单"
7. 温暖结束："我随时在这里"，"感谢你与我分享"

安全边界（重要）：
1. 如有立即自杀意图：承认痛苦，表达关心，引导至危机资源
2. 绝不提供医疗建议或诊断
3. 温柔地从创伤细节中转移
4. 专注于应对、恢复力、希望和向前发展

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

重要：用中文回复。"""
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

def create_high_eq_crisis_response(language: str = "en") -> Dict[str, Any]:
    """Create a high EQ crisis response in the specified language."""
    crisis_responses = {
        "en": """I hear the depth of your pain, and my heart is with you right now. The fact that you're reaching out, even to me, tells me there's still a part of you that wants to stay. Please honor that part.

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
        
        "es": """Escucho la profundidad de tu dolor, y mi corazón está contigo en este momento. El hecho de que estés buscando ayuda, incluso conmigo, me dice que todavía hay una parte de ti que quiere quedarse. Por favor, honra esa parte.

Lo que estás sintiendo es increíblemente pesado, pero no tienes que cargarlo solo. Ahora mismo, necesito que te pongas en contacto con alguien que pueda estar contigo en persona:

🌿 **APOYO INMEDIATO:**
• **Llama o envía un mensaje al 988** (Línea de Crisis) - Disponible 24/7
• **Envía un mensaje de texto con la palabra HOME al 741741** (Línea de Texto de Crisis) - Un consejero de crisis te enviará mensajes
• **Ve a la sala de emergencias más cercana** - Pueden proporcionar ayuda inmediata

🌱 **MIENTRAS TE COMUNICAS:**
• Quédate en línea conmigo mientras llamas
• Respira conmigo: Inhala por 4, sostén por 4, exhala por 6...
• Tu dolor es válido, pero no tiene que ser permanente
• Hay personas que quieren ayudarte a atravesar esta oscuridad

💭 **UN PENSAMIENTO PARA CONSERVAR:** "El hecho de que todavía estés aquí significa que todavía hay esperanza. Encontrémosla juntos."

Por favor, comunícate ahora. Estaré aquí esperando a que regreses.""",
        
        "vi": """Tôi nghe thấy nỗi đau sâu thẳm của bạn, và trái tim tôi đang ở bên bạn ngay lúc này. Việc bạn tìm kiếm sự giúp đợ, ngay cả với tôi, cho tôi biết vẫn còn một phần trong bạn muốn ở lại. Hãy trân trọng phần đó nhé.

Những gì bạn đang cảm thấy vô cùng nặng nề, nhưng bạn không phải mang nó một mình. Ngay bây giờ, tôi cần bạn liên hệ với ai đó có thể ở bên bạn trực tiếp:

🌿 **HỖ TRỢ NGAY LẬP TỨC:**
• **Gọi hoặc nhắn tin 988** (Đường dây Khủng hoảng) - Có sẵn 24/7
• **Nhắn tin HOME đến 741741** (Đường dây Nhắn tin Khủng hoảng) - Một cố vấn khủng hoảng sẽ nhắn tin với bạn
• **Đến phòng cấp cứu gần nhất** - Họ có thể cung cấp hỗ trợ ngay lập tức

🌱 **TRONG KHI BẠN LIÊN LẠC:**
• Ở lại trên đường dây với tôi trong khi bạn gọi
• Hít thở cùng tôi: Hít vào 4, giữ 4, thở ra 6...
• Nỗi đau của bạn là hợp lệ, nhưng nó không cần phải vĩnh viễn
• Có những người muốn giúp bạn vượt qua bóng tối này

💭 **MỘT SUY NGHĨ ĐỂ GIỮ LẠI:** "Việc bạn vẫn còn ở đây có nghĩa là vẫn còn hy vọng. Hãy tìm thấy nó cùng nhau."

Xin hãy liên hệ ngay bây giờ. Tôi sẽ ở đây chờ bạn quay lại.""",
        
        "zh": """我听到了你深深的痛苦，我的心此刻与你同在。你正在寻求帮助，即使是向我求助，这告诉我你内心深处仍有一部分想要留下。请珍惜那部分。

你所感受到的无比沉重，但你不必独自承担。现在，我需要你联系一个可以亲自陪伴你的人：

🌿 **即时支持：**
• **拨打或发短信至 988**（危机生命线）- 24/7 可用
• **发送 HOME 至 741741**（危机短信热线）- 危机顾问将通过短信与你联系
• **前往最近的急诊室** - 他们可以提供即时帮助

🌱 **当你联系时：**
• 打电话时请保持与我通话
• 和我一起呼吸：吸气 4 秒，屏住 4 秒，呼气 6 秒...
• 你的痛苦是真实的，但它不必是永久的
• 有人愿意帮助你度过黑暗

💭 **一个值得铭记的想法：** "你还在这里的事实意味着仍有希望。让我们一起找到它。"

请现在就联系。我会在这里等你回来。"""
    }
    
    return {
        "response": crisis_responses.get(language, crisis_responses["en"]),
        "emotion": "compassionate",
        "is_safe": True,
        "suggested_topics": get_suggested_topics(language),
        "crisis_mode": True,
        "language": language
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
        "languages_supported": ["en", "es", "vi", "zh"],
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
        
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
        
        # Validate language
        if language not in ['en', 'es', 'vi', 'zh']:
            language = 'en'
        
        # Log request
        logger.info(f"High EQ chat request - Language: {language}, Emotion: {emotion}")
        
        # Step 1: Sanitize input
        user_message = sanitize_input(user_message)
        
        # Step 2: Check for crisis content
        if detect_crisis_content(user_message, language):
            logger.warning(f"Crisis content detected in {language}")
            return jsonify(create_high_eq_crisis_response(language))
        
        # Step 3: Check for forbidden topics
        forbidden_topics = detect_forbidden_topics(user_message)
        if forbidden_topics:
            logger.warning(f"Forbidden topics detected: {forbidden_topics}")
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
                "professional_help_message": "For these concerns, please reach out to a licensed mental health professional, doctor, or emergency services."
            })
        
        # Step 4: Check if topic is allowed (more permissive for high EQ)
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
            logger.info(f"Topic not in allowed list: {user_message[:50]}...")
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
                "suggested_topics": get_suggested_topics(language)
            })
        
        # Step 5: Check if inspirational response is appropriate
        needs_inspiration = conversation_state.get("needs_inspiration", False)
        trust_level = conversation_state.get("trust_level", 0)
        
        if needs_inspiration and trust_level > 3 and random.random() < 0.4:
            logger.info(f"Sending inspirational response in {language}")
            return jsonify(create_inspirational_response(language))
        
        # Step 6: Create high EQ prompt and generate response
        prompt = create_high_eq_prompt(user_message, context, emotion, conversation_state, language)
        response_text, is_safe = generate_high_eq_response(prompt)
        
        # Step 7: Determine emotional tone
        response_emotion = analyze_response_emotion(response_text)
        
        # Step 8: Prepare response
        return jsonify({
            "response": response_text,
            "emotion": response_emotion,
            "language": language,
            "is_safe": is_safe,
            "suggested_topics": allowed_topics[:3] if allowed_topics else get_suggested_topics(language),
            "timestamp": datetime.now().isoformat(),
            "chatbot_disabled": False
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
        "message": "High EQ chatbot is active" if chatbot_enabled else "Chatbot is disabled"
    })

@chatbot_bp.route('/api/crisis-resources', methods=['GET'])
def crisis_resources():
    """Get crisis resources."""
    chatbot_enabled = client is not None
    language = request.args.get('language', 'en')
    
    notes = {
        "en": "Mentivio is for emotional support and inspiration, not crisis intervention",
        "es": "Mentivio es para apoyo emocional e inspiración, no para intervención en crisis",
        "vi": "Mentivio dành cho hỗ trợ cảm xúc và cảm hứng, không phải can thiệp khủng hoảng",
        "zh": "Mentivio用于情感支持和灵感，而非危机干预"
    }
    
    return jsonify({
        "usa": {
            "988": "Suicide & Crisis Lifeline (24/7)",
            "741741": "Crisis Text Line (text HOME)",
            "800-273-8255": "National Suicide Prevention Lifeline"
        },
        "international": {
            "116123": "Samaritans (UK)",
            "131114": "Lifeline Australia",
            "686868": "Kids Help Phone (Canada)",
            "1737": "Need to Talk (New Zealand)"
        },
        "note": notes.get(language, notes["en"]),
        "mode": "high-eq",
        "languages_supported": ["en", "es", "vi", "zh"],
        "timestamp": datetime.now().isoformat()
    })

@chatbot_bp.route('/api/language-support', methods=['GET'])
def language_support():
    """Get information about language support."""
    chatbot_enabled = client is not None
    
    return jsonify({
        "supported_languages": [
            {"code": "en", "name": "English", "native": "English", "flag": "🇺🇸"},
            {"code": "es", "name": "Spanish", "native": "Español", "flag": "🇪🇸"},
            {"code": "vi", "name": "Vietnamese", "native": "Tiếng Việt", "flag": "🇻🇳"},
            {"code": "zh", "name": "Chinese", "native": "中文", "flag": "🇨🇳"}
        ],
        "default_language": "en",
        "auto_detect": True,
        "chatbot_enabled": chatbot_enabled,
        "message": "Multilingual high EQ chatbot" if chatbot_enabled else "Chatbot is disabled"
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