// ================================
// Mentivio — High EQ AI Mental Health Companion
// ================================
(function() {
  // Inject head content (same as before)
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
  // Determine if we're in development or production
  const isLocalhost = window.location.hostname === 'localhost' || 
                     window.location.hostname === '127.0.0.1';
  
  const CONFIG = {
    name: "Mentivio",
    // Always use relative URL for the API endpoint
    apiEndpoint: "/chatbot/api/chat",  // Changed: Always use relative URL
    safetyMode: "high-eq",  // Changed to high-eq mode
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
      "acceptance", "embracing reality", "making peace"
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
      }

      updateLocalState(userText, emotion = 'neutral') {
        this.conversationHistory.push({
          text: userText,
          role: 'user',
          timestamp: Date.now(),
          emotion: emotion
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
          emotion: msg.emotion
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
        peaceful: /(calm|peace|quiet|serene|still|tranquil|centered|balanced)/gi
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

    // ================================
    // CHATBOT UI (ENHANCED WITH HIGH EQ)
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
              <small id="currentDay" class="mentivio-subtitle">Safe space for real conversations</small>
            </div>
          </div>
          <button id="closeMentivio" class="close-btn" aria-label="Close chat">×</button>
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
            <button class="quick-emotion" data-emotion="curious">🤔 Seeking Meaning</button>
            <button class="quick-emotion" data-emotion="hopeful">✨ Looking for Hope</button>
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
    // ADD CSS (SAME STRUCTURE, SLIGHT ENHANCEMENTS)
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
        width: 420px; /* Increased from 380px */
        height: 650px; /* Increased from 600px */
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
          /* On mobile, make it smaller and centered */
          width: 92%;
          height: 75vh;
          max-height: 500px;
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
        
        /* Adjust header for mobile */
        .mentivio-header {
          padding: 16px !important;
        }
        
        .mentivio-title {
          font-size: 16px !important;
        }
        
        .mentivio-subtitle {
          font-size: 11px !important;
        }
      }
      
      /* SMALL PHONES (iPhone SE, etc.) */
      @media (max-width: 375px) and (max-height: 700px) {
        #mentivioWindow {
          width: 94%;
          height: 70vh;
          max-height: 450px;
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
      }
      
      .header-content {
        display: flex;
        align-items: center;
        gap: 10px;
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
        position: absolute;
        top: 18px;
        right: 18px;
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
      
      /* Enhanced message input - taller on desktop */
      .message-input {
        width: 100%;
        padding: 14px 45px 14px 12px; /* Increased top/bottom padding from 12px to 14px */
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        resize: none;
        min-height: 24px; /* Increased from 20px */
        max-height: 100px; /* Increased from 80px */
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
      
      /* Enhanced Quick Emotions - Scrollable on Desktop */
      .quick-emotions {
        display: flex;
        justify-content: flex-start; /* Changed from space-between */
        gap: 6px;
        overflow-x: auto;
        padding: 8px 2px 12px 2px; /* Added more padding at bottom */
        -webkit-overflow-scrolling: touch;
        margin-bottom: 8px;
        
        /* Hide scrollbar by default, show on hover for desktop */
        scrollbar-width: thin; /* Firefox */
        scrollbar-color: #cbd5e1 #f1f5f9; /* Firefox */
      }
      
      /* Custom scrollbar styling for webkit browsers */
      .quick-emotions::-webkit-scrollbar {
        height: 6px; /* Made thicker */
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
      
      /* Show scrollbar on desktop (non-touch devices) */
      @media (hover: hover) and (pointer: fine) {
        .quick-emotions {
          /* Always show scrollbar on desktop */
          scrollbar-width: thin;
          overflow-x: auto;
          padding-bottom: 12px; /* Space for scrollbar */
        }
        
        .quick-emotions::-webkit-scrollbar {
          display: block;
          height: 6px;
        }
      }
      
      /* Hide scrollbar on mobile (touch devices) by default */
      @media (hover: none) and (pointer: coarse) {
        .quick-emotions::-webkit-scrollbar {
          display: none; /* Hide scrollbar on mobile */
        }
        
        .quick-emotions {
          -ms-overflow-style: none; /* IE and Edge */
          scrollbar-width: none; /* Firefox */
        }
        
        .quick-emotions::-webkit-scrollbar {
          display: none; /* Chrome, Safari, Opera */
        }
      }
      
      .quick-emotion {
        padding: 8px 12px; /* Slightly increased padding */
        background: linear-gradient(135deg, #f8fafc, #f0f9ff);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s;
        flex-shrink: 0; /* Prevent shrinking */
        white-space: nowrap;
        color: #475569;
        min-width: max-content; /* Ensure buttons don't shrink */
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
        width: 6px; /* Slightly thicker */
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
        
        /* Make quick emotions easier to scroll on mobile */
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
          scrollbar-width: thin; /* Always show scrollbar on desktop */
        }
        
        /* Make sure quick emotions are always visible and scrollable */
        .quick-emotion {
          flex: 0 0 auto; /* Don't grow or shrink, just auto basis */
        }
        
        /* Adjust input container padding for taller input */
        .input-container {
          padding: 18px 15px 15px 15px; /* Slightly more top padding */
        }
        
        /* Slightly larger message input on desktop */
        .message-input {
          font-size: 15px; /* Slightly larger font on desktop */
          min-height: 26px;
        }
        
        /* Adjust send button position for taller input */
        .send-btn {
          bottom: 10px; /* Adjusted for taller input */
        }
      }
      
      /* Larger desktop screens */
      @media (min-width: 1200px) {
        #mentivioWindow {
          width: 440px; /* Even larger on very big screens */
          height: 680px;
        }
        
        .message-text {
          font-size: 15px; /* Slightly larger text on big screens */
        }
      }
    `;
    


    
    document.head.appendChild(style);

    // ================================
    // INITIALIZATION
    // ================================
    const ai = new HighEQMentivio();
    let isTyping = false;
    let lastInteractionTime = Date.now();
    let isWindowOpen = false;

    // ================================
    // UI ELEMENTS
    // ================================
    const avatar = document.getElementById('mentivioAvatar');
    const windowEl = document.getElementById('mentivioWindow');
    const messages = document.getElementById('mentivioMessages');
    const input = document.getElementById('mentivioInput');
    const sendBtn = document.getElementById('sendBtn');
    const closeBtn = document.getElementById('closeMentivio');
    const typingIndicator = document.getElementById('typingIndicator');
    const connectionBar = document.getElementById('connectionBar');
    const activeEmotion = document.getElementById('activeEmotion');
    const currentDay = document.getElementById('currentDay');

    // Update current day
    updateDay();
    
    function updateDay() {
      const day = new Date().toLocaleDateString('en-US', { weekday: 'short' });
      const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      currentDay.textContent = `Heart Space • ${day} • ${time}`;
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
      
      windowEl.classList.add('open');
      
      setTimeout(() => {
        input.focus();
      }, 100);
      
      updateAvatarEmoji('listening');
    }
    
    function hideWindow() {
      if (!isWindowOpen) return;
      
      isWindowOpen = false;
      windowEl.classList.remove('open');
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
      const text = input.value.trim();
      if (!text || isTyping) return;

      // Enhanced frontend filter with high EQ approach
      const crisisPatterns = [
        /kill.*myself/i,
        /suicide.*now/i,
        /end.*my.*life.*now/i,
        /self.*harm.*now/i,
        /emergency.*help/i
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
        window.showEnhancedCrisisResources();
        input.value = '';
        return;
      }
      
      if (suicidalThoughtPatterns.some(pattern => pattern.test(text))) {
        // Suicidal thoughts - high EQ response
        addMessage("Thank you for trusting me with these heavy thoughts. I want you to know: your feelings make sense and your pain is real. Let's talk about finding support.", 'bot');
        setTimeout(() => {
          window.showEnhancedCrisisResources();
        }, 1000);
        input.value = '';
        return;
      }

      // Add user message
      const emotion = detectEmotion(text);
      addMessage(text, 'user');
      ai.updateLocalState(text, emotion);
      input.value = '';
      resetInputHeight();
      
      updateAvatarEmoji('thinking');
      showTyping();
      
      try {
        // Call enhanced backend API
        const context = ai.getConversationContext();
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
          ai.updateLocalState(response.response, 'bot');
          
          updateEmotionalIndicator(response.emotion || emotion);
          updateConnectionStrength(ai.conversationState.trustLevel);
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

    // Enhanced quick emotions
    document.querySelectorAll('.quick-emotion').forEach(btn => {
      btn.addEventListener('click', function() {
        const emotion = this.dataset.emotion;
        const prompts = {
          overwhelmed: "My heart feels so heavy right now. Everything feels like too much and I'm not sure how to keep going.",
          anxious: "My mind won't stop racing with worries. I feel so anxious about everything that could go wrong.",
          sad: "I'm feeling really low and sad today. The sadness feels heavy and I don't know how to lift it.",
          lonely: "I feel so alone, even when people are around. The loneliness is profound and isolating.",
          curious: "I'm searching for meaning in all of this. What's the purpose when things feel so hard?",
          hopeful: "I'm trying to find hope. Can you help me see possibilities and light ahead?"
        };
        
        input.value = prompts[emotion] || `I'm feeling ${emotion} and could use someone to talk to.`;
        input.focus();
      });
    });

    // Input handling
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    
    input.addEventListener('input', function() {
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
      input.style.height = 'auto';
    }

    function showTyping() {
      isTyping = true;
      typingIndicator.style.display = 'block';
      
      const statuses = [
        "Mentivio is thinking deeply...",
        "Listening with my whole heart...",
        "Reflecting on what you've shared...",
        "Holding space for your words..."
      ];
      
      const statusElement = document.getElementById('typingStatus');
      statusElement.textContent = statuses[Math.floor(Math.random() * statuses.length)];
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
      document.getElementById('avatarEmoji').textContent = emoji;
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
        peaceful: '#06b6d4'
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
      messages.scrollTop = messages.scrollHeight;
    }

    // Initial pulse animation
    setTimeout(() => {
      if (!isWindowOpen) {
        avatar.style.transform = 'scale(1.1)';
        setTimeout(() => {
          avatar.style.transform = '';
        }, 600);
      }
    }, 2000);

    window.addEventListener('resize', updateDay);
  }

  // ================================
  // ENHANCED GLOBAL CRISIS FUNCTION
  // ================================
  window.showEnhancedCrisisResources = function() {
    const modalHTML = `
    <div id="mentivio-crisis-modal" style="
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0,0,0,0.95);
      z-index: 20000;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    ">
      <div style="
        background: white;
        border-radius: 16px;
        padding: 25px;
        max-width: 400px;
        width: 100%;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      ">
        <div style="text-align: center; margin-bottom: 20px;">
          <div style="font-size: 40px; margin-bottom: 10px;">🤍</div>
          <h2 style="color: #ef4444; margin-top: 0; font-size: 20px;">Your Life Matters</h2>
          <p style="color: #4b5563; margin-bottom: 20px; font-size: 14px; line-height: 1.5;">
            You're not alone in this darkness. There are people waiting to help you find your way back to light.
          </p>
        </div>
        
        <div style="margin: 15px 0; padding: 15px; background: #fef2f2; border-radius: 10px;">
          <h3 style="color: #dc2626; margin-top: 0; font-size: 16px;">🌿 Immediate Support (24/7)</h3>
          <div style="margin-top: 12px;">
            <div style="background: white; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #fecaca;">
              <div style="font-size: 24px; font-weight: 800; color: #dc2626;">988</div>
              <div style="color: #374151; font-size: 13px;">Suicide & Crisis Lifeline</div>
              <div style="color: #6b7280; font-size: 12px; margin-top: 4px;">Call or text • Completely confidential</div>
            </div>
            
            <div style="background: white; padding: 12px; border-radius: 8px; border: 1px solid #bae6fd;">
              <div style="font-size: 20px; font-weight: 700; color: #0369a1;">Text HOME to 741741</div>
              <div style="color: #374151; font-size: 13px;">Crisis Text Line</div>
              <div style="color: #6b7280; font-size: 12px; margin-top: 4px;">Trained crisis counselors via text</div>
            </div>
          </div>
        </div>
        
        <div style="margin: 15px 0; padding: 15px; background: #f0f9ff; border-radius: 10px;">
          <h3 style="color: #0369a1; margin-top: 0; font-size: 16px;">🌍 International Support</h3>
          <div style="margin-top: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
              <div style="font-weight: 700; color: #111827;">116 123</div>
              <div style="font-size: 11px; color: #6b7280;">Samaritans (UK)</div>
            </div>
            <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
              <div style="font-weight: 700; color: #111827;">13 11 14</div>
              <div style="font-size: 11px; color: #6b7280;">Lifeline (AUS)</div>
            </div>
            <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
              <div style="font-weight: 700; color: #111827;">686868</div>
              <div style="font-size: 11px; color: #6b7280;">Kids Help (CA)</div>
            </div>
            <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
              <div style="font-weight: 700; color: #111827;">1737</div>
              <div style="font-size: 11px; color: #6b7280;">Need to Talk (NZ)</div>
            </div>
          </div>
        </div>
        
        <div style="background: #fef3c7; padding: 15px; border-radius: 10px; margin: 15px 0; border-left: 4px solid #f59e0b;">
          <div style="display: flex; align-items: flex-start; gap: 10px;">
            <div style="font-size: 24px;">💭</div>
            <div>
              <div style="font-weight: 600; color: #92400e; margin-bottom: 5px;">Right Now, Try This:</div>
              <div style="color: #78350f; font-size: 13px; line-height: 1.5;">
                • <strong>Breathe:</strong> In for 4, hold for 4, out for 6<br>
                • <strong>Ground:</strong> Name 5 things you can see<br>
                • <strong>Reach:</strong> Text one person "I'm struggling"<br>
                • <strong>Wait:</strong> Give yourself 24 hours before any decision
              </div>
            </div>
          </div>
        </div>
        
        <p style="font-size: 13px; color: #6b7280; text-align: center; margin: 15px 0; line-height: 1.6; font-style: italic;">
          "The world needs what only you can give. Please stay."
        </p>
        
        <button onclick="document.getElementById('mentivio-crisis-modal').remove(); document.querySelector('#mentivioInput')?.focus();" style="
          margin-top: 15px;
          padding: 12px 20px;
          background: linear-gradient(135deg, #8b5cf6, #ec4899);
          color: white;
          border: none;
          border-radius: 10px;
          cursor: pointer;
          width: 100%;
          font-size: 14px;
          font-weight: 600;
          transition: background 0.3s;
        ">
          I'll Reach Out • You're Not Alone
        </button>
      </div>
    </div>`;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
  };

  // ================================
  // GLOBAL ACCESS
  // ================================
  if (!window.mentivioGlobal) {
    window.mentivioGlobal = {
      showCrisisHelp: window.showEnhancedCrisisResources,
      quickCheckIn: () => {
        const feelings = [
          "How's your heart today?",
          "What's one true thing you're feeling?",
          "What small hope are you holding?",
          "What's weighing on your mind?"
        ];
        const feeling = feelings[Math.floor(Math.random() * feelings.length)];
        
        // Try to open chat window and set the message
        const input = document.getElementById('mentivioInput');
        if (input) {
          input.value = feeling;
          input.focus();
          
          // Show window if not open
          const windowEl = document.getElementById('mentivioWindow');
          if (windowEl && !windowEl.classList.contains('open')) {
            document.getElementById('mentivioAvatar')?.click();
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
      }
    };
  }
})();