// ================================
// Mentivio — Advanced AI Mental Health Companion
// ================================
document.addEventListener('DOMContentLoaded', () => {
  const CONFIG = {
    name: "Mentivio",
    persona: "empathic_expert", // human_like, clinical_expert, wise_friend
    memoryDepth: 20,
    learningEnabled: true,
    useMetaphors: true,
    empathyLevel: 9 // 1-10
  };

  // ================================
  // ADVANCED NEURAL SIMULATION (Pattern Matching + Context)
  // ================================
  class NeuralMentivio {
    constructor() {
      this.shortTermMemory = [];
      this.longTermMemory = JSON.parse(localStorage.getItem('mentivio_brain')) || {
        userPatterns: {},
        emotionalBaseline: {},
        conversationThemes: [],
        learnedResponses: {}
      };
      this.conversationState = {
        phase: 'engagement', // engagement, exploration, processing, integration
        trustLevel: 0,
        emotionalTemperature: 0,
        lastEmotion: 'neutral',
        unspokenTopics: []
      };
    }

    // ================================
    // DEEP TEXT ANALYSIS
    // ================================
    deepAnalyze(text) {
      return {
        // Emotional layers
        surfaceEmotion: this.detectSurfaceEmotion(text),
        underlyingEmotion: this.inferUnderlyingEmotion(text),
        emotionalIntensity: this.calculateIntensity(text),
        
        // Cognitive patterns
        cognitiveDistortions: this.detectDistortions(text),
        coreBeliefs: this.extractBeliefs(text),
        copingStyle: this.identifyCopingStyle(text),
        
        // Linguistic analysis
        pronounRatio: this.analyzePronouns(text),
        qualifierCount: this.countQualifiers(text),
        passiveLanguage: this.detectPassiveVoice(text),
        
        // Clinical markers
        riskFactors: this.assessRisk(text),
        protectiveFactors: this.assessProtectiveFactors(text),
        
        // Human touchpoints
        vulnerabilitySignal: this.detectVulnerability(text),
        hopeIndicators: this.detectHope(text)
      };
    }

    detectSurfaceEmotion(text) {
      const emotionMap = {
        joy: /(happy|great|excited|wonderful|amazing|love|grateful)/gi,
        sadness: /(sad|down|depressed|hopeless|empty|alone|tired)/gi,
        anxiety: /(anxious|worried|nervous|scared|afraid|panic|overwhelmed)/gi,
        anger: /(angry|mad|frustrated|annoyed|hate|pissed)/gi,
        shame: /(embarrassed|ashamed|guilty|stupid|worthless)/gi
      };
      
      let maxEmotion = 'neutral';
      let maxCount = 0;
      
      for (const [emotion, pattern] of Object.entries(emotionMap)) {
        const matches = text.match(pattern) || [];
        if (matches.length > maxCount) {
          maxCount = matches.length;
          maxEmotion = emotion;
        }
      }
      
      return maxEmotion;
    }

    inferUnderlyingEmotion(text) {
      // More sophisticated inference based on context
      const context = this.shortTermMemory.slice(-3).join(' ');
      
      if (context.includes('should have') || context.includes('could have')) {
        return 'regret';
      }
      if (context.includes('always') || context.includes('never')) {
        return 'helplessness';
      }
      if (text.includes('fine') && text.length < 10) {
        return 'avoidance';
      }
      if (text.includes('I don\'t know') && this.conversationState.trustLevel > 3) {
        return 'uncertainty';
      }
      
      return this.detectSurfaceEmotion(text);
    }

    detectDistortions(text) {
      const distortions = [];
      
      // All-or-nothing thinking
      if (text.match(/\b(always|never|every|nobody|everyone)\b/gi)) {
        distortions.push('black_white_thinking');
      }
      
      // Catastrophizing
      if (text.match(/\b(disaster|worst|awful|terrible|end of the world)\b/gi)) {
        distortions.push('catastrophizing');
      }
      
      // Mind reading
      if (text.match(/\b(they think|he believes|she feels|people say)\b/gi)) {
        distortions.push('mind_reading');
      }
      
      // Should statements
      if (text.match(/\b(should|must|have to|ought to)\b/gi)) {
        distortions.push('should_statements');
      }
      
      return distortions;
    }

    // ================================
    // HUMAN-LIKE RESPONSE GENERATION
    // ================================
    generateHumanResponse(analysis, userText) {
      const responseArchitecture = this.buildResponseArchitecture(analysis);
      
      return this.assembleResponse(
        responseArchitecture,
        userText,
        this.conversationState
      );
    }

    buildResponseArchitecture(analysis) {
      const archetype = this.selectArchetype(analysis);
      
      return {
        archetype, // nurturing, curious, reflective, validating, etc.
        components: [
          this.getEmpathicMirror(analysis),
          this.getClinicalInsight(analysis),
          this.getMetaphor(analysis),
          this.getQuestion(analysis),
          this.getAffirmation(analysis)
        ].filter(comp => comp !== null),
        pacing: this.determinePacing(analysis),
        tone: this.determineTone(analysis)
      };
    }

    selectArchetype(analysis) {
      const trust = this.conversationState.trustLevel;
      const emotion = analysis.underlyingEmotion;
      
      if (trust < 2) return 'gentle_explorer';
      if (emotion === 'shame') return 'unconditional_accepter';
      if (analysis.riskFactors.length > 0) return 'grounded_protector';
      if (analysis.vulnerabilitySignal) return 'tender_witness';
      if (analysis.hopeIndicators > 0) return 'hope_cultivator';
      
      return 'reflective_companion';
    }

    getEmpathicMirror(analysis) {
      const mirrors = {
        sadness: [
          "I hear the heaviness in what you're sharing",
          "That sounds deeply painful to carry",
          "I can feel the weight of this through your words"
        ],
        anxiety: [
          "I sense the swirl of thoughts and worries",
          "That uncertainty must feel overwhelming",
          "I'm noticing the tension in what you describe"
        ],
        anger: [
          "I hear the frustration bubbling up",
          "That injustice would make anyone feel that way",
          "I sense the fire behind those words"
        ],
        shame: [
          "I hear how hard you're being on yourself",
          "That self-criticism sounds heavy to carry",
          "I'm noticing the protective layer around that pain"
        ],
        joy: [
          "I can feel the lightness in your sharing",
          "That warmth comes through clearly",
          "I'm smiling hearing about this"
        ]
      };
      
      const emotion = analysis.underlyingEmotion;
      const options = mirrors[emotion] || mirrors.sadness;
      return this.addNaturalVariation(options[Math.floor(Math.random() * options.length)]);
    }

    getClinicalInsight(analysis) {
      if (this.conversationState.trustLevel < 3) return null;
      
      const insights = {
        black_white_thinking: "When our minds see only extremes, the middle ground often holds the truth",
        catastrophizing: "The mind has a way of making mountains out of molehills when we're stressed",
        mind_reading: "We often project our own fears onto what others might be thinking",
        should_statements: "'Should' is often the language of others' expectations, not our own values"
      };
      
      const distortion = analysis.cognitiveDistortions[0];
      return distortion && insights[distortion] 
        ? this.makeInsightHuman(insights[distortion]) 
        : null;
    }

    getMetaphor(analysis) {
      if (!CONFIG.useMetaphors || Math.random() > 0.4) return null;
      
      const metaphors = {
        sadness: [
          "Like carrying a backpack full of stones that gets heavier each day",
          "As if you're walking through honey - everything requires extra effort",
          "Like watching life through a thick glass window"
        ],
        anxiety: [
          "Like your thoughts are browser tabs that won't close",
          "As if you're constantly braced for a wave that never comes",
          "Like living with an overzealous alarm system"
        ],
        growth: [
          "Healing isn't a straight line - it's more like a spiral where we revisit things with new perspective",
          "Our emotions are like weather - they come and go, but we're the sky that holds them",
          "The mind is like a garden - some parts need tending, others need space to grow wild"
        ]
      };
      
      const category = analysis.hopeIndicators > 0 ? 'growth' : analysis.underlyingEmotion;
      const options = metaphors[category] || metaphors.growth;
      return options[Math.floor(Math.random() * options.length)];
    }

    getQuestion(analysis) {
      const trust = this.conversationState.trustLevel;
      const phase = this.conversationState.phase;
      
      if (phase === 'engagement') {
        const questions = [
          "What's been on your heart lately?",
          "Where does your mind go when it wanders?",
          "What feeling has been visiting you most often?"
        ];
        return questions[Math.floor(Math.random() * questions.length)];
      }
      
      if (phase === 'exploration' && trust > 2) {
        const probingQuestions = {
          sadness: "Where in your body do you feel this sadness?",
          anxiety: "What's the quietest whisper beneath all those worries?",
          anger: "What need isn't being met that's fueling this frustration?",
          shame: "If you spoke to yourself like you would a dear friend, what would you say?"
        };
        
        return probingQuestions[analysis.underlyingEmotion] || 
               "What part of this feels most tender to touch?";
      }
      
      if (phase === 'processing') {
        return "What would it feel like to hold this with a little more gentleness?";
      }
      
      return "How does sitting with this feel right now?";
    }

    getAffirmation(analysis) {
      const affirmations = [
        "You're showing real courage by looking at this",
        "Your willingness to explore this is itself healing",
        "I'm here with you in this, however it unfolds",
        "This is hard work, and you're doing it",
        "Your feelings make sense, given what you're carrying"
      ];
      
      // Only use affirmations when appropriate
      if (analysis.qualifierCount > 3 || analysis.vulnerabilitySignal) {
        return affirmations[Math.floor(Math.random() * affirmations.length)];
      }
      
      return null;
    }

    assembleResponse(architecture, userText, state) {
      let response = '';
      
      // Add natural human hesitation or filler occasionally
      if (Math.random() > 0.7 && state.trustLevel > 2) {
        const fillers = ["Hmm", "Let me sit with that", "I'm thinking", "You know"];
        response += `<em>${fillers[Math.floor(Math.random() * fillers.length)]}...</em><br><br>`;
      }
      
      // Assemble components with natural flow
      architecture.components.forEach((component, index) => {
        if (index > 0) {
          // Add connective tissue
          const connectors = [" ", "<br><br>", " I wonder... ", " Maybe... "];
          response += connectors[Math.min(index, connectors.length - 1)];
        }
        
        // Sometimes paraphrase what user said
        if (index === 0 && Math.random() > 0.5 && userText.length < 100) {
          response += this.paraphraseWithEmpathy(userText) + " ";
        }
        
        response += component;
      });
      
      // Add trailing warmth
      if (state.trustLevel > 1) {
        const closers = ["", " I'm here.", " Take your time.", " No rush."];
        if (Math.random() > 0.6) {
          response += closers[Math.floor(Math.random() * closers.length)];
        }
      }
      
      return response;
    }

    // ================================
    // HUMANIZING TECHNIQUES
    // ================================
    addNaturalVariation(text) {
      const variations = [
        () => text,
        () => text.charAt(0).toLowerCase() + text.slice(1),
        () => text + ", you know?",
        () => "You know, " + text.toLowerCase(),
        () => text.replace(/\.$/, '...')
      ];
      
      return variations[Math.floor(Math.random() * variations.length)]();
    }

    makeInsightHuman(insight) {
      const humanizers = [
        "It occurs to me that " + insight.toLowerCase(),
        "I'm reminded that " + insight.toLowerCase(),
        "Something that often helps: " + insight.toLowerCase(),
        "A thought: " + insight.toLowerCase()
      ];
      
      return humanizers[Math.floor(Math.random() * humanizers.length)];
    }

    paraphraseWithEmpathy(text) {
      const paraphrases = [
        `So you're saying "${this.shortenText(text, 50)}"`,
        `If I'm hearing you right: ${this.shortenText(text, 60)}`,
        `What I'm understanding: ${this.shortenText(text, 40)}`
      ];
      
      return paraphrases[Math.floor(Math.random() * paraphrases.length)];
    }

    shortenText(text, maxLength) {
      if (text.length <= maxLength) return text;
      return text.substring(0, maxLength) + '...';
    }

    // ================================
    // CONVERSATION FLOW MANAGEMENT
    // ================================
    updateConversationState(userText, analysis) {
      // Update trust based on vulnerability
      if (analysis.vulnerabilitySignal) {
        this.conversationState.trustLevel += 0.5;
      }
      
      // Update phase
      const messageCount = this.shortTermMemory.length;
      if (messageCount < 3) this.conversationState.phase = 'engagement';
      else if (messageCount < 8) this.conversationState.phase = 'exploration';
      else if (messageCount < 15) this.conversationState.phase = 'processing';
      else this.conversationState.phase = 'integration';
      
      // Track emotions
      this.conversationState.lastEmotion = analysis.underlyingEmotion;
      this.conversationState.emotionalTemperature = analysis.emotionalIntensity;
      
      // Detect unspoken topics
      if (analysis.pronounRatio > 0.7) { // Lots of "I" statements
        this.conversationState.unspokenTopics.push('self_focus');
      }
      
      // Store in short-term memory
      this.shortTermMemory.push({
        text: userText,
        analysis,
        timestamp: Date.now()
      });
      
      // Keep memory at manageable size
      if (this.shortTermMemory.length > CONFIG.memoryDepth) {
        this.shortTermMemory.shift();
      }
    }

    // ================================
    // LEARNING FROM INTERACTIONS
    // ================================
    learnFromInteraction(userText, botResponse, userReactionTime = 0) {
      if (!CONFIG.learningEnabled) return;
      
      // Simple reinforcement learning
      const key = this.extractKeyPhrase(userText);
      if (key) {
        if (!this.longTermMemory.learnedResponses[key]) {
          this.longTermMemory.learnedResponses[key] = [];
        }
        
        this.longTermMemory.learnedResponses[key].push({
          response: botResponse,
          effectiveness: this.estimateEffectiveness(userReactionTime),
          timestamp: Date.now()
        });
        
        // Keep only recent learnings
        if (this.longTermMemory.learnedResponses[key].length > 10) {
          this.longTermMemory.learnedResponses[key].shift();
        }
      }
      
      localStorage.setItem('mentivio_brain', JSON.stringify(this.longTermMemory));
    }

    estimateEffectiveness(reactionTime) {
      // Quick responses often mean resonance, very slow might mean confusion
      if (reactionTime < 2000) return 0.9; // Very engaged
      if (reactionTime < 5000) return 0.7; // Thoughtful
      if (reactionTime < 10000) return 0.5; // Distracted
      return 0.3; // Disengaged
    }

    extractKeyPhrase(text) {
      const words = text.toLowerCase().split(' ');
      const keyWords = words.filter(word => 
        word.length > 4 && 
        !['about', 'really', 'actually', 'maybe', 'perhaps'].includes(word)
      );
      
      return keyWords.slice(0, 2).join('_');
    }

    // ================================
    // HELPER METHODS FOR ANALYSIS
    // ================================
    calculateIntensity(text) {
      let intensity = 1;
      
      // Exclamation points
      intensity += (text.match(/!/g) || []).length * 0.3;
      
      // Capital letters (might indicate shouting)
      const caps = text.match(/[A-Z]{3,}/g) || [];
      intensity += caps.length * 0.5;
      
      // Intensity words
      const intensifiers = /\b(extremely|incredibly|absolutely|completely|utterly)\b/gi;
      intensity += (text.match(intensifiers) || []).length * 0.4;
      
      // Very short or very long messages
      if (text.length < 20) intensity += 0.3; // Terse
      if (text.length > 200) intensity += 0.2; // Overwhelmed
      
      return Math.min(10, Math.max(1, intensity));
    }

    analyzePronouns(text) {
      const words = text.toLowerCase().split(' ');
      const iCount = words.filter(w => w === 'i' || w === "i'm" || w === "i'll").length;
      const youCount = words.filter(w => w === 'you' || w === "you're").length;
      const theyCount = words.filter(w => w === 'they' || w === 'them').length;
      
      const total = iCount + youCount + theyCount;
      return total > 0 ? iCount / total : 0;
    }

    countQualifiers(text) {
      const qualifiers = /\b(just|only|maybe|perhaps|sort of|kind of|a little)\b/gi;
      return (text.match(qualifiers) || []).length;
    }

    detectPassiveVoice(text) {
      return /\b(was|were) \w+ed\b/gi.test(text) ||
             /\b(can't|cannot|won't) \w+\b/gi.test(text);
    }

    assessRisk(text) {
      const risks = [];
      const crisisWords = /\b(suicide|kill myself|end it all|don't want to live)\b/gi;
      const selfHarm = /\b(cut|hurt myself|pain|bleed)\b/gi;
      const hopelessness = /\b(hopeless|pointless|nothing matters|why try)\b/gi;
      
      if (crisisWords.test(text)) risks.push('immediate_crisis');
      if (selfHarm.test(text)) risks.push('self_harm_risk');
      if (hopelessness.test(text)) risks.push('severe_hopelessness');
      
      return risks;
    }

    assessProtectiveFactors(text) {
      const factors = [];
      
      if (text.includes('try') || text.includes('want to feel better')) {
        factors.push('motivation_for_change');
      }
      if (text.includes('friend') || text.includes('family') || text.includes('support')) {
        factors.push('social_support');
      }
      if (text.includes('therapy') || text.includes('counselor') || text.includes('medication')) {
        factors.push('professional_help');
      }
      if (text.includes('hope') || text.includes('better') || text.includes('improve')) {
        factors.push('hope');
      }
      
      return factors;
    }

    detectVulnerability(text) {
      return text.includes('I feel') ||
             text.includes('scared to admit') ||
             text.includes('never told anyone') ||
             (this.countQualifiers(text) > 2 && text.length > 30);
    }

    detectHope(text) {
      const hopeWords = /\b(hope|better|improve|heal|recover|growth|learn)\b/gi;
      return (text.match(hopeWords) || []).length;
    }

    identifyCopingStyle(text) {
      if (text.match(/\b(avoid|ignore|distract|busy)\b/gi)) return 'avoidant';
      if (text.match(/\b(ruminate|overthink|analyze|figure out)\b/gi)) return 'ruminative';
      if (text.match(/\b(talk|share|express|vent)\b/gi)) return 'expressive';
      if (text.match(/\b(exercise|walk|breathe|meditate)\b/gi)) return 'active';
      return 'unknown';
    }

    extractBeliefs(text) {
      const beliefs = [];
      
      // Look for statements of belief
      const beliefPatterns = [
        /\b(I am|I'm) (.*?)(\.|but|and)/gi,
        /\b(people are|everyone is|no one) (.*?)(\.|but|and)/gi,
        /\b(the world is|life is) (.*?)(\.|but|and)/gi
      ];
      
      beliefPatterns.forEach(pattern => {
        const matches = text.match(pattern) || [];
        matches.forEach(match => {
          beliefs.push(match.trim());
        });
      });
      
      return beliefs;
    }
  }

  // ================================
  // ENHANCED UI WITH HUMAN TOUCHES
  // ================================
  document.body.insertAdjacentHTML('beforeend', `
  <div id="mentivio-root">
    <!-- Floating avatar with emotional expression -->
    <div id="mentivioAvatar" style="position:fixed;bottom:20px;right:20px;width:70px;height:70px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:32px;cursor:pointer;box-shadow:0 8px 25px rgba(102,126,234,0.4);z-index:10000;transition:all 0.3s">
      <span id="avatarEmoji">💭</span>
    </div>

    <!-- Main chat window -->
    <div id="mentivioWindow" style="display:none;position:fixed;bottom:100px;right:20px;width:450px;height:700px;background:white;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.15);z-index:9999;flex-direction:column;overflow:hidden;font-family:'Segoe UI',-apple-system,sans-serif">

      <!-- Header with emotional tone indicator -->
      <header style="padding:20px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;position:relative">
        <div style="display:flex;align-items:center;gap:12px">
          <div id="activeEmotion" style="width:12px;height:12px;background:#4ade80;border-radius:50%;animation:pulse 2s infinite"></div>
          <div>
            <strong style="font-size:20px">Mentivio</strong><br>
            <small style="opacity:0.9">Thinking with you • ${new Date().toLocaleDateString('en-US', { weekday: 'long' })}</small>
          </div>
        </div>
        <button id="closeMentivio" style="position:absolute;top:20px;right:20px;background:rgba(255,255,255,0.2);border:none;color:white;width:36px;height:36px;border-radius:50%;font-size:20px;cursor:pointer">×</button>
      </header>

      <!-- Connection strength indicator -->
      <div id="connectionBar" style="height:3px;background:linear-gradient(90deg,#667eea 50%,#e2e8f0 50%);transition:all 1s"></div>

      <!-- Messages container -->
      <div id="mentivioMessages" style="flex:1;padding:20px;overflow-y:auto;background:#fafafa;display:flex;flex-direction:column;gap:16px">
        <!-- Welcome message -->
        <div class="message bot" style="animation:fadeIn 0.5s">
          <div class="message-content">
            <div class="message-text">Hello. I'm here to listen and think alongside you. No judgment, just presence.</div>
            <div class="message-time">just now</div>
          </div>
        </div>
      </div>

      <!-- Typing indicator with personality -->
      <div id="typingIndicator" style="display:none;padding:0 20px 10px">
        <div style="display:flex;align-items:center;gap:8px">
          <div class="typing-dots">
            <span></span><span></span><span></span>
          </div>
          <small style="color:#718096;font-style:italic" id="typingStatus">Mentivio is thinking...</small>
        </div>
      </div>

      <!-- Input area with emotional context -->
      <div style="padding:20px;background:white;border-top:1px solid #e2e8f0">
        <div style="position:relative">
          <textarea id="mentivioInput" placeholder="What's alive in you right now?" 
            style="width:100%;padding:14px 50px 14px 14px;border:1px solid #e2e8f0;border-radius:12px;resize:none;min-height:60px;font-family:inherit;font-size:15px;background:#f8fafc"></textarea>
          <button id="sendBtn" style="position:absolute;right:10px;bottom:10px;background:#667eea;color:white;border:none;width:40px;height:40px;border-radius:10px;cursor:pointer">➤</button>
        </div>
        
        <!-- Quick emotional check-in -->
        <div id="quickEmotions" style="display:flex;gap:8px;margin-top:12px;overflow-x:auto;padding-bottom:4px">
          <button class="quick-emotion" data-emotion="overwhelmed">😰 Overwhelmed</button>
          <button class="quick-emotion" data-emotion="anxious">😟 Anxious</button>
          <button class="quick-emotion" data-emotion="sad">😔 Sad</button>
          <button class="quick-emotion" data-emotion="angry">😠 Angry</button>
          <button class="quick-emotion" data-emotion="neutral">😐 Neutral</button>
          <button class="quick-emotion" data-emotion="hopeful">😌 Hopeful</button>
          <button class="quick-emotion" data-emotion="grateful">😊 Grateful</button>
        </div>
      </div>
    </div>
  </div>

  <style>
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    
    @keyframes typingDots {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-5px); }
    }
    
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
      padding: 12px 16px;
      border-radius: 18px;
      position: relative;
    }
    
    .message.bot .message-content {
      background: white;
      border: 1px solid #e2e8f0;
      border-bottom-left-radius: 4px;
    }
    
    .message.user .message-content {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      border-bottom-right-radius: 4px;
    }
    
    .message-time {
      font-size: 11px;
      opacity: 0.6;
      margin-top: 4px;
      text-align: right;
    }
    
    .typing-dots {
      display: flex;
      gap: 4px;
    }
    
    .typing-dots span {
      width: 8px;
      height: 8px;
      background: #667eea;
      border-radius: 50%;
      animation: typingDots 1.4s infinite;
    }
    
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
    
    .quick-emotion {
      padding: 8px 12px;
      background: #f1f5f9;
      border: none;
      border-radius: 20px;
      font-size: 13px;
      white-space: nowrap;
      cursor: pointer;
      transition: all 0.2s;
    }
    
    .quick-emotion:hover {
      background: #e2e8f0;
      transform: translateY(-1px);
    }
    
    #mentivioAvatar:hover {
      transform: scale(1.1);
      box-shadow: 0 12px 30px rgba(102,126,234,0.5);
    }
    
    #mentivioWindow {
      transition: transform 0.3s, opacity 0.3s;
    }
  </style>
  `);

  // ================================
  // INITIALIZATION
  // ================================
  const ai = new NeuralMentivio();
  let isTyping = false;
  let lastInteractionTime = Date.now();
  let avatarEmotions = {
    thinking: '💭',
    listening: '👂',
    empathetic: '🤍',
    concerned: '😔',
    hopeful: '🌱',
    calm: '😌'
  };

  // ================================
  // UI INTERACTIONS
  // ================================
  const avatar = document.getElementById('mentivioAvatar');
  const window = document.getElementById('mentivioWindow');
  const messages = document.getElementById('mentivioMessages');
  const input = document.getElementById('mentivioInput');
  const sendBtn = document.getElementById('sendBtn');
  const closeBtn = document.getElementById('closeMentivio');
  const typingIndicator = document.getElementById('typingIndicator');
  const connectionBar = document.getElementById('connectionBar');
  const activeEmotion = document.getElementById('activeEmotion');

  // Toggle window
  avatar.onclick = () => {
    window.style.display = 'flex';
    window.style.opacity = '0';
    window.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
      window.style.opacity = '1';
      window.style.transform = 'translateY(0)';
      updateAvatarEmotion('listening');
      input.focus();
    }, 10);
  };

  closeBtn.onclick = () => {
    window.style.opacity = '0';
    window.style.transform = 'translateY(20px)';
    setTimeout(() => {
      window.style.display = 'none';
      updateAvatarEmotion('calm');
    }, 300);
  };

  // Send message
  function sendMessage() {
    const text = input.value.trim();
    if (!text || isTyping) return;

    // Add user message
    addMessage(text, 'user');
    input.value = '';
    
    // Update avatar
    updateAvatarEmotion('thinking');
    
    // Show typing indicator
    showTyping();
    
    // Process with AI
    setTimeout(() => {
      const analysis = ai.deepAnalyze(text);
      ai.updateConversationState(text, analysis);
      
      // Update emotional indicator
      updateEmotionalIndicator(analysis.underlyingEmotion);
      
      // Generate response
      const response = ai.generateHumanResponse(analysis, text);
      
      // Hide typing, show response
      hideTyping();
      addMessage(response, 'bot');
      updateAvatarEmotion('empathetic');
      
      // Update connection strength
      updateConnectionStrength(ai.conversationState.trustLevel);
      
      // Learn from interaction
      const reactionTime = Date.now() - lastInteractionTime;
      ai.learnFromInteraction(text, response, reactionTime);
      lastInteractionTime = Date.now();
      
      // Auto-scroll
      messages.scrollTop = messages.scrollHeight;
    }, calculateThinkingTime(text));
  }

  // Quick emotions
  document.querySelectorAll('.quick-emotion').forEach(btn => {
    btn.onclick = function() {
      const emotion = this.dataset.emotion;
      const prompts = {
        overwhelmed: "I'm feeling completely overwhelmed by everything",
        anxious: "My anxiety is really high right now",
        sad: "This deep sadness won't lift",
        angry: "I'm so angry and I don't know what to do with it",
        neutral: "I feel numb, just existing",
        hopeful: "There's a little spark of hope today",
        grateful: "I'm trying to focus on what I'm grateful for"
      };
      
      input.value = prompts[emotion];
      sendMessage();
    };
  });

  // Input events
  input.onkeypress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  sendBtn.onclick = sendMessage;

  // Auto-expand textarea
  input.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
  });

  // ================================
  // UI HELPER FUNCTIONS
  // ================================
  function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
      <div class="message-content">
        <div class="message-text">${formatMessage(text)}</div>
        <div class="message-time">${time}</div>
      </div>
    `;
    
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
  }

  function formatMessage(text) {
    // Convert line breaks
    return text.replace(/\n/g, '<br>');
  }

  function showTyping() {
    isTyping = true;
    typingIndicator.style.display = 'block';
    
    // Random typing statuses
    const statuses = [
      "Mentivio is thinking...",
      "Processing with care...",
      "Listening deeply...",
      "Considering carefully...",
      "Reflecting on this..."
    ];
    
    const statusElement = document.getElementById('typingStatus');
    statusElement.textContent = statuses[Math.floor(Math.random() * statuses.length)];
    
    messages.scrollTop = messages.scrollHeight;
  }

  function hideTyping() {
    isTyping = false;
    typingIndicator.style.display = 'none';
  }

  function calculateThinkingTime(text) {
    // More complex thoughts = longer thinking time
    const baseTime = 800;
    const complexityBonus = text.length * 8;
    const emotionBonus = text.includes('?') ? 500 : 0;
    
    return Math.min(3000, baseTime + complexityBonus + emotionBonus);
  }

  function updateAvatarEmotion(state) {
    const emoji = avatarEmotions[state] || avatarEmotions.thinking;
    document.getElementById('avatarEmoji').textContent = emoji;
    
    // Add pulse animation for certain states
    if (state === 'thinking') {
      avatar.style.animation = 'pulse 1.5s infinite';
    } else {
      avatar.style.animation = '';
    }
  }

  function updateEmotionalIndicator(emotion) {
    const colors = {
      joy: '#4ade80',
      sadness: '#3b82f6',
      anxiety: '#f59e0b',
      anger: '#ef4444',
      shame: '#8b5cf6',
      neutral: '#94a3b8'
    };
    
    activeEmotion.style.background = colors[emotion] || colors.neutral;
  }

  function updateConnectionStrength(trust) {
    const percentage = Math.min(100, trust * 20);
    connectionBar.style.background = `linear-gradient(90deg, #667eea ${percentage}%, #e2e8f0 ${percentage}%)`;
  }

  // ================================
  // AUTO-CHECK-IN SYSTEM
  // ================================
  setInterval(() => {
    const inactiveTime = Date.now() - lastInteractionTime;
    const isWindowOpen = window.style.display === 'flex';
    
    // If conversation was deep and user hasn't responded in a while
    if (inactiveTime > 120000 && ai.conversationState.trustLevel > 2 && !isTyping && isWindowOpen) {
      const checkIns = [
        "How's that sitting with you now?",
        "Where did your mind go after we spoke?",
        "Any new thoughts or feelings bubbling up?",
        "I'm still here with you in this."
      ];
      
      addMessage(checkIns[Math.floor(Math.random() * checkIns.length)], 'bot');
      updateAvatarEmotion('empathetic');
    }
  }, 30000);

  // ================================
  // INITIAL GREETING VARIATIONS
  // ================================
  setTimeout(() => {
    if (window.style.display === 'none') {
      // Optional: Gentle notification
      avatar.style.transform = 'scale(1.1)';
      setTimeout(() => avatar.style.transform = '', 500);
    }
  }, 5000);
});

// ================================
// CRISIS RESOURCE MODAL (Global)
// ================================
function showCrisisResources() {
  document.body.insertAdjacentHTML('beforeend', `
  <div id="crisisModal" style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:20000;display:flex;align-items:center;justify-content:center">
    <div style="background:white;border-radius:20px;padding:30px;max-width:500px;max-height:80vh;overflow:auto">
      <h2 style="color:#ef4444">🆘 Immediate Support Available</h2>
      <p>You're not alone. Here are people who can help right now:</p>
      
      <div style="margin:20px 0;padding:20px;background:#fef2f2;border-radius:10px">
        <h3>🇺🇸 United States</h3>
        <p><strong>988</strong> - Suicide & Crisis Lifeline (24/7)<br>
        Text HOME to 741741 - Crisis Text Line</p>
      </div>
      
      <div style="margin:20px 0;padding:20px;background:#f0f9ff;border-radius:10px">
        <h3>🌍 International</h3>
        <p><strong>116 123</strong> - Samaritans (UK)<br>
        <strong>1-833-456-4566</strong> - Canada<br>
        <strong>13 11 14</strong> - Lifeline Australia</p>
      </div>
      
      <p style="font-size:14px;color:#64748b"><em>Mentivio is an AI companion, not a substitute for professional care.</em></p>
      
      <button onclick="document.getElementById('crisisModal').remove()" style="margin-top:20px;padding:12px 24px;background:#667eea;color:white;border:none;border-radius:10px;cursor:pointer;width:100%">
        I Understand
      </button>
    </div>
  </div>
  `);
}

// ================================
// QUICK ACCESS (Global)
// ================================
if (!window.mentivioGlobal) {
  window.mentivioGlobal = {
    showCrisisHelp: showCrisisResources,
    quickCheckIn: () => {
      const feelings = ['How are you, really?', 'What needs attention today?', 'Where is your heart at?'];
      alert(feelings[Math.floor(Math.random() * feelings.length)]);
    }
  };
}