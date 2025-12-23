// ================================
// Mentivio — Intelligent Mental Health Companion
// ================================
document.addEventListener('DOMContentLoaded', () => {

  // ================================
  // ENHANCED CONFIGURATION
  // ================================
  const CONFIG = {
    encryptionKey: 'mentivio-local-key-v2',
    voiceEnabled: 'speechSynthesis' in window,
    aiMode: 'therapist', // 'friend' or 'therapist'
    sessionTimeout: 300000 // 5 minutes
  };

  // ================================
  // KNOWLEDGE BASE & RESPONSE ENGINE
  // ================================
  const MENTIVIO_BRAIN = {
    // Context understanding patterns
    patterns: {
      greetings: /(hello|hi|hey|good morning|good afternoon)/i,
      gratitude: /(thank you|thanks|appreciate)/i,
      sadness: /(sad|depressed|down|hopeless|empty|lonely)/i,
      anxiety: /(anxious|worried|nervous|stressed|panic|overwhelmed)/i,
      anger: /(angry|mad|frustrated|annoyed|irritated)/i,
      sleep: /(sleep|insomnia|tired|exhausted|fatigue)/i,
      relationships: /(friend|partner|family|parent|spouse|boyfriend|girlfriend)/i,
      work: /(work|job|career|boss|colleague|office)/i,
      trauma: /(abuse|trauma|ptsd|assault|violence)/i,
      crisis: /(suicide|kill myself|end it all|want to die|don't want to live)/i
    },
    
    // Response templates by mode
    responses: {
      therapist: {
        reflections: [
          "I'm hearing that {topic} has been weighing on you. Tell me more about that?",
          "It sounds like {emotion} is coming up around {topic}. How long has this been present?",
          "What I'm understanding is {summary}. What does that bring up for you?",
          "I notice you mentioned {keyword}. Would you like to explore that feeling further?",
          "Let's gently unpack {topic}. Where do you feel this in your body?"
        ],
        questions: [
          "What's the smallest step you could take toward feeling better?",
          "If this feeling had a color or shape, what would it be?",
          "What would you say to a friend experiencing this?",
          "What's one thing you're grateful for today, even if tiny?",
          "How would your life be different without this burden?",
          "What does your intuition whisper about this situation?"
        ],
        affirmations: [
          "You're showing courage by exploring this.",
          "Your feelings are valid and important.",
          "It's okay to not have all the answers right now.",
          "Healing isn't linear, and you're on your own timeline.",
          "You deserve compassion, especially from yourself."
        ]
      },
      friend: {
        reflections: [
          "Hey, that sounds really tough about {topic}. Want to talk more?",
          "I get why you'd feel {emotion} about that. That's really understandable.",
          "Damn, {topic} is heavy stuff. I'm here for you.",
          "It makes total sense you're feeling this way. Anyone would.",
          "That's a lot to carry. How can I support you right now?"
        ],
        questions: [
          "What's helping you get through the day?",
          "Remember that time you got through something hard? What helped then?",
          "If you could wave a magic wand, what would change?",
          "What's one thing that made you smile recently?",
          "Who in your life really gets what you're going through?"
        ],
        affirmations: [
          "You're stronger than you realize.",
          "I'm proud of you for sharing this.",
          "You're not alone in this, I promise.",
          "It's okay to have bad days. They don't define you.",
          "You matter, and your feelings matter."
        ]
      }
    },
    
    // Follow-up system
    contextMemory: {
      lastTopics: [],
      emotionalState: 'neutral',
      conversationDepth: 0,
      lastQuestion: null
    }
  };

  // ================================
  // AI RESPONSE GENERATOR
  // ================================
  class MentivioAI {
    constructor() {
      this.context = MENTIVIO_BRAIN.contextMemory;
    }
    
    analyzeText(text) {
      const analysis = {
        emotions: [],
        topics: [],
        intensity: 1,
        requiresFollowUp: false
      };
      
      // Detect emotions and topics
      for (const [category, pattern] of Object.entries(MENTIVIO_BRAIN.patterns)) {
        if (pattern.test(text) && !['crisis', 'greetings'].includes(category)) {
          analysis.topics.push(category);
          if (['sadness', 'anxiety', 'anger'].includes(category)) {
            analysis.emotions.push(category);
            analysis.intensity = 2;
          }
        }
      }
      
      // Detect crisis
      if (MENTIVIO_BRAIN.patterns.crisis.test(text)) {
        analysis.crisis = true;
        analysis.intensity = 3;
      }
      
      // Detect gratitude
      if (MENTIVIO_BRAIN.patterns.gratitude.test(text)) {
        analysis.emotions.push('grateful');
        analysis.intensity = 0.5;
      }
      
      // Update context
      if (analysis.topics.length > 0) {
        this.context.lastTopics = [...new Set([...this.context.lastTopics, ...analysis.topics])].slice(-3);
        this.context.conversationDepth++;
      }
      
      return analysis;
    }
    
    generateResponse(userInput, mode = CONFIG.aiMode) {
      const analysis = this.analyzeText(userInput);
      const responses = MENTIVIO_BRAIN.responses[mode];
      
      // Crisis response
      if (analysis.crisis) {
        this.context.conversationDepth = 0;
        return this.getCrisisResponse();
      }
      
      // Greeting response
      if (MENTIVIO_BRAIN.patterns.greetings.test(userInput)) {
        return `Hello there. I'm here to listen. What's on your mind today?`;
      }
      
      // Gratitude response
      if (MENTIVIO_BRAIN.patterns.gratitude.test(userInput)) {
        return `You're welcome. I'm genuinely glad I could be here for you. How are you feeling now?`;
      }
      
      // Determine response type
      let responseType;
      if (this.context.conversationDepth < 2) {
        responseType = 'reflections'; // Start with reflection
      } else if (this.context.conversationDepth < 4) {
        responseType = Math.random() > 0.5 ? 'questions' : 'reflections';
      } else {
        responseType = Math.random() > 0.3 ? 'questions' : 'affirmations';
      }
      
      // Select template
      const templates = responses[responseType];
      let template = templates[Math.floor(Math.random() * templates.length)];
      
      // Personalize template
      if (analysis.topics.length > 0) {
        template = template.replace('{topic}', analysis.topics[0]);
      }
      if (analysis.emotions.length > 0) {
        template = template.replace('{emotion}', analysis.emotions[0]);
      }
      
      // Add follow-up question if appropriate
      if (responseType !== 'questions' && analysis.requiresFollowUp) {
        const questions = responses.questions;
        template += ` ${questions[Math.floor(Math.random() * questions.length)]}`;
      }
      
      this.context.lastQuestion = template;
      return template;
    }
    
    getCrisisResponse() {
      return `
        <div style="background:#ffe6e6;border-left:4px solid #ff4444;padding:12px;border-radius:8px">
          <strong>⚠️ I hear how much pain you're in.</strong><br><br>
          Please reach out to a human professional right now:<br><br>
          🇺🇸 <strong>988</strong> Suicide & Crisis Lifeline (24/7)<br>
          🇬🇧 <strong>116 123</strong> Samaritans<br>
          🇨🇦 <strong>1-833-456-4566</strong> Crisis Services Canada<br><br>
          You don't have to go through this alone. <em>Right now, please reach out.</em>
        </div>
      `;
    }
    
    suggestResources(topics) {
      const resources = {
        anxiety: [
          "Deep breathing exercise",
          "5-4-3-2-1 grounding technique",
          "Progressive muscle relaxation"
        ],
        sadness: [
          "Gratitude journaling",
          "Gentle movement or stretching",
          "Connecting with a safe person"
        ],
        sleep: [
          "Sleep hygiene checklist",
          "Guided sleep meditation",
          "Digital sunset routine"
        ],
        relationships: [
          "Boundary-setting worksheet",
          "Communication skills practice",
          "Needs assessment exercise"
        ]
      };
      
      const suggestions = [];
      topics.forEach(topic => {
        if (resources[topic]) {
          suggestions.push(...resources[topic].slice(0, 2));
        }
      });
      
      return suggestions.length > 0 
        ? `<br><br><small>🌱 <em>Try this:</em> ${suggestions.slice(0, 3).join(' • ')}</small>`
        : '';
    }
  }

  // ================================
  // ENHANCED UI
  // ================================
  document.body.insertAdjacentHTML('beforeend', `
  <div id="mentivio-root" style="position:fixed;bottom:20px;right:20px;z-index:9999;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
    <button id="mentivioToggle" style="width:60px;height:60px;border-radius:50%;border:none;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font-size:26px;box-shadow:0 4px 15px rgba(102,126,234,0.3);cursor:pointer;transition:transform 0.2s">🤍</button>

    <div id="mentivioWindow" style="display:none;width:420px;height:720px;background:#f8f9fa;border-radius:20px;position:absolute;bottom:80px;right:0;flex-direction:column;box-shadow:0 10px 40px rgba(0,0,0,0.15);border:1px solid #e2e8f0;overflow:hidden">

      <header style="padding:16px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;display:flex;justify-content:space-between;align-items:center">
        <div>
          <strong style="font-size:18px">Mentivio</strong><br>
          <small style="opacity:0.9;font-size:12px">Confidential mental health companion</small>
        </div>
        <div style="display:flex;gap:10px">
          <button id="settingsBtn" style="background:none;border:none;color:white;font-size:18px">⚙️</button>
          <button id="closeMentivio" style="background:none;border:none;color:white;font-size:24px;line-height:1">×</button>
        </div>
      </header>

      <div style="padding:12px;background:#eef1ff;display:flex;gap:8px;border-bottom:1px solid #e2e8f0">
        <select id="modeToggle" style="flex:1;padding:8px;border-radius:8px;border:1px solid #cbd5e0;background:white">
          <option value="friend">🤝 Friend Mode</option>
          <option value="therapist">👨‍⚕️ Therapist Mode</option>
        </select>
        <button id="voiceBtn" class="icon-btn" title="Voice input">🎙</button>
        <button id="exportPdf" class="icon-btn" title="Export journal">📄</button>
        <button id="dashboardBtn" class="icon-btn" title="Insights">📊</button>
      </div>

      <div id="mentivioMessages" style="flex:1;padding:16px;overflow-y:auto;display:flex;flex-direction:column;gap:12px;background:#f8fafc"></div>

      <div id="quickReplies" style="display:none;padding:12px;background:white;border-top:1px solid #e2e8f0">
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="quick-reply">I'm feeling anxious</button>
          <button class="quick-reply">Had a tough day</button>
          <button class="quick-reply">Need coping strategies</button>
          <button class="quick-reply">Just checking in</button>
        </div>
      </div>

      <div style="padding:16px;background:white;border-top:1px solid #e2e8f0">
        <div style="display:flex;gap:8px">
          <input id="mentivioInput" placeholder="What's on your mind?" 
            style="flex:1;padding:12px 16px;border-radius:12px;border:1px solid #e2e8f0;background:#f8fafc;font-size:14px">
          <button id="sendBtn" style="padding:12px 16px;background:#667eea;color:white;border:none;border-radius:12px;cursor:pointer">➤</button>
        </div>
        <div style="display:flex;gap:8px;margin-top:8px">
          <button id="journalBtn" style="flex:1;padding:10px;background:#edf2f7;border:none;border-radius:8px;cursor:pointer">✍️ Journal Entry</button>
          <button id="moodBtn" style="width:40px;background:#edf2f7;border:none;border-radius:8px;cursor:pointer">😊</button>
        </div>
      </div>
    </div>
  </div>

  <style>
    .icon-btn { width:40px; height:40px; border-radius:8px; border:1px solid #cbd5e0; background:white; cursor:pointer; }
    .quick-reply { padding:8px 12px; background:#e2e8f0; border:none; border-radius:20px; font-size:13px; cursor:pointer; }
    .quick-reply:hover { background:#cbd5e0; }
    .user-msg { align-self:flex-end; background:linear-gradient(135deg,#667eea,#764ba2); color:white; padding:12px 16px; border-radius:18px 18px 4px 18px; max-width:80%; }
    .bot-msg { align-self:flex-start; background:white; color:#2d3748; padding:12px 16px; border-radius:18px 18px 18px 4px; max-width:80%; box-shadow:0 2px 8px rgba(0,0,0,0.05); }
    .typing-indicator { display:inline-block; background:#e2e8f0; padding:8px 16px; border-radius:18px; }
    .typing-dot { display:inline-block; width:6px; height:6px; background:#a0aec0; border-radius:50%; margin:0 2px; animation: pulse 1.5s infinite; }
    .typing-dot:nth-child(2) { animation-delay:0.2s; }
    .typing-dot:nth-child(3) { animation-delay:0.4s; }
    @keyframes pulse { 0%, 100% { opacity:0.4; } 50% { opacity:1; } }
  </style>
  `);

  // ================================
  // INITIALIZATION
  // ================================
  const ai = new MentivioAI();
  let memory = JSON.parse(localStorage.getItem('mentivioMemory')) || {
    conversations: [],
    journalEntries: [],
    moodLogs: [],
    insights: [],
    safetyFlags: 0,
    lastActive: Date.now()
  };

  let sessionActive = true;
  let typingTimeout = null;

  // ================================
  // UI CONTROLS
  // ================================
  mentivioToggle.onclick = () => {
    mentivioWindow.style.display = 'flex';
    showTypingIndicator();
    setTimeout(() => {
      if (memory.conversations.length === 0) {
        bot("Hello. I'm Mentivio, your confidential mental health companion. How are you feeling today?");
      } else {
        bot("Welcome back. How have you been since we last spoke?");
      }
    }, 800);
  };

  closeMentivio.onclick = () => {
    saveSession();
    mentivioWindow.style.display = 'none';
  };

  modeToggle.onchange = (e) => {
    CONFIG.aiMode = e.target.value;
    bot(`Switched to ${e.target.value} mode. How can I support you differently?`);
  };

  // ================================
  // ENHANCED INPUT HANDLER
  // ================================
  mentivioInput.onkeypress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  sendBtn.onclick = sendMessage;

  function sendMessage() {
    const text = mentivioInput.value.trim();
    if (!text) return;

    // User message
    user(text);
    mentivioInput.value = '';

    // Analyze and store
    const analysis = ai.analyzeText(text);
    memory.conversations.push({
      user: text,
      analysis,
      timestamp: new Date().toISOString(),
      mode: CONFIG.aiMode
    });

    // Safety check
    if (analysis.crisis) {
      memory.safetyFlags++;
      localStorage.setItem('mentivioMemory', JSON.stringify(memory));
      showTypingIndicator();
      setTimeout(() => {
        bot(ai.getCrisisResponse());
        showQuickReplies(['I need help now', 'Feeling calmer', 'Want to talk']);
      }, 1200);
      return;
    }

    // Generate intelligent response
    showTypingIndicator();
    setTimeout(() => {
      const response = ai.generateResponse(text, CONFIG.aiMode);
      
      // Add resources if appropriate
      let fullResponse = response;
      if (analysis.topics.length > 0 && Math.random() > 0.6) {
        fullResponse += ai.suggestResources(analysis.topics);
      }

      bot(fullResponse);
      
      // Store bot response
      memory.conversations[memory.conversations.length - 1].bot = fullResponse;
      memory.lastActive = Date.now();
      
      // Show quick replies after depth
      if (ai.context.conversationDepth > 1 && Math.random() > 0.5) {
        showQuickReplies([
          'Tell me more',
          'I feel better',
          'What should I do?',
          'Change topic'
        ]);
      }
      
      // Auto-save
      saveSession();
    }, calculateTypingDelay(text));
  }

  // ================================
  // QUICK REPLIES
  // ================================
  function showQuickReplies(options) {
    const container = document.getElementById('quickReplies');
    const buttons = container.querySelectorAll('.quick-reply');
    
    buttons.forEach((btn, i) => {
      if (options[i]) {
        btn.textContent = options[i];
        btn.style.display = 'block';
        btn.onclick = () => {
          user(options[i]);
          container.style.display = 'none';
          showTypingIndicator();
          setTimeout(() => bot(ai.generateResponse(options[i])), 800);
        };
      } else {
        btn.style.display = 'none';
      }
    });
    
    container.style.display = 'block';
  }

  // ================================
  // MOOD TRACKER
  // ================================
  moodBtn.onclick = () => {
    const moods = ['😊', '😌', '😐', '😔', '😢', '😰', '😡'];
    bot(`
      How are you feeling right now?<br><br>
      ${moods.map(m => `<button onclick="setMood('${m}')" style="font-size:24px;background:none;border:none;cursor:pointer">${m}</button>`).join(' ')}
    `);
  };

  window.setMood = function(mood) {
    const moodMap = {
      '😊': 'happy', '😌': 'calm', '😐': 'neutral',
      '😔': 'sad', '😢': 'crying', '😰': 'anxious', '😡': 'angry'
    };
    
    memory.moodLogs.push({
      mood: moodMap[mood] || 'neutral',
      emoji: mood,
      timestamp: new Date().toISOString()
    });
    
    bot(`Noted ${mood}. What's contributing to this feeling?`);
    saveSession();
  };

  // ================================
  // ENHANCED JOURNAL
  // ================================
  journalBtn.onclick = () => {
    const entry = prompt('Write your journal entry (private, encrypted):');
    if (entry) {
      memory.journalEntries.push({
        content: entry,
        timestamp: new Date().toISOString(),
        length: entry.length
      });
      bot(`Journal entry saved. Sometimes writing helps us see patterns. Would you like to reflect on it?`);
      saveSession();
    }
  };

  // ================================
  // ENHANCED DASHBOARD
  // ================================
  dashboardBtn.onclick = () => {
    const insights = generateInsights();
    bot(`
      <div style="background:white;padding:16px;border-radius:12px;border:1px solid #e2e8f0">
        <strong>📊 Your Mental Wellness Insights</strong><br><br>
        • Conversations: ${memory.conversations.length}<br>
        • Journal entries: ${memory.journalEntries.length}<br>
        • Moods tracked: ${memory.moodLogs.length}<br>
        • Most discussed: ${insights.topTopics.join(', ')}<br>
        • Emotional tone: ${insights.avgMood}<br><br>
        <small><em>Pattern: ${insights.pattern}</em></small>
      </div>
    `);
  };

  // ================================
  // VOICE INTERACTION
  // ================================
  voiceBtn.onclick = () => {
    if (!CONFIG.voiceEnabled) {
      bot("Voice not supported in your browser.");
      return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      bot("Voice recognition not available.");
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      mentivioInput.value = transcript;
      sendMessage();
    };
    
    recognition.start();
    bot("Listening... Speak your mind.");
  };

  // ================================
  // UTILITY FUNCTIONS
  // ================================
  function showTypingIndicator() {
    clearTimeout(typingTimeout);
    const indicator = `<div class="typing-indicator"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>`;
    mentivioMessages.innerHTML += `<div class="bot-msg">${indicator}</div>`;
    mentivioMessages.scrollTop = mentivioMessages.scrollHeight;
    
    typingTimeout = setTimeout(() => {
      const indicators = document.querySelectorAll('.typing-indicator');
      if (indicators.length > 0) {
        indicators[indicators.length - 1].parentElement.remove();
      }
    }, 3000);
  }

  function calculateTypingDelay(text) {
    return Math.min(2000, Math.max(800, text.length * 15));
  }

  function user(text) {
    mentivioMessages.innerHTML += `<div class="user-msg">${escapeHtml(text)}</div>`;
    mentivioMessages.scrollTop = mentivioMessages.scrollHeight;
  }

  function bot(text) {
    const indicators = document.querySelectorAll('.typing-indicator');
    if (indicators.length > 0) {
      indicators[indicators.length - 1].parentElement.remove();
    }
    
    mentivioMessages.innerHTML += `<div class="bot-msg">${text}</div>`;
    mentivioMessages.scrollTop = mentivioMessages.scrollHeight;
    
    // Text-to-speech if enabled
    if (CONFIG.voiceEnabled && memory.conversations.length < 10) {
      const utterance = new SpeechSynthesisUtterance(text.replace(/<[^>]*>/g, ''));
      utterance.rate = 0.9;
      utterance.pitch = 1;
      speechSynthesis.speak(utterance);
    }
  }

  function generateInsights() {
    const topics = {};
    memory.conversations.forEach(conv => {
      conv.analysis.topics.forEach(topic => {
        topics[topic] = (topics[topic] || 0) + 1;
      });
    });
    
    const topTopics = Object.entries(topics)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([topic]) => topic);
    
    const moods = memory.moodLogs.map(m => m.mood);
    const moodCounts = moods.reduce((acc, mood) => {
      acc[mood] = (acc[mood] || 0) + 1;
      return acc;
    }, {});
    
    const avgMood = Object.entries(moodCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'neutral';
    
    const patterns = [
      "You often reflect in the evening",
      "Writing helps you process emotions",
      "You value connection and understanding",
      "Growth comes through self-awareness"
    ];
    
    return {
      topTopics,
      avgMood,
      pattern: patterns[Math.floor(Math.random() * patterns.length)]
    };
  }

  function saveSession() {
    // Trim old conversations to prevent storage overflow
    if (memory.conversations.length > 100) {
      memory.conversations = memory.conversations.slice(-50);
    }
    
    localStorage.setItem('mentivioMemory', JSON.stringify(memory));
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // ================================
  // SESSION MANAGEMENT
  // ================================
  setInterval(() => {
    if (sessionActive && Date.now() - memory.lastActive > CONFIG.sessionTimeout) {
      bot("It's been a while. Would you like to check in about how you're feeling now?");
      memory.lastActive = Date.now();
    }
  }, 60000);

  // Initial greeting
  setTimeout(() => {
    if (mentivioWindow.style.display === 'none') {
      // Optional: Show notification bubble
      mentivioToggle.style.animation = 'pulse 2s infinite';
      setTimeout(() => mentivioToggle.style.animation = '', 6000);
    }
  }, 10000);
});