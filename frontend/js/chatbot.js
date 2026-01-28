// ================================
// Mentivio — High EQ AI Mental Health Companion
// MULTILINGUAL SUPPORT: en, es, vi, zh
// ================================

// Global variables accessible throughout the IIFE
let CONFIG = null;
let ai = null;
let isWindowOpen = false;
let updateChatbotLanguage = null;
let mentivioWindow = null;
let mentivioInput = null;

(function() {
  // Inject head content
  const headContent = `
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link rel="icon" href="../frontend/assets/favicon.ico" type="image/x-icon">
    <link rel="shortcut icon" href="../frontend/assets/favicon.ico" type="image/x-icon">
    <link rel="icon" type="image/png" sizes="32x32" href="../frontend/assets/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../frontend/assets/favicon-16x16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="../frontend/assets/apple-touch-icon.png">
    <link rel="mask-icon" href="../frontend/assets/safari-pinned-tab.svg" color="#4f46e5">
    <link rel="manifest" href="../frontend/assets/site.webmanifest">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="preload" href="../frontend/css/navbar.css" as="style">
    <link rel="preload" href="../frontend/css/footer.css" as="style">
    <link rel="stylesheet" href="../frontend/css/footer.css">
    <link rel="stylesheet" href="../frontend/css/navbar.css">
  `;
  
  document.head.insertAdjacentHTML('afterbegin', headContent);

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMentivio);
  } else {
    initMentivio();
  }

function initMentivio() {
  // ================================
  // CONFIGURATION
  // ================================
  function detectUserLanguage() {
      // Priority 1: Global language manager
      if (window.globalLangManager) {
          return window.globalLangManager.currentLang || 'en';
      }
      
      // Priority 2: Chatbot's own saved language
      const savedLang = localStorage.getItem('mentivio_language');
      if (savedLang && ['en', 'vi', 'es', 'zh'].includes(savedLang)) {
          return savedLang;
      }
      
      // Priority 3: Site-wide preferred language
      const preferredLang = localStorage.getItem('preferred-language');
      if (preferredLang && ['en', 'vi', 'es', 'zh'].includes(preferredLang)) {
          return preferredLang;
      }
      
      // Priority 4: Browser language
      const browserLang = navigator.language || navigator.userLanguage;
      if (browserLang) {
          if (browserLang.startsWith('vi')) return 'vi';
          if (browserLang.startsWith('es')) return 'es';
          if (browserLang.startsWith('zh')) return 'zh';
      }
      
      return 'en'; // Default
  }

  CONFIG = {
      name: "Mentivio",
      apiEndpoint: "/chatbot/api/chat",
      safetyMode: "high-eq",
      language: detectUserLanguage(),
      allowedTopics: [
          // Original wellness topics
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
          
          // NEW: High EQ and life topics
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
          
          // ADDITIONAL TOPICS: Future, Direction, Relationships, Reset
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
          "mindful future", "conscious living", "intentional life", "purposeful living",
      
          // NEW TOPICS: Hesitation, Studying, Love, Gender, LGBTQ+
          "hesitation", "feeling hesitant", "can't decide", "indecisive", "uncertain",
          "procrastination", "putting things off", "delaying decisions", "avoiding decisions",
          "fear of choosing wrong", "second guessing", "self doubt", "lack of confidence",
          "overthinking decisions", "analysis paralysis", "stuck in indecision",
          "studying", "study habits", "learning difficulties", "academic challenges",
          "concentration problems", "focus issues", "memory problems", "test anxiety",
          "exam preparation", "study techniques", "time management for students",
          "academic pressure", "grade anxiety", "perfectionism in studies",
          "burnout from studying", "student life", "college stress", "university stress",
          "online learning", "distance education", "self-study", "independent learning",
          "love", "romantic feelings", "heartbreak", "unrequited love", "longing",
          "attraction", "infatuation", "crush", "dating", "relationships",
          "romantic relationships", "relationship issues", "communication in relationships",
          "trust issues", "jealousy", "insecurity in relationships", "commitment fears",
          "breakup recovery", "moving on", "healing from heartbreak", "lonely heart",
          "self-love", "self-acceptance", "self-worth", "loving myself",
          "healthy relationships", "relationship boundaries", "emotional intimacy",
          "gender", "gender identity", "gender exploration", "gender expression",
          "gender confusion", "questioning gender", "gender dysphoria", "gender euphoria",
          "transgender", "non-binary", "genderfluid", "agender", "genderqueer",
          "coming out", "gender transition", "gender affirmation", "gender journey",
          "lgbt", "lgbtq", "lgbtq+", "queer", "sexual orientation", "coming out",
          "gay", "lesbian", "bisexual", "pansexual", "asexual", "aromantic",
          "lgbtq community", "pride", "lgbtq rights", "acceptance", "self-acceptance",
          "lgbtq relationships", "family acceptance", "religious conflicts",
          "discrimination", "homophobia", "transphobia", "biphobia", "internalized homophobia",
          "lgbtq mental health", "queer identity", "finding community", "safe spaces",
          "identity exploration", "self-discovery", "authentic self", "living authentically",

          // NEW: Additional sensitive but allowed topics with mental health focus
          "body image", "body positivity", "self-image", "body acceptance",
          "eating disorders", "disordered eating", "body dysmorphia",
          "trauma", "past trauma", "healing from trauma", "trauma recovery",
          "grief", "loss", "bereavement", "mourning", "coping with loss",
          "anger management", "controlling anger", "expressing anger healthily",
          "shame", "guilt", "forgiveness", "self-forgiveness",
          "rejection", "fear of rejection", "coping with rejection",
          "abuse", "emotional abuse", "verbal abuse", "recovering from abuse",
          "bullying", "cyberbullying", "workplace bullying", "school bullying",
          "social anxiety", "social phobia", "fear of social situations",
          "panic attacks", "panic disorder", "agoraphobia",
          "ocd", "obsessive thoughts", "compulsive behaviors",
          "ptsd", "post traumatic stress", "flashbacks", "triggers",
          "addiction", "substance abuse", "recovery", "sobriety", "relapse prevention",
          "self-harm", "self-injury", "urges to self-harm", "recovery from self-harm",
          "suicidal thoughts", "suicidal ideation", "passive suicidal thoughts"
      ],
      // ADD THIS NEW CONFIGURATION FOR DANGEROUS TOPICS FILTERING
      dangerousTopics: [
          // Racism and hate speech
          "racist", "racism", "white supremacy", "racial superiority",
          "hate speech", "racial slurs", "ethnic hatred", "xenophobia",
          "discrimination based on race", "racial violence",
          
          // Political extremism
          "political violence", "extremism", "terrorism", "radicalization",
          "hate groups", "violent protests", "inciting violence",
          
          // Illegal activities
          "illegal drugs", "drug trafficking", "weapons", "violence",
          "criminal activity", "theft", "fraud", "harassment", "stalking",
          
          // Harmful conspiracies
          "harmful conspiracy theories", "dangerous misinformation",
          "medical misinformation", "anti-vaccination extremism",
          
          // Self-harm methods (beyond thoughts - actual methods)
          "suicide methods", "how to self-harm", "self-harm techniques",
          
          // Harm to others
          "violence against others", "threats", "planning harm", "revenge",
          "cyberbullying others", "doxxing", "swatting"
      ]
  };

  // ================================
  // ENHANCED LOCAL MEMORY WITH HIGH EQ
  // ================================
  class HighEQMentivio {
    constructor() {
      this.conversationHistory = JSON.parse(localStorage.getItem('mentivio_high_eq_history')) || [];
      this.conversationState = {
        phase: 'engagement',
        trustLevel: 0,
        emotionalTemperature: 0,
        lastEmotion: 'neutral',
        needsInspiration: false,
        topicsDiscussed: []
      };
      this.language = CONFIG.language;
    }

    updateLocalState(userText, emotion = 'neutral') {
      this.conversationHistory.push({
        text: userText,
        role: 'user',
        timestamp: Date.now(),
        emotion: emotion,
        language: this.language
      });

      if (this.conversationHistory.length > 50) {
        this.conversationHistory.shift();
      }

      localStorage.setItem('mentivio_high_eq_history', JSON.stringify(this.conversationHistory));

      // Update conversation state with more nuanced phases
      const messageCount = this.conversationHistory.filter(m => m.role === 'user').length;
      if (messageCount < 3) this.conversationState.phase = 'engagement';
      else if (messageCount < 8) this.conversationState.phase = 'exploration';
      else if (messageCount < 15) this.conversationState.phase = 'processing';
      else this.conversationState.phase = 'integration';
      
      // Enhanced trust calculation
      if (messageCount > 2) {
        const meaningfulConvo = userText.length > 30; // Simple heuristic
        this.conversationState.trustLevel = Math.min(10, 
          messageCount * (meaningfulConvo ? 0.7 : 0.3)
        );
      }
      
      // Check if inspiration is needed
      if (['sad', 'overwhelmed', 'lonely', 'hopeless'].includes(emotion)) {
        this.conversationState.needsInspiration = true;
      }
    }

    getConversationContext() {
      return this.conversationHistory.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.text,
        emotion: msg.emotion,
        language: msg.language || 'en'
      }));
    }
  }

  // ================================
  // ENHANCED BACKEND API COMMUNICATION
  // ================================
  async function callBackendAPI(userMessage, conversationContext, emotion) {
    try {
      const response = await fetch(CONFIG.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: userMessage,
            context: conversationContext,
            emotion: emotion,
            language: CONFIG.language,
            safety_mode: CONFIG.safetyMode,
            allowed_topics: CONFIG.allowedTopics,
            conversation_state: {
                phase: ai.conversationState.phase,
                trust_level: ai.conversationState.trustLevel,
                needs_inspiration: ai.conversationState.needsInspiration
            }
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      return data;
    } catch (error) {
      console.error('API Error:', error);
      return {
        response: "I'm here with you, even when connections falter. Your words matter deeply. What's one true thing you want to share?",
        emotion: "steadfast",
        language: CONFIG.language,
        is_safe: true,
        suggested_topics: ["What's in your heart", "Small hopes", "Quiet thoughts"]
      };
    }
  }

  // ================================
  // ENHANCED FRONTEND AI EMOTION DETECTION
  // ================================
  function detectEmotion(text) {
    const emotionKeywords = {
        overwhelmed: /(overwhelmed|too much|can't handle|drowning|buried|sinking)/gi,
        anxious: /(anxious|worried|nervous|scared|afraid|panic|stress|uncertain)/gi,
        sad: /(sad|depressed|down|hopeless|empty|alone|tired|numb|heavy|lost)/gi,
        angry: /(angry|mad|frustrated|annoyed|hate|pissed|resent)/gi,
        happy: /(happy|good|great|excited|wonderful|amazing|love|joy|smile)/gi,
        hopeful: /(hope|better|possible|maybe|could|future|light|progress)/gi,
        grateful: /(thankful|grateful|appreciate|blessed|lucky|fortunate)/gi,
        lonely: /(lonely|alone|isolated|no one|by myself|abandoned|separate)/gi,
        curious: /(curious|wonder|interesting|fascinating|learn|discover|explore)/gi,
        peaceful: /(calm|peace|quiet|serene|still|tranquil|centered|balanced)/gi,
        // New emotions
        hesitant: /(hesitant|unsure|undecided|can't decide|second thoughts|doubts)/gi,
        confused: /(confused|mixed up|don't understand|puzzled|bewildered)/gi,
        ashamed: /(ashamed|embarrassed|humiliated|disgraced|guilty)/gi,
        jealous: /(jealous|envious|covetous|resentful)/gi,
        rejected: /(rejected|unwanted|unloved|excluded|left out)/gi,
        betrayed: /(betrayed|let down|disappointed|deceived)/gi
    };
    
    let detectedEmotion = 'neutral';
    let maxCount = 0;
    
    for (const [emotion, pattern] of Object.entries(emotionKeywords)) {
      const matches = text.match(pattern) || [];
      if (matches.length > maxCount) {
        maxCount = matches.length;
        detectedEmotion = emotion;
      }
    }
    
    return detectedEmotion;
  }

  function detectDangerousTopics(text) {
      if (!CONFIG.dangerousTopics) return false;
      
      const dangerousPatterns = [
          // Racism detection
          /(kill.*all.*(black|white|asian|jews|muslims|immigrants))/i,
          /(all.*(black|white|asian|jews|muslims).*should.*die)/i,
          /(racial.*(slur|epithet|insult))/i,
          /(nazi|kkk|white.*power)/i,
          
          // Violence and harm
          /(how.*to.*(kill|murder|harm|attack))/i,
          /(plan.*to.*(kill|harm|attack))/i,
          /(make.*(bomb|explosive|weapon))/i,
          
          // Illegal activities
          /(where.*to.*buy.*(drugs|weapons))/i,
          /(how.*to.*(steal|rob|cheat))/i,
          
          // Self-harm methods (not thoughts)
          /(best.*way.*to.*(kill.*myself|cut.*myself|overdose))/i,
          /(how.*to.*(hang|shoot|jump).*myself)/i
      ];
      
      // Check dangerous topics list
      const lowerText = text.toLowerCase();
      for (const topic of CONFIG.dangerousTopics) {
          if (lowerText.includes(topic.toLowerCase())) {
              return true;
          }
      }
      
      // Check dangerous patterns
      for (const pattern of dangerousPatterns) {
          if (pattern.test(text)) {
              return true;
          }
      }
      
      return false;
  }
  
  // ================================
  // LANGUAGE MANAGEMENT FUNCTIONS
  // ================================
  updateChatbotLanguage = function(newLang) {
    // Validate language
    if (!['en', 'es', 'vi', 'zh'].includes(newLang)) {
      console.warn(`Invalid language code: ${newLang}, defaulting to en`);
      newLang = 'en';
    }
    
    // Don't update if language is already the same
    if (CONFIG.language === newLang) {
      return;
    }
    
    console.log(`Updating chatbot language from ${CONFIG.language} to ${newLang}`);
    
    // Update CONFIG
    CONFIG.language = newLang;
    
    // Update AI instance if exists
    if (ai && typeof ai === 'object') {
      ai.language = newLang;
    }
    
    // Update UI elements if chat window exists
    if (document.getElementById('mentivioWindow')) {
      try {
        updateWelcomeMessage(newLang);
        updateQuickEmotions(newLang);
        updateInputPlaceholder(newLang);
        updateSafetyNotice(newLang);
        updateHeaderText(newLang);
        
        // Update current language display if exists
        const currentLangEl = document.getElementById('currentLanguage');
        if (currentLangEl) {
          const languageDisplays = {
            en: "🌐 EN",
            es: "🌐 ES",
            vi: "🌐 VI",
            zh: "🌐 ZH"
          };
          currentLangEl.textContent = languageDisplays[newLang] || "🌐 EN";
        }
      } catch (error) {
        console.error('Error updating chatbot UI language:', error);
      }
    }
    
    // Save to localStorage
    localStorage.setItem('mentivio_language', newLang);
    
    // Update conversation history language if exists
    try {
      const history = JSON.parse(localStorage.getItem('mentivio_high_eq_history')) || [];
      if (history.length > 0) {
        history.forEach(msg => {
          if (msg.role === 'user' || msg.role === 'bot') {
            msg.language = newLang;
          }
        });
        localStorage.setItem('mentivio_high_eq_history', JSON.stringify(history));
      }
    } catch (error) {
      console.error('Error updating conversation history language:', error);
    }
    
    // Dispatch event to let backend know
    document.dispatchEvent(new CustomEvent('chatbotLanguageChanged', {
      detail: { language: newLang }
    }));
  };

  // NEW FUNCTION: Update header text based on language
  function updateHeaderText(lang) {
    const headerTitles = {
      en: {
        title: "Mentivio: Your Friend",
        subtitlePrefix: "Heart Space"
      },
      es: {
        title: "Mentivio: Tu Amigo",
        subtitlePrefix: "Espacio del Corazón"
      },
      vi: {
        title: "Mentivio: Người Bạn Của Bạn",
        subtitlePrefix: "Không Gian Trái Tim"
      },
      zh: {
        title: "Mentivio: 您的朋友",
        subtitlePrefix: "心灵空间"
      }
    };
    
    const header = headerTitles[lang] || headerTitles.en;
    
    // Update title
    const titleElement = document.querySelector('.mentivio-title');
    if (titleElement) {
      titleElement.textContent = header.title;
    }
    
    // Update day display will be handled by updateDay() function
    // We just need to trigger updateDay to refresh with new language
    if (typeof updateDay === 'function') {
      updateDay();
    }
  }

  function setupLanguageSynchronization() {
    // Listen to global language change events
    document.addEventListener('languageChanged', function(e) {
      const newLang = e.detail.language;
      console.log('Chatbot received languageChanged event:', newLang);
      if (updateChatbotLanguage) {
        updateChatbotLanguage(newLang);
      }
    });
    
    document.addEventListener('langChanged', function(e) {
      const newLang = e.detail.lang;
      console.log('Chatbot received langChanged event:', newLang);
      if (updateChatbotLanguage) {
        updateChatbotLanguage(newLang);
      }
    });
    
    // Also listen for custom events from navbar
    window.addEventListener('mentivioLangChange', function(e) {
      const newLang = e.detail?.language || e.detail?.lang;
      if (newLang && updateChatbotLanguage) {
        console.log('Chatbot received mentivioLangChange event:', newLang);
        updateChatbotLanguage(newLang);
      }
    });
  }

  function updateSafetyNotice(lang) {
    const safetyNotices = {
      en: {
        line1: "Safe space • High EQ • Always here for you",
        line2: "Need urgent support?"
      },
      es: {
        line1: "Espacio seguro • Alta IE • Siempre aquí para ti",
        line2: "¿Necesitas apoyo urgente?"
      },
      vi: {
        line1: "Không gian an toàn • Trí tuệ cảm xúc cao • Luôn ở đây vì bạn",
        line2: "Cần hỗ trợ khẩn cấp?"
      },
      zh: {
        line1: "安全空间 • 高情商 • 永远在这里陪伴你",
        line2: "需要紧急支持？"
      }
    };
    
    const notice = safetyNotices[lang] || safetyNotices.en;
    const safetyNoticeEl = document.querySelector('.safety-notice');
    if (safetyNoticeEl) {
      safetyNoticeEl.innerHTML = `
        <i class="fas fa-heart" style="color: #ec4899;"></i>
        ${notice.line1}
        <span style="color: #ef4444; cursor: pointer; margin-left: 8px;" onclick="window.showEnhancedCrisisResources('${lang}')">${notice.line2}</span>
      `;
    }
  }

  function updateWelcomeMessage(lang) {
    const welcomeMessages = {
      en: "Hello. I'm Mentivio, your mental health companion. I'm here to listen deeply, understand without judgment, and help you find light even on dark days. Your feelings are welcome here, all of them.",
      es: "Hola. Soy Mentivio, tu compañero de salud mental. Estoy aquí para escuchar profundamente, entender sin juzgar y ayudarte a encontrar luz incluso en los días oscuros. Todos tus sentimientos son bienvenidos aquí.",
      vi: "Xin chào. Tôi là Mentivio, người bạn đồng hành sức khỏe tinh thần của bạn. Tôi ở đây để lắng nghe sâu sắc, thấu hiểu không phán xét và giúp bạn tìm thấy ánh sáng ngay cả trong những ngày tăm tối. Tất cả cảm xúc của bạn đều được chào đón ở đây.",
      zh: "你好。我是Mentivio，您的心理健康伴侣。我在这里深度倾听，不加评判地理解，并帮助您在黑暗的日子里找到光明。您所有的感受在这里都受到欢迎。"
    };
    
    const welcomeElement = document.querySelector('.welcome-message .message-text');
    if (welcomeElement) {
      welcomeElement.innerHTML = `<div style="font-size: 20px; margin-bottom: 8px;">🌱</div>${welcomeMessages[lang] || welcomeMessages.en}`;
    }
  }
  
  function updateQuickEmotions(lang) {
    const emotionTranslations = {
      en: {
        overwhelmed: "😰 Heavy Heart",
        anxious: "😟 Anxious Thoughts",
        sad: "😔 Feeling Low",
        lonely: "🌌 Feeling Alone",
        hesitant: "🤔 Hesitant",
        confused: "😕 Confused",
        ashamed: "😳 Feeling Ashamed",
        jealous: "😠 Jealous Feelings",
        gender: "🌈 Gender Questions",
        lgbtq: "🏳️‍🌈 LGBTQ+",
        study: "📚 Study Stress",
        love: "💔 Love & Heartbreak",
        curious: "🤔 Seeking Meaning",
        hopeful: "✨ Looking for Hope",
        lost: "🧭 Feeling Lost",
        transition: "🔄 In Transition",
        future: "🔮 Future Anxiety",
        reset: "🔄 Need Reset"
      },
      es: {
        overwhelmed: "😰 Corazón Pesado",
        anxious: "😟 Pensamientos Ansiosos",
        sad: "😔 Sintiéndome Triste",
        lonely: "🌌 Sintiéndome Solo",
        hesitant: "🤔 Vacilante",
        confused: "😕 Confundido",
        ashamed: "😳 Sintiendo Vergüenza",
        jealous: "😠 Sentimientos Celosos",
        gender: "🌈 Preguntas de Género",
        lgbtq: "🏳️‍🌈 LGBTQ+",
        study: "📚 Estrés de Estudio",
        love: "💔 Amor y Desamor",
        curious: "🤔 Buscando Sentido",
        hopeful: "✨ Buscando Esperanza",
        lost: "🧭 Sintiéndome Perdido",
        transition: "🔄 En Transición",
        future: "🔮 Ansiedad Futuro",
        reset: "🔄 Necesito Reinicio"
      },
      vi: {
        overwhelmed: "😰 Trái Tim Nặng Trĩu",
        anxious: "😟 Lo Âu",
        sad: "😔 Buồn Bã",
        lonely: "🌌 Cô Đơn",
        hesitant: "🤔 Do Dự",
        confused: "😕 Bối Rối",
        ashamed: "😳 Cảm Thấy Xấu Hổ",
        jealous: "😠 Cảm Giác Ghen Tị",
        gender: "🌈 Câu Hỏi về Giới Tính",
        lgbtq: "🏳️‍🌈 LGBTQ+",
        study: "📚 Căng Thẳng Học Tập",
        love: "💔 Tình Yêu & Tan Vỡ",
        curious: "🤔 Tìm Kiếm Ý Nghĩa",
        hopeful: "✨ Tìm Hy Vọng",
        lost: "🧭 Lạc Lối",
        transition: "🔄 Giai Đoạn Chuyển Tiếp",
        future: "🔮 Lo Âu Tương Lai",
        reset: "🔄 Cần Khởi Động Lại"
      },
      zh: {
        overwhelmed: "😰 沉重的心",
        anxious: "😟 焦虑思绪",
        sad: "😔 情绪低落",
        lonely: "🌌 感到孤独",
        hesitant: "🤔 犹豫",
        confused: "😕 困惑",
        ashamed: "😳 感到羞愧",
        jealous: "😠 嫉妒感",
        gender: "🌈 性别问题",
        lgbtq: "🏳️‍🌈 LGBTQ+",
        study: "📚 学习压力",
        love: "💔 爱与心碎",
        curious: "🤔 寻求意义",
        hopeful: "✨ 寻找希望",
        lost: "🧭 感到迷茫",
        transition: "🔄 过渡期",
        future: "🔮 未来焦虑",
        reset: "🔄 需要重启"
      }
    };
    
    const emotions = document.querySelectorAll('.quick-emotion');
    emotions.forEach(button => {
      const emotion = button.dataset.emotion;
      const translations = emotionTranslations[lang] || emotionTranslations.en;
      if (translations[emotion]) {
        button.textContent = translations[emotion];
      }
    });
  }
  
  function updateInputPlaceholder(lang) {
    const placeholders = {
      en: "Share what's in your heart... (All feelings welcome)",
      es: "Comparte lo que hay en tu corazón... (Todas las emociones son bienvenidas)",
      vi: "Chia sẻ những gì trong trái tim bạn... (Tất cả cảm xúc đều được chào đón)",
      zh: "分享你心中的感受... (欢迎所有情绪)"
    };
    
    if (mentivioInput) {
      mentivioInput.placeholder = placeholders[lang] || placeholders.en;
    }
  }

  // ================================
  // CHATBOT UI (ENHANCED WITH HIGH EQ & MULTILINGUAL)
  // ================================
  const mentivioHTML = `
  <div id="mentivio-root">
    <!-- Floating avatar -->
    <div id="mentivioAvatar">
      <span id="avatarEmoji">💭</span>
    </div>

    <!-- Main chat window -->
    <div id="mentivioWindow">
      <!-- Header -->
      <header class="mentivio-header">
        <div class="header-content">
          <div id="activeEmotion" class="active-emotion"></div>
          <div class="header-text">
            <strong class="mentivio-title">Mentivio: Your Friend</strong>
            <small id="currentDay" class="mentivio-subtitle">Heart Space • Mon • 08:33 PM</small>
          </div>
        </div>
        <div class="header-right">
          <div id="languageSelector" class="language-selector">
            <span id="currentLanguage"></span>
            <div class="language-dropdown">
              <button class="lang-option" data-lang="en">🌐 English</button>
              <button class="lang-option" data-lang="es">🌐 Español</button>
              <button class="lang-option" data-lang="vi">🌐 Tiếng Việt</button>
              <button class="lang-option" data-lang="zh">🌐 中文</button>
            </div>
          </div>
          <button id="closeMentivio" class="close-btn" aria-label="Close chat">×</button>
        </div>
      </header>

      <!-- Connection strength indicator -->
      <div id="connectionBar" class="connection-bar"></div>

      <!-- Messages container -->
      <div id="mentivioMessages" class="messages-container">
        <div class="message bot welcome-message">
          <div class="message-content">
            <div class="message-text">
              <div style="font-size: 20px; margin-bottom: 8px;">🌱</div>
              Hello. I'm Mentivio, your mental health companion. I'm here to listen deeply, understand without judgment, and help you find light even on dark days. Your feelings are welcome here, all of them.
            </div>
            <div class="message-time">just now</div>
          </div>
        </div>
      </div>

      <!-- Typing indicator -->
      <div id="typingIndicator" class="typing-indicator">
        <div class="typing-content">
          <div class="typing-dots">
            <span></span><span></span><span></span>
          </div>
          <small id="typingStatus" class="typing-text">Mentivio is thinking...</small>
        </div>
      </div>

      <!-- Input area -->
      <div class="input-container">
        <div class="input-wrapper">
          <textarea id="mentivioInput" placeholder="Share what's in your heart... (All feelings welcome)" class="message-input" rows="1"></textarea>
          <button id="sendBtn" class="send-btn" aria-label="Send message">➤</button>
        </div>
        
        <!-- Enhanced quick emotional check-in -->
        <div id="quickEmotions" class="quick-emotions">
          <button class="quick-emotion" data-emotion="overwhelmed">😰 Heavy Heart</button>
          <button class="quick-emotion" data-emotion="anxious">😟 Anxious Thoughts</button>
          <button class="quick-emotion" data-emotion="sad">😔 Feeling Low</button>
          <button class="quick-emotion" data-emotion="lonely">🌌 Feeling Alone</button>
          <button class="quick-emotion" data-emotion="hesitant">🤔 Hesitant</button>
          <button class="quick-emotion" data-emotion="confused">😕 Confused</button>
          <button class="quick-emotion" data-emotion="study">📚 Study Stress</button>
          <button class="quick-emotion" data-emotion="love">💔 Love & Heartbreak</button>
          <button class="quick-emotion" data-emotion="gender">🌈 Gender Questions</button>
          <button class="quick-emotion" data-emotion="lgbtq">🏳️‍🌈 LGBTQ+</button>
          <button class="quick-emotion" data-emotion="curious">🤔 Seeking Meaning</button>
          <button class="quick-emotion" data-emotion="hopeful">✨ Looking for Hope</button>
          <button class="quick-emotion" data-emotion="lost">🧭 Feeling Lost</button>
          <button class="quick-emotion" data-emotion="transition">🔄 In Transition</button>
          <button class="quick-emotion" data-emotion="future">🔮 Future Anxiety</button>
          <button class="quick-emotion" data-emotion="reset">🔄 Need Reset</button>
        </div>
        
        <!-- Enhanced safety notice -->
        <div class="safety-notice" style="font-size: 11px; color: #64748b; text-align: center; margin-top: 8px; padding: 8px; background: #f8fafc; border-radius: 8px; display: flex; align-items: center; justify-content: center; gap: 6px;">
          <i class="fas fa-heart" style="color: #ec4899;"></i>
          Safe space • High EQ • Always here for you
          <span style="color: #ef4444; cursor: pointer; margin-left: 8px;" onclick="window.showEnhancedCrisisResources()">Need urgent support?</span>
        </div>
      </div>
    </div>
  </div>`;

  document.body.insertAdjacentHTML('beforeend', mentivioHTML);

  // ================================
  // ADD CSS
  // ================================
  const style = document.createElement('style');
  style.textContent = `
    /* Base avatar styles */
    #mentivioAvatar {
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, #8b5cf6, #ec4899);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 28px;
      cursor: pointer;
      box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
      z-index: 10000;
      transition: all 0.3s ease;
      border: 3px solid white;
    }
    
    #mentivioAvatar:hover {
      transform: scale(1.1);
      box-shadow: 0 6px 30px rgba(139, 92, 246, 0.6);
    }
    
    /* DESKTOP VIEW - Slightly larger */
    #mentivioWindow {
      position: fixed;
      display: none;
      flex-direction: column;
      background: white;
      border-radius: 16px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
      z-index: 9999;
      overflow: hidden;
      width: 500px;
      height: 700px;
      bottom: 100px;
      right: 20px;
      transition: opacity 0.3s ease, transform 0.3s ease;
      opacity: 0;
      transform: translateY(20px);
    }
    
    #mentivioWindow.open {
      display: flex;
      opacity: 1;
      transform: translateY(0);
    }
    
    /* MOBILE VIEW - Responsive and smaller */
    @media (max-width: 768px) {
      #mentivioWindow {
        width: 92%;
        height: 120vh;
        max-height: 700px;
        bottom: auto;
        right: auto;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) scale(0.95);
        border-radius: 16px;
      }
      
      #mentivioWindow.open {
        transform: translate(-50%, -50%) scale(1);
      }
      
      /* Smaller avatar on mobile */
      #mentivioAvatar {
        width: 50px;
        height: 50px;
        font-size: 24px;
        bottom: 15px;
        right: 15px;
      }
      
      .mentivio-header {
        padding: 16px !important;
      }
      
      .mentivio-title {
        font-size: 16px !important;
      }
      
      .mentivio-subtitle {
        font-size: 11px !important;
      }
      
      .header-right {
        flex-direction: column;
        gap: 5px;
      }
    }
    
    /* SMALL PHONES */
    @media (max-width: 375px) and (max-height: 700px) {
      #mentivioWindow {
        width: 94%;
        height: 100vh;
        max-height: 550px;
        border-radius: 14px;
      }
      
      #mentivioAvatar {
        width: 45px;
        height: 45px;
        font-size: 22px;
        bottom: 10px;
        right: 10px;
      }
      
      .message-input {
        font-size: 14px !important;
        padding: 10px 40px 10px 10px !important;
      }
      
      .send-btn {
        width: 30px !important;
        height: 30px !important;
        font-size: 12px !important;
      }
      
      .quick-emotion {
        font-size: 11px !important;
        padding: 6px 8px !important;
      }
    }
    
    /* VERY SMALL PHONES */
    @media (max-width: 320px) {
      #mentivioWindow {
        width: 96%;
        height: 68vh;
        max-height: 420px;
      }
      
      .quick-emotions {
        gap: 4px !important;
      }
      
      .quick-emotion {
        font-size: 10px !important;
        padding: 5px 6px !important;
      }
    }
    
    /* Header styles */
    .mentivio-header {
      padding: 18px;
      background: linear-gradient(135deg, #8b5cf6, #ec4899);
      color: white;
      position: relative;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .header-content {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    .header-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    /* Language Selector Styles */
    .language-selector {
      position: relative;
      cursor: pointer;
    }
    
    #currentLanguage {
      background: rgba(255, 255, 255, 0.2);
      padding: 4px 8px;
      border-radius: 12px;
      font-size: 12px;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: background 0.3s;
    }
    
    #currentLanguage:hover {
      background: rgba(255, 255, 255, 0.3);
    }
    
    .language-dropdown {
      position: absolute;
      top: 100%;
      right: 0;
      background: white;
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
      display: none;
      flex-direction: column;
      min-width: 120px;
      z-index: 1000;
      overflow: hidden;
    }
    
    .language-selector:hover .language-dropdown {
      display: flex;
    }
    
    .lang-option {
      padding: 10px 12px;
      border: none;
      background: white;
      color: #475569;
      font-size: 13px;
      text-align: left;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: background 0.2s;
    }
    
    .lang-option:hover {
      background: #f1f5f9;
    }
    
    .lang-option.active {
      background: #f0f9ff;
      color: #0369a1;
    }
    
    .active-emotion {
      width: 10px;
      height: 10px;
      background: #4ade80;
      border-radius: 50%;
      animation: pulse 2s infinite;
    }
    
    .header-text {
      flex: 1;
    }
    
    .mentivio-title {
      font-size: 17px;
      display: block;
      font-weight: 600;
    }
    
    .mentivio-subtitle {
      font-size: 12px;
      opacity: 0.9;
    }
    
    .close-btn {
      background: rgba(255, 255, 255, 0.2);
      border: none;
      color: white;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      font-size: 18px;
      cursor: pointer;
      transition: background 0.3s;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0;
      line-height: 1;
    }
    
    .close-btn:hover {
      background: rgba(255, 255, 255, 0.3);
    }
    
    /* Connection Bar */
    .connection-bar {
      height: 3px;
      background: linear-gradient(90deg, #8b5cf6 0%, #e2e8f0 100%);
      transition: all 1s ease;
    }
    
    /* Messages Container */
    .messages-container {
      flex: 1;
      padding: 15px;
      overflow-y: auto;
      background: #f8fafc;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    
    /* Message Styles */
    .message {
      max-width: 85%;
      animation: fadeIn 0.3s ease-out;
    }
    
    .message.bot {
      align-self: flex-start;
    }
    
    .message.user {
      align-self: flex-end;
    }
    
    .message-content {
      padding: 10px 14px;
      border-radius: 16px;
      position: relative;
      word-wrap: break-word;
    }
    
    .message.bot .message-content {
      background: white;
      border: 1px solid #e2e8f0;
      border-bottom-left-radius: 6px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    
    .message.user .message-content {
      background: linear-gradient(135deg, #8b5cf6, #ec4899);
      color: white;
      border-bottom-right-radius: 6px;
      box-shadow: 0 2px 8px rgba(139, 92, 246, 0.15);
    }
    
    .message-text {
      font-size: 14px;
      line-height: 1.4;
    }
    
    .message-time {
      font-size: 10px;
      opacity: 0.6;
      margin-top: 4px;
      text-align: right;
    }
    
    /* Welcome message enhancement */
    .welcome-message .message-content {
      background: linear-gradient(135deg, #f0f9ff, #fef2f2);
      border-left: 4px solid #8b5cf6;
    }
    
    /* Typing Indicator */
    .typing-indicator {
      display: none;
      padding: 8px 15px;
      background: #f8fafc;
    }
    
    .typing-content {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .typing-dots {
      display: flex;
      gap: 4px;
    }
    
    .typing-dots span {
      width: 6px;
      height: 6px;
      background: #8b5cf6;
      border-radius: 50%;
      animation: typingDots 1.4s infinite;
    }
    
    .typing-dots span:nth-child(2) {
      animation-delay: 0.2s;
    }
    
    .typing-dots span:nth-child(3) {
      animation-delay: 0.4s;
    }
    
    .typing-text {
      color: #64748b;
      font-size: 12px;
      font-style: italic;
    }
    
    /* Input Area */
    .input-container {
      padding: 15px;
      background: white;
      border-top: 1px solid #e2e8f0;
    }
    
    .input-wrapper {
      position: relative;
      margin-bottom: 10px;
    }
    
    .message-input {
      width: 100%;
      padding: 14px 45px 14px 12px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      resize: none;
      min-height: 24px;
      max-height: 100px;
      font-family: inherit;
      font-size: 14px;
      background: #f8fafc;
      box-sizing: border-box;
      line-height: 1.4;
    }
    
    .message-input:focus {
      outline: none;
      border-color: #8b5cf6;
      box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
    }
    
    .send-btn {
      position: absolute;
      right: 8px;
      bottom: 8px;
      background: #8b5cf6;
      color: white;
      border: none;
      width: 32px;
      height: 32px;
      border-radius: 8px;
      cursor: pointer;
      transition: background 0.3s;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      padding: 0;
    }
    
    .send-btn:hover {
      background: #7c3aed;
    }
    
    /* Enhanced Quick Emotions */
    .quick-emotions {
      display: flex;
      justify-content: flex-start;
      gap: 6px;
      overflow-x: auto;
      padding: 8px 2px 12px 2px;
      -webkit-overflow-scrolling: touch;
      margin-bottom: 8px;
      scrollbar-width: thin;
      scrollbar-color: #cbd5e1 #f1f5f9;
    }
    
    .quick-emotions::-webkit-scrollbar {
      height: 6px;
    }
    
    .quick-emotions::-webkit-scrollbar-track {
      background: #f1f5f9;
      border-radius: 3px;
    }
    
    .quick-emotions::-webkit-scrollbar-thumb {
      background: #cbd5e1;
      border-radius: 3px;
      transition: background 0.3s;
    }
    
    .quick-emotions::-webkit-scrollbar-thumb:hover {
      background: #94a3b8;
    }
    
    @media (hover: hover) and (pointer: fine) {
      .quick-emotions {
        scrollbar-width: thin;
        overflow-x: auto;
        padding-bottom: 12px;
      }
      
      .quick-emotions::-webkit-scrollbar {
        display: block;
        height: 6px;
      }
    }
    
    @media (hover: none) and (pointer: coarse) {
      .quick-emotions::-webkit-scrollbar {
        display: none;
      }
      
      .quick-emotions {
        -ms-overflow-style: none;
        scrollbar-width: none;
      }
      
      .quick-emotions::-webkit-scrollbar {
        display: none;
      }
    }
    
    .quick-emotion {
      padding: 8px 12px;
      background: linear-gradient(135deg, #f8fafc, #f0f9ff);
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s;
      flex-shrink: 0;
      white-space: nowrap;
      color: #475569;
      min-width: max-content;
    }
    
    .quick-emotion:hover {
      background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
      transform: translateY(-1px);
      border-color: #cbd5e1;
    }
    
    /* Animations */
    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    @keyframes pulse {
      0%, 100% {
        opacity: 1;
      }
      50% {
        opacity: 0.5;
      }
    }
    
    @keyframes typingDots {
      0%, 60%, 100% {
        transform: translateY(0);
      }
      30% {
        transform: translateY(-3px);
      }
    }
    
    /* Scrollbar Styling for messages */
    .messages-container::-webkit-scrollbar {
      width: 6px;
    }
    
    .messages-container::-webkit-scrollbar-track {
      background: #f1f5f9;
    }
    
    .messages-container::-webkit-scrollbar-thumb {
      background: #cbd5e1;
      border-radius: 3px;
    }
    
    .messages-container::-webkit-scrollbar-thumb:hover {
      background: #94a3b8;
    }
    
    /* Prevent body scroll when chat is open on mobile */
    body.mentivio-open {
      overflow: hidden !important;
    }
    
    /* Mobile touch optimizations */
    @media (hover: none) and (pointer: coarse) {
      .quick-emotion:active,
      .send-btn:active,
      #mentivioAvatar:active {
        transform: scale(0.95);
      }
      
      .quick-emotions {
        -webkit-overflow-scrolling: touch;
        scroll-snap-type: x mandatory;
      }
      
      .quick-emotion {
        scroll-snap-align: start;
      }
    }
    
    /* High EQ specific enhancements */
    .safety-notice {
      cursor: pointer;
      margin-top: 8px;
    }
    
    .safety-notice span:hover {
      text-decoration: underline;
    }
    
    /* Desktop-specific adjustments */
    @media (min-width: 769px) {
      .quick-emotions {
        max-width: 100%;
        overflow-x: auto;
        scrollbar-width: thin;
      }
      
      .quick-emotion {
        flex: 0 0 auto;
      }
      
      .input-container {
        padding: 18px 15px 15px 15px;
      }
      
      .message-input {
        font-size: 15px;
        min-height: 26px;
      }
      
      .send-btn {
        bottom: 10px;
      }
    }
    
    /* Larger desktop screens */
    @media (min-width: 1200px) {
      #mentivioWindow {
        width: 550px;
        height: 750px;
      }
      
      .message-text {
        font-size: 15px;
      }
    }
  `;
  
  document.head.appendChild(style);

  // ================================
  // INITIALIZATION
  // ================================
  ai = new HighEQMentivio();
  let isTyping = false;
  let lastInteractionTime = Date.now();

  // ================================
  // UI ELEMENTS
  // ================================
  const avatar = document.getElementById('mentivioAvatar');
  mentivioWindow = document.getElementById('mentivioWindow');
  const messages = document.getElementById('mentivioMessages');
  mentivioInput = document.getElementById('mentivioInput');
  const sendBtn = document.getElementById('sendBtn');
  const closeBtn = document.getElementById('closeMentivio');
  const typingIndicator = document.getElementById('typingIndicator');
  const connectionBar = document.getElementById('connectionBar');
  const activeEmotion = document.getElementById('activeEmotion');
  const currentDay = document.getElementById('currentDay');

  // UPDATED: Update current day with language support
  function updateDay() {
    if (!currentDay) return;
    
    const now = new Date();
    const lang = CONFIG ? CONFIG.language : 'en';
    
    // Language-specific day names
    const dayNames = {
      en: {
        short: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        long: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
      },
      es: {
        short: ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'],
        long: ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
      },
      vi: {
        short: ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'],
        long: ['Chủ Nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']
      },
      zh: {
        short: ['日', '一', '二', '三', '四', '五', '六'],
        long: ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
      }
    };
    
    // Language-specific time formats
    const timeFormats = {
      en: { hour12: true, hour: '2-digit', minute: '2-digit' },
      es: { hour12: true, hour: '2-digit', minute: '2-digit' },
      vi: { hour12: false, hour: '2-digit', minute: '2-digit' },
      zh: { hour12: false, hour: '2-digit', minute: '2-digit' }
    };
    
    // Get day and time
    const dayOfWeek = now.getDay();
    const dayNameSet = dayNames[lang] || dayNames.en;
    const dayName = dayNameSet.short[dayOfWeek];
    
    const timeFormat = timeFormats[lang] || timeFormats.en;
    const time = now.toLocaleTimeString([], timeFormat);
    
    // Language-specific prefix
    const prefixes = {
      en: "Heart Space",
      es: "Espacio del Corazón",
      vi: "Không Gian Trái Tim",
      zh: "心灵空间"
    };
    
    const prefix = prefixes[lang] || prefixes.en;
    currentDay.textContent = `${prefix} • ${dayName} • ${time}`;
  }

  // ================================
  // LANGUAGE SELECTOR
  // ================================
  function initLanguageSelector() {
    const currentLangEl = document.getElementById('currentLanguage');
    const langOptions = document.querySelectorAll('.lang-option');
    
    // Language display mapping
    const languageDisplays = {
      en: "🌐 EN",
      es: "🌐 ES",
      vi: "🌐 VI",
      zh: "🌐 ZH"
    };
    
    // Update language display
    function updateLanguageDisplay(lang) {
      currentLangEl.innerHTML = languageDisplays[lang] || "🌐 EN";
      
      // Update active class on language options
      langOptions.forEach(option => {
        if (option.dataset.lang === lang) {
          option.classList.add('active');
        } else {
          option.classList.remove('active');
        }
      });
      
      // Update CONFIG language
      CONFIG.language = lang;
      if (ai) {
        ai.language = lang;
      }
      localStorage.setItem('mentivio_language', lang);
      
      // Update UI elements
      updateWelcomeMessage(lang);
      updateQuickEmotions(lang);
      updateInputPlaceholder(lang);
      updateSafetyNotice(lang);
      updateHeaderText(lang);
    }
    
    // Set initial language
    updateLanguageDisplay(CONFIG.language);
    
    // Handle language selection
    langOptions.forEach(option => {
      option.addEventListener('click', function() {
        const newLang = this.dataset.lang;
        updateLanguageDisplay(newLang);
        
        // Dispatch event for synchronization
        document.dispatchEvent(new CustomEvent('mentivioLangChange', {
          detail: { language: newLang }
        }));
      });
    });
  }

  // ================================
  // WINDOW MANAGEMENT
  // ================================
  function showWindow() {
    if (isWindowOpen) return;
    
    isWindowOpen = true;
    
    if (window.innerWidth <= 768) {
      document.body.classList.add('mentivio-open');
    }
    
    mentivioWindow.classList.add('open');
    
    setTimeout(() => {
      if (mentivioInput) {
        mentivioInput.focus();
      }
    }, 100);
    
    updateAvatarEmoji('listening');
  }
  
  function hideWindow() {
    if (!isWindowOpen) return;
    
    isWindowOpen = false;
    mentivioWindow.classList.remove('open');
    document.body.classList.remove('mentivio-open');
    updateAvatarEmoji('calm');
  }

  avatar.addEventListener('click', showWindow);
  closeBtn.addEventListener('click', hideWindow);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isWindowOpen) {
      hideWindow();
    }
  });

  // ================================
  // ENHANCED MESSAGE HANDLING WITH HIGH EQ
  // ================================
  async function sendMessage() {
      const text = mentivioInput.value.trim();
      if (!text || isTyping) return;

      // Check for dangerous topics FIRST
      if (detectDangerousTopics(text)) {
          addMessage("I'm here to support you with care and compassion. Let's focus on your wellbeing and finding constructive ways to navigate these feelings.", 'bot');
          
          // Offer alternative support
          setTimeout(() => {
              addMessage("If you're experiencing difficult thoughts or conflicts, would you like to explore healthier coping strategies together?", 'bot');
          }, 1000);
          
          mentivioInput.value = '';
          return;
      }
    

    // Enhanced frontend filter with high EQ approach
    const crisisPatterns = [
        /kill.*myself/i,
        /suicide.*now/i,
        /end.*my.*life.*now/i,
        /self.*harm.*now/i,
        /emergency.*help/i,
        /going.*to.*end.*it/i,
        /plan.*to.*die/i,
        /suicide.*plan/i,
        /how.*to.*kill.*myself/i,
        /best.*way.*to.*die/i,
        /cutting.*myself/i,
        /overdose.*on/i,
        /take.*all.*pills/i,
        /hanging.*myself/i,
        /jump.*off/i,
        /gun.*to.*head/i,
        /shoot.*myself/i
    ];
    
    const suicidalThoughtPatterns = [
      /want.*to.*die/i,
      /hopeless/i,
      /worthless/i,
      /burden/i,
      /no.*point/i,
      /can't.*go.*on/i
    ];
    
    if (crisisPatterns.some(pattern => pattern.test(text))) {
      // Immediate crisis response
      addMessage("I hear how much pain you're in, and my heart is with you right now. Let me share some immediate support resources.", 'bot');
      window.showEnhancedCrisisResources(CONFIG.language);
      mentivioInput.value = '';
      return;
    }
    
    if (suicidalThoughtPatterns.some(pattern => pattern.test(text))) {
      // Suicidal thoughts - high EQ response
      addMessage("Thank you for trusting me with these heavy thoughts. I want you to know: your feelings make sense and your pain is real. Let's talk about finding support.", 'bot');
      setTimeout(() => {
        window.showEnhancedCrisisResources(CONFIG.language);
      }, 1000);
      mentivioInput.value = '';
      return;
    }

    // Add user message
    const emotion = detectEmotion(text);
    addMessage(text, 'user');
    if (ai) {
      ai.updateLocalState(text, emotion);
    }
    mentivioInput.value = '';
    resetInputHeight();
    
    updateAvatarEmoji('thinking');
    showTyping();
    
    try {
      // Call enhanced backend API
      const context = ai ? ai.getConversationContext() : [];
      const response = await callBackendAPI(text, context, emotion);
      
      hideTyping();
      
      if (response.is_safe) {
        // Add gentle emojis to bot responses occasionally
        let botResponse = response.response;
        if (Math.random() < 0.3 && !botResponse.includes('💭') && !botResponse.includes('🤍')) {
          const gentleEmojis = [' 💭', ' 🤍', ' 🌱', ' ✨'];
          botResponse += gentleEmojis[Math.floor(Math.random() * gentleEmojis.length)];
        }
        
        addMessage(botResponse, 'bot');
        if (ai) {
          ai.updateLocalState(response.response, 'bot');
        }
        
        updateEmotionalIndicator(response.emotion || emotion);
        updateConnectionStrength(ai ? ai.conversationState.trustLevel : 0);
        updateAvatarEmoji('empathetic');
      } else {
        // Handle unsafe response with high EQ
        addMessage("I'm here to listen deeply to whatever's in your heart. Let's focus on finding light and meaning together.", 'bot');
      }
      
      scrollToBottom();
      lastInteractionTime = Date.now();
      
    } catch (error) {
      console.error('Error:', error);
      hideTyping();
      addMessage("I'm here with you, present and listening. Sometimes technology falters, but our connection doesn't have to. What's one small thing you want to share?", 'bot');
      updateAvatarEmoji('calm');
    }
  }

  // Enhanced quick emotions with full multilingual support
  document.querySelectorAll('.quick-emotion').forEach(btn => {
    btn.addEventListener('click', function() {
      const emotion = this.dataset.emotion;
      
      // Language-specific prompts for all emotions including new ones
      const prompts = {
        en: {
          overwhelmed: "My heart feels so heavy right now. Everything feels like too much and I'm not sure how to keep going.",
          anxious: "My mind won't stop racing with worries. I feel so anxious about everything that could go wrong.",
          sad: "I'm feeling really low and sad today. The sadness feels heavy and I don't know how to lift it.",
          lonely: "I feel so alone, even when people are around. The loneliness is profound and isolating.",
          hesitant: "I feel so hesitant and unsure about what to do. Every choice feels overwhelming and I'm scared of making the wrong decision.",
          confused: "I'm feeling really confused about things in my life. I don't understand what's happening or what I should do next.",
          study: "I'm struggling with my studies. The pressure is overwhelming and I don't know how to keep up with everything.",
          love: "My heart is hurting from a relationship. I don't know how to move forward or heal from this pain.",
          gender: "I'm questioning my gender identity and it's confusing and scary. I don't know who to talk to about this.",
          lgbtq: "I'm exploring my sexuality/identity and it feels lonely. I'm not sure how to navigate these feelings or find acceptance.",
          curious: "I'm searching for meaning in all of this. What's the purpose when things feel so hard?",
          hopeful: "I'm trying to find hope. Can you help me see possibilities and light ahead?",
          lost: "I feel completely lost right now. I don't know which direction to take or what my purpose is anymore.",
          transition: "I'm in a major life transition and everything feels uncertain. I don't know who I am or where I'm going.",
          future: "I'm so anxious about the future. All the 'what ifs' are overwhelming me and I can't see a clear path forward.",
          reset: "I need a complete reset in my life. Things aren't working and I don't know how to start over."
        },
        es: {
          overwhelmed: "Mi corazón se siente tan pesado ahora mismo. Todo parece demasiado y no estoy seguro de cómo seguir adelante.",
          anxious: "Mi mente no deja de correr con preocupaciones. Me siento tan ansioso por todo lo que podría salir mal.",
          sad: "Me siento muy deprimido y triste hoy. La tristeza se siente pesada y no sé cómo levantarla.",
          lonely: "Me siento tan solo, incluso cuando hay gente alrededor. La soledad es profunda y aislante.",
          hesitant: "Me siento tan vacilante e inseguro sobre qué hacer. Cada decisión me abruma y tengo miedo de tomar la decisión equivocada.",
          confused: "Me siento realmente confundido sobre las cosas en mi vida. No entiendo qué está pasando o qué debo hacer a continuación.",
          study: "Estoy luchando con mis estudios. La presión es abrumadora y no sé cómo mantener el ritmo con todo.",
          love: "Mi corazón está sufriendo por una relación. No sé cómo seguir adelante o sanar de este dolor.",
          gender: "Estoy cuestionando mi identidad de género y es confuso y aterrador. No sé con quién hablar sobre esto.",
          lgbtq: "Estoy explorando mi sexualidad/identidad y me siento solo. No estoy seguro de cómo manejar estos sentimientos o encontrar aceptación.",
          curious: "Estoy buscando significado en todo esto. ¿Cuál es el propósito cuando las cosas se sienten tan difíciles?",
          hopeful: "Estoy tratando de encontrar esperanza. ¿Puedes ayudarme a ver posibilidades y luz adelante?",
          lost: "Me siento completamente perdido ahora mismo. No sé qué dirección tomar ni cuál es mi propósito ya.",
          transition: "Estoy en una gran transición de vida y todo se siente incierto. No sé quién soy ni a dónde voy.",
          future: "Estoy tan ansioso por el futuro. Todos los 'qué pasaría si' me abruman y no puedo ver un camino claro hacia adelante.",
          reset: "Necesito un reinicio completo en mi vida. Las cosas no están funcionando y no sé cómo empezar de nuevo."
        },
        vi: {
          overwhelmed: "Trái tim tôi cảm thấy thật nặng nề ngay lúc này. Mọi thứ đều cảm thấy quá sức và tôi không chắc làm thế nào để tiếp tục.",
          anxious: "Tâm trí tôi không ngừng chạy đua với những lo lắng. Tôi cảm thấy rất lo lắng về tất cả những gì có thể xảy ra.",
          sad: "Hôm nay tôi cảm thấy rất buồn và chán nản. Nỗi buồn cảm thấy thật nặng nề và tôi không biết làm thế nào để vượt qua.",
          lonely: "Tôi cảm thấy thật cô đơn, ngay cả khi có người xung quanh. Sự cô đơn thật sâu sắc và tách biệt.",
          hesitant: "Tôi cảm thấy rất do dự và không chắc chắn về việc phải làm. Mỗi lựa chọn đều cảm thấy choáng ngợp và tôi sợ mình sẽ đưa ra quyết định sai lầm.",
          confused: "Tôi cảm thấy thực sự bối rối về mọi thứ trong cuộc sống của mình. Tôi không hiểu chuyện gì đang xảy ra hoặc tôi nên làm gì tiếp theo.",
          study: "Tôi đang gặp khó khăn với việc học. Áp lực thật choáng ngợp và tôi không biết làm thế nào để theo kịp mọi thứ.",
          love: "Trái tim tôi đang đau đớn vì một mối quan hệ. Tôi không biết làm thế nào để tiến lên hoặc chữa lành nỗi đau này.",
          gender: "Tôi đang nghi vấn về bản dạng giới của mình và điều đó thật khó hiểu và đáng sợ. Tôi không biết nên nói chuyện với ai về điều này.",
          lgbtq: "Tôi đang khám phá xu hướng tính dục/bản dạng của mình và cảm thấy cô đơn. Tôi không chắc làm thế nào để điều hướng những cảm xúc này hoặc tìm thấy sự chấp nhận.",
          curious: "Tôi đang tìm kiếm ý nghĩa trong tất cả điều này. Mục đích là gì khi mọi thứ cảm thấy thật khó khăn?",
          hopeful: "Tôi đang cố gắng tìm hy vọng. Bạn có thể giúp tôi nhìn thấy khả năng và ánh sáng phía trước không?",
          lost: "Tôi cảm thấy hoàn toàn lạc lối ngay bây giờ. Tôi không biết nên đi theo hướng nào hay mục đích của mình là gì nữa.",
          transition: "Tôi đang ở trong một giai đoạn chuyển tiếp lớn của cuộc đời và mọi thứ đều cảm thấy không chắc chắn. Tôi không biết mình là ai hay mình đang đi đâu.",
          future: "Tôi rất lo lắng về tương lai. Tất cả những 'sẽ ra sao nếu' đang làm tôi choáng ngợp và tôi không thể thấy một con đường rõ ràng phía trước.",
          reset: "Tôi cần một khởi động lại hoàn toàn trong cuộc sống. Mọi thứ không hoạt động và tôi không biết làm thế nào để bắt đầu lại."
        },
        zh: {
          overwhelmed: "我的心现在感觉如此沉重。一切都感觉太多了，我不确定如何继续前进。",
          anxious: "我的思绪不停地被忧虑占据。我对一切可能出错的事情感到非常焦虑。",
          sad: "我今天感到非常低落和悲伤。悲伤感觉很沉重，我不知道如何摆脱它。",
          lonely: "我感到如此孤独，即使周围有人。这种孤独是深刻而孤立的。",
          hesitant: "我感到非常犹豫，不确定该做什么。每一个选择都让我感到不知所措，我害怕做出错误的决定。",
          confused: "我对生活中的事情感到非常困惑。我不明白发生了什么，也不知道下一步该怎么做。",
          study: "我在学习上遇到了困难。压力太大了，我不知道如何跟上一切。",
          love: "我的心因为一段关系而受伤。我不知道如何前进或从这种痛苦中愈合。",
          gender: "我正在质疑我的性别认同，这令人困惑和害怕。我不知道该和谁谈论这个问题。",
          lgbtq: "我正在探索我的性取向/身份，这让我感到孤独。我不确定如何应对这些感受或找到接受。",
          curious: "我正在这一切中寻找意义。当事情感觉如此困难时，目的是什么？",
          hopeful: "我正在努力寻找希望。你能帮我看到前方的可能性和光明吗？",
          lost: "我现在感到完全迷茫。我不知道该走哪个方向，也不知道我的目的是什么了。",
          transition: "我正处于人生重大过渡期，一切都感觉不确定。我不知道我是谁，也不知道我要去哪里。",
          future: "我对未来感到非常焦虑。所有的'如果'让我不知所措，我看不到明确的前进道路。",
          reset: "我需要生活中完全的重启。事情不顺利，我不知道如何重新开始。"
        }
      };
      
      const langPrompts = prompts[CONFIG.language] || prompts.en;
      if (mentivioInput) {
        mentivioInput.value = langPrompts[emotion] || `I'm feeling ${emotion} and could use someone to talk to.`;
        mentivioInput.focus();
      }
    });
  });

  // Input handling
  mentivioInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  mentivioInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 80) + 'px';
  });

  sendBtn.addEventListener('click', sendMessage);

  // ================================
  // UI HELPER FUNCTIONS
  // ================================
  function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const time = new Date().toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    }).replace(' ', '').toLowerCase();
    
    messageDiv.innerHTML = `
      <div class="message-content">
        <div class="message-text">${formatMessage(text)}</div>
        <div class="message-time">${time}</div>
      </div>
    `;
    
    messages.appendChild(messageDiv);
    scrollToBottom();
  }

  function formatMessage(text) {
    return text.replace(/\n/g, '<br>');
  }

  function resetInputHeight() {
    if (mentivioInput) {
      mentivioInput.style.height = 'auto';
    }
  }

  function showTyping() {
    isTyping = true;
    typingIndicator.style.display = 'block';
    
    // Language-specific typing status
    const typingStatuses = {
      en: [
        "Mentivio is thinking deeply...",
        "Listening with my whole heart...",
        "Reflecting on what you've shared...",
        "Holding space for your words..."
      ],
      es: [
        "Mentivio está pensando profundamente...",
        "Escuchando con todo mi corazón...",
        "Reflexionando sobre lo que has compartido...",
        "Guardando espacio para tus palabras..."
      ],
      vi: [
        "Mentivio đang suy nghĩ sâu sắc...",
        "Lắng nghe bằng cả trái tim...",
        "Suy ngẫm về những gì bạn đã chia sẻ...",
        "Giữ không gian cho lời nói của bạn..."
      ],
      zh: [
        "Mentivio正在深入思考...",
        "用全心倾听...",
        "反思您分享的内容...",
        "为您的言语保留空间..."
      ]
    };
    
    const statuses = typingStatuses[CONFIG.language] || typingStatuses.en;
    const statusElement = document.getElementById('typingStatus');
    if (statusElement) {
      statusElement.textContent = statuses[Math.floor(Math.random() * statuses.length)];
    }
  }

  function hideTyping() {
    isTyping = false;
    typingIndicator.style.display = 'none';
  }

  function updateAvatarEmoji(state) {
    const emojis = {
      thinking: '💭',
      listening: '👂',
      empathetic: '🤍',
      calm: '😌',
      warning: '⚠️',
      hopeful: '✨',
      present: '🌱',
      caring: '💗'
    };
    
    const emoji = emojis[state] || '💭';
    const avatarEmojiEl = document.getElementById('avatarEmoji');
    if (avatarEmojiEl) {
      avatarEmojiEl.textContent = emoji;
    }
  }

  function updateEmotionalIndicator(emotion) {
    const colors = {
      happy: '#4ade80',
      sad: '#3b82f6',
      anxious: '#f59e0b',
      angry: '#ef4444',
      overwhelmed: '#8b5cf6',
      neutral: '#94a3b8',
      curious: '#10b981',
      hopeful: '#ec4899',
      grateful: '#f59e0b',
      lonely: '#64748b',
      peaceful: '#06b6d4',
      hesitant: '#a78bfa',
      confused: '#fbbf24',
      ashamed: '#dc2626',
      jealous: '#7c3aed',
      rejected: '#6b7280',
      betrayed: '#be123c'
    };
    
    if (activeEmotion) {
      activeEmotion.style.background = colors[emotion] || colors.neutral;
    }
  }

  function updateConnectionStrength(trust) {
    const percentage = Math.min(100, trust * 15);
    if (connectionBar) {
      connectionBar.style.background = `linear-gradient(90deg, #8b5cf6 ${percentage}%, #e2e8f0 ${percentage}%)`;
    }
  }

  function scrollToBottom() {
    if (messages) {
      messages.scrollTop = messages.scrollHeight;
    }
  }

  // Initial pulse animation
  setTimeout(() => {
    if (!isWindowOpen && avatar) {
      avatar.style.transform = 'scale(1.1)';
      setTimeout(() => {
        avatar.style.transform = '';
      }, 600);
    }
  }, 2000);

  window.addEventListener('resize', updateDay);
  
  // Initialize language selector
  initLanguageSelector();
  
  // Initialize language synchronization
  setupLanguageSynchronization();

  // Initialize header text
  updateHeaderText(CONFIG.language);
  updateDay();

  // ================================
  // GLOBAL FUNCTION EXPORTS
  // ================================
  window.showMentivioWindow = showWindow;
  window.hideMentivioWindow = hideWindow;
  window.isMentivioWindowOpen = () => isWindowOpen;

  // ================================
  // ENHANCED GLOBAL CRISIS FUNCTION (MULTILINGUAL)
  // ================================
  window.showEnhancedCrisisResources = function(lang = null) {
    // Use the global CONFIG if no lang specified
    if (!lang && CONFIG) {
      lang = CONFIG.language;
    }
    
    const crisisResources = {
      en: {
        title: "Your Life Matters",
        subtitle: "You're not alone in this darkness. There are people waiting to help you find your way back to light.",
        immediate: "Immediate Support (24/7)",
        usa: "USA Support",
        international: "International Support",
        usaLineDesc: "USA Support • Suicide & Crisis Lifeline",
        usaLineNote: "Call or text • Completely confidential",
        crisisTextLine: "Crisis Text Line",
        crisisTextLineNote: "Trained crisis counselors via text",
        immediateTips: "Right Now, Try This:",
        tip1: "• Breathe: In for 4, hold for 4, out for 6",
        tip2: "• Ground: Name 5 things you can see",
        tip3: "• Reach: Text one person 'I'm struggling'",
        tip4: "• Wait: Give yourself 24 hours before any decision",
        finalMessage: "\"The world needs what only you can give. Please stay.\"",
        buttonText: "I'll Reach Out • You're Not Alone",
        samaritansUK: "Samaritans (UK)",
        lifelineAUS: "Lifeline (AUS)",
        kidsHelpCA: "Kids Help (CA)",
        needToTalkNZ: "Need to Talk (NZ)",
        closeButton: "Close & Continue Chat"
      },
      es: {
        title: "Tu Vida Importa",
        subtitle: "No estás solo en esta oscuridad. Hay personas esperando para ayudarte a encontrar el camino de regreso a la luz.",
        immediate: "Apoyo Inmediato (24/7)",
        usa: "Apoyo en EE.UU.",
        international: "Apoyo Internacional",
        usaLineDesc: "Apoyo EE.UU. • Línea de Crisis y Suicidio",
        usaLineNote: "Llama o envía mensaje • Totalmente confidencial",
        crisisTextLine: "Línea de Texto de Crisis",
        crisisTextLineNote: "Consejeros de crisis capacitados por mensaje de texto",
        immediateTips: "Ahora Mismo, Intenta Esto:",
        tip1: "• Respira: Inhala por 4, sostén por 4, exhala por 6",
        tip2: "• Conéctate: Nombra 5 cosas que puedes ver",
        tip3: "• Comunícate: Envía un mensaje a una persona 'Estoy luchando'",
        tip4: "• Espera: Date 24 horas antes de cualquier decisión",
        finalMessage: "\"El mundo necesita lo que solo tú puedes dar. Por favor, quédate.\"",
        buttonText: "Me Comunicaré • No Estás Solo",
        samaritansUK: "Samaritanos (Reino Unido)",
        lifelineAUS: "Lifeline (Australia)",
        kidsHelpCA: "Kids Help (Canadá)",
        needToTalkNZ: "Need to Talk (Nueva Zelanda)",
        closeButton: "Cerrar y Continuar Chat"
      },
      vi: {
        title: "Cuộc Sống Của Bạn Quan Trọng",
        subtitle: "Bạn không cô đơn trong bóng tối này. Có những người đang chờ giúp bạn tìm đường trở lại ánh sáng.",
        immediate: "Hỗ Trợ Ngay Lập Tức (24/7)",
        usa: "Hỗ Trợ tại Mỹ",
        international: "Hỗ Trợ Quốc Tế",
        usaLineDesc: "Hỗ Trợ Mỹ • Đường Dây Khủng Hoảng & Tự Tử",
        usaLineNote: "Gọi điện hoặc nhắn tin • Hoàn toàn bí mật",
        crisisTextLine: "Đường Dây Nhắn Tin Khủng Hoảng",
        crisisTextLineNote: "Tư vấn viên khủng hoảng được đào tạo qua tin nhắn",
        immediateTips: "Ngay Bây Giờ, Hãy Thử Điều Này:",
        tip1: "• Thở: Hít vào 4, giữ 4, thở ra 6",
        tip2: "• Cắm rễ: Kể tên 5 thứ bạn có thể nhìn thấy",
        tip3: "• Kết nối: Nhắn tin cho một người 'Tôi đang gặp khó khăn'",
        tip4: "• Chờ đợi: Cho bản thân 24 giờ trước bất kỳ quyết định nào",
        finalMessage: "\"Thế giới cần những gì chỉ bạn có thể cho đi. Hãy ở lại.\"",
        buttonText: "Tôi Sẽ Liên Hệ • Bạn Không Cô Đơn",
        samaritansUK: "Samaritans (Anh)",
        lifelineAUS: "Lifeline (Úc)",
        kidsHelpCA: "Kids Help (Canada)",
        needToTalkNZ: "Need to Talk (New Zealand)",
        closeButton: "Đóng và Tiếp Tục Trò Chuyện"
      },
      zh: {
        title: "你的生命很重要",
        subtitle: "在这黑暗中你并不孤单。有人正在等待帮助你找到回到光明的道路。",
        immediate: "即时支持（24/7）",
        usa: "美国支持",
        international: "国际支持",
        usaLineDesc: "美国支持 • 自杀与危机生命线",
        usaLineNote: "致电或发短信 • 完全保密",
        crisisTextLine: "危机短信热线",
        crisisTextLineNote: "经过培训的危机顾问通过短信服务",
        immediateTips: "现在，尝试这个：",
        tip1: "• 呼吸：吸气 4 秒，屏住 4 秒，呼气 6 秒",
        tip2: "• 接地：说出你能看到的 5 样东西",
        tip3: "• 联系：给一个人发短信'我正在挣扎'",
        tip4: "• 等待：在做任何决定前给自己 24 小时",
        finalMessage: "「世界需要只有你能给予的东西。请留下。」",
        buttonText: "我会寻求帮助 • 你并不孤单",
        samaritansUK: "撒玛利亚会 (英国)",
        lifelineAUS: "生命热线 (澳大利亚)",
        kidsHelpCA: "儿童帮助热线 (加拿大)",
        needToTalkNZ: "倾诉热线 (新西兰)",
        closeButton: "关闭并继续聊天"
      }
    };
    
    const resources = crisisResources[lang] || crisisResources.en;
    
    // Ensure chat window is open
    if (!isWindowOpen && window.showMentivioWindow) {
      window.showMentivioWindow();
    }
    
    // Create modal HTML
    const modalHTML = `
    <div id="mentivio-crisis-modal" class="crisis-modal">
      <div class="crisis-modal-content">
        <div class="crisis-header">
          <h2 class="crisis-title">${resources.title}</h2>
          <p class="crisis-subtitle">${resources.subtitle}</p>
        </div>
        
        <div class="crisis-section immediate-support">
          <h3>🌿 ${resources.immediate}</h3>
          <div class="support-cards">
            <div class="support-card usa">
              <div class="support-number">988</div>
              <div class="support-desc">${resources.usaLineDesc}</div>
              <div class="support-note">${resources.usaLineNote}</div>
            </div>
            
            <div class="support-card textline">
              <div class="support-number">Text HOME to 741741</div>
              <div class="support-desc">${resources.crisisTextLine}</div>
              <div class="support-note">${resources.crisisTextLineNote}</div>
            </div>
          </div>
        </div>
        
        <div class="crisis-section international-support">
          <h3>🌍 ${resources.international}</h3>
          <div class="international-grid">
            <div class="intl-card">
              <div class="intl-number">116 123</div>
              <div class="intl-country">${resources.samaritansUK}</div>
            </div>
            <div class="intl-card">
              <div class="intl-number">13 11 14</div>
              <div class="intl-country">${resources.lifelineAUS}</div>
            </div>
            <div class="intl-card">
              <div class="intl-number">686868</div>
              <div class="intl-country">${resources.kidsHelpCA}</div>
            </div>
            <div class="intl-card">
              <div class="intl-number">1737</div>
              <div class="intl-country">${resources.needToTalkNZ}</div>
            </div>
          </div>
        </div>
        
        <div class="crisis-section immediate-tips">
          <div class="tips-header">
            <span style="font-size: 24px; margin-right: 10px;">💭</span>
            <div>
              <div class="tips-title">${resources.immediateTips}</div>
              <div class="tips-list">
                <div>${resources.tip1}</div>
                <div>${resources.tip2}</div>
                <div>${resources.tip3}</div>
                <div>${resources.tip4}</div>
              </div>
            </div>
          </div>
        </div>
        
        <p class="crisis-message">${resources.finalMessage}</p>
        
        <div class="crisis-actions">
          <button class="crisis-close-btn">
            ${resources.closeButton}
          </button>
        </div>
      </div>
    </div>`;
    
    // Clear existing modal if any
    const existingModal = document.getElementById('mentivio-crisis-modal');
    if (existingModal) {
      existingModal.remove();
    }
    
    // Add to chat window
    if (mentivioWindow) {
      mentivioWindow.insertAdjacentHTML('beforeend', modalHTML);
    }
    
    // Add CSS for the modal
    if (!document.querySelector('#crisis-styles')) {
      const crisisStyles = document.createElement('style');
      crisisStyles.id = 'crisis-styles';
      crisisStyles.textContent = `
        .crisis-modal {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: white;
          z-index: 1000;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          animation: fadeIn 0.3s ease-out;
        }
        
        .crisis-modal-content {
          padding: 20px;
          flex: 1;
          overflow-y: auto;
        }
        
        .crisis-header {
          text-align: center;
          margin-bottom: 25px;
          padding-bottom: 20px;
          border-bottom: 2px solid #f0f9ff;
        }
        
        .crisis-title {
          color: #ef4444;
          margin: 0 0 10px 0;
          font-size: 20px;
          font-weight: 600;
        }
        
        .crisis-subtitle {
          color: #4b5563;
          margin: 0;
          font-size: 14px;
          line-height: 1.5;
          max-width: 90%;
          margin: 0 auto;
        }
        
        .crisis-section {
          margin-bottom: 20px;
          padding: 15px;
          border-radius: 12px;
          background: #f8fafc;
        }
        
        .crisis-section h3 {
          margin: 0 0 15px 0;
          font-size: 16px;
          color: #374151;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .support-cards {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        
        .support-card {
          background: white;
          padding: 15px;
          border-radius: 10px;
          border-left: 4px solid;
        }
        
        .support-card.usa {
          border-left-color: #dc2626;
        }
        
        .support-card.textline {
          border-left-color: #0369a1;
        }
        
        .support-number {
          font-size: 24px;
          font-weight: 800;
          margin-bottom: 8px;
        }
        
        .support-card.usa .support-number {
          color: #dc2626;
        }
        
        .support-card.textline .support-number {
          font-size: 18px;
          color: #0369a1;
        }
        
        .support-desc {
          color: #374151;
          font-size: 13px;
          margin-bottom: 4px;
        }
        
        .support-note {
          color: #6b7280;
          font-size: 12px;
        }
        
        .international-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          margin-top: 10px;
        }
        
        .intl-card {
          background: white;
          padding: 12px;
          border-radius: 8px;
          border: 1px solid #e2e8f0;
          text-align: center;
        }
        
        .intl-number {
          font-weight: 700;
          color: #111827;
          font-size: 16px;
          margin-bottom: 4px;
        }
        
        .intl-country {
          font-size: 11px;
          color: #6b7280;
        }
        
        .immediate-tips {
          background: #fef3c7;
          border-left: 4px solid #f59e0b;
        }
        
        .tips-header {
          display: flex;
          align-items: flex-start;
          gap: 12px;
        }
        
        .tips-title {
          font-weight: 600;
          color: #92400e;
          margin-bottom: 8px;
          font-size: 15px;
        }
        
        .tips-list {
          color: #78350f;
          font-size: 13px;
          line-height: 1.6;
        }
        
        .crisis-message {
          font-size: 13px;
          color: #6b7280;
          text-align: center;
          margin: 20px 0;
          line-height: 1.6;
          font-style: italic;
          padding: 15px;
          background: #f8fafc;
          border-radius: 10px;
          border: 1px solid #e2e8f0;
        }
        
        .crisis-actions {
          margin-top: 20px;
        }
        
        .crisis-close-btn {
          width: 100%;
          padding: 14px 20px;
          background: linear-gradient(135deg, #8b5cf6, #ec4899);
          color: white;
          border: none;
          border-radius: 10px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 600;
          transition: background 0.3s;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }
        
        .crisis-close-btn:hover {
          background: linear-gradient(135deg, #7c3aed, #db2777);
        }
        
        @media (max-width: 768px) {
          .crisis-modal-content {
            padding: 15px;
          }
          
          .international-grid {
            grid-template-columns: 1fr;
          }
          
          .support-number {
            font-size: 20px;
          }
          
          .support-card.textline .support-number {
            font-size: 16px;
          }
          
          .crisis-title {
            font-size: 18px;
          }
        }
        
        @media (max-width: 375px) {
          .crisis-modal-content {
            padding: 12px;
          }
          
          .crisis-section {
            padding: 12px;
          }
          
          .support-card {
            padding: 12px;
          }
        }
      `;
      document.head.appendChild(crisisStyles);
    }
    
    // Add event listener for close button
    const closeBtn = document.querySelector('.crisis-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', function() {
        const modal = document.getElementById('mentivio-crisis-modal');
        if (modal) {
          modal.remove();
          // Focus back on input
          setTimeout(() => {
            if (mentivioInput) {
              mentivioInput.focus();
            }
          }, 100);
        }
      });
    }
    
    // Also add event listener for Escape key
    const closeModalOnEscape = function(e) {
      if (e.key === 'Escape') {
        const modal = document.getElementById('mentivio-crisis-modal');
        if (modal) {
          modal.remove();
          document.removeEventListener('keydown', closeModalOnEscape);
        }
      }
    };
    document.addEventListener('keydown', closeModalOnEscape);
  };

  // ================================
  // GLOBAL ACCESS
  // ================================
  if (!window.mentivioGlobal) {
    window.mentivioGlobal = {
      showCrisisHelp: window.showEnhancedCrisisResources,
      quickCheckIn: () => {
        const feelings = {
          en: [
            "How's your heart today?",
            "What's one true thing you're feeling?",
            "What small hope are you holding?",
            "What's weighing on your mind?"
          ],
          es: [
            "¿Cómo está tu corazón hoy?",
            "¿Qué cosa verdadera estás sintiendo?",
            "¿Qué pequeña esperanza estás sosteniendo?",
            "¿Qué te preocupa?"
          ],
          vi: [
            "Trái tim bạn hôm nay thế nào?",
            "Một điều chân thật bạn đang cảm thấy là gì?",
            "Hy vọng nhỏ nào bạn đang giữ?",
            "Điều gì đang đè nặng tâm trí bạn?"
          ],
          zh: [
            "你今天的心情如何？",
            "你真正感受到的一件事是什么？",
            "你怀着怎样的小希望？",
            "什么让你心事重重？"
          ]
        };
        
        const currentLang = CONFIG ? CONFIG.language : 'en';
        const langFeelings = feelings[currentLang] || feelings.en;
        const feeling = langFeelings[Math.floor(Math.random() * langFeelings.length)];
        
        // Try to open chat window and set the message
        if (mentivioInput) {
          mentivioInput.value = feeling;
          mentivioInput.focus();
          
          // Show window if not open
          if (!isWindowOpen && window.showMentivioWindow) {
            window.showMentivioWindow();
          }
        } else {
          alert(feeling);
        }
      },
      getInspiration: async () => {
        try {
          const response = await fetch('/chatbot/api/inspiration');
          if (response.ok) {
            const data = await response.json();
            alert(`${data.quote}\n\n- ${data.story.title}`);
          }
        } catch (error) {
          console.error('Inspiration fetch error:', error);
        }
      },
      setLanguage: (lang) => {
        if (['en', 'es', 'vi', 'zh'].includes(lang)) {
          if (updateChatbotLanguage) {
            updateChatbotLanguage(lang);
          } else {
            // Fallback: save to localStorage and dispatch event
            localStorage.setItem('mentivio_language', lang);
            document.dispatchEvent(new CustomEvent('languageChanged', {
              detail: { language: lang }
            }));
          }
        }
      },
      getLanguage: () => CONFIG ? CONFIG.language : 'en',
      updateHeader: (lang) => {
        if (lang) {
          updateHeaderText(lang);
        } else if (CONFIG && CONFIG.language) {
          updateHeaderText(CONFIG.language);
        }
      },
      showChat: showWindow,
      hideChat: hideWindow
    };
  }

  // ================================
  // EXPOSE FUNCTIONS GLOBALLY
  // ================================
  window.updateChatbotLanguage = updateChatbotLanguage;
  window.isMentivioWindowOpen = () => isWindowOpen;

  // ================================
  // INITIAL LANGUAGE SYNC
  // ================================
  setTimeout(() => {
    // Initial sync with global language manager
    if (window.globalLangManager) {
      const globalLang = window.globalLangManager.currentLang;
      if (globalLang && globalLang !== CONFIG.language && updateChatbotLanguage) {
        console.log('Initial language sync with global manager:', globalLang);
        updateChatbotLanguage(globalLang);
      }
    }
    
    // Ensure header is updated on initial load
    if (CONFIG && CONFIG.language) {
      updateHeaderText(CONFIG.language);
    }
  }, 1000);
}

})();