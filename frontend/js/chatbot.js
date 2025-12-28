// ================================
// Mentivio — Advanced AI Mental Health Companion
// ================================
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
    const CONFIG = {
      name: "Mentivio",
      persona: "empathic_expert",
      memoryDepth: 20,
      learningEnabled: true,
      useMetaphors: true,
      empathyLevel: 9
    };

    // ================================
    // ADVANCED NEURAL SIMULATION
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
          phase: 'engagement',
          trustLevel: 0,
          emotionalTemperature: 0,
          lastEmotion: 'neutral',
          unspokenTopics: []
        };
      }

      // [All AI methods remain the same as your original code - keeping it concise]
      deepAnalyze(text) {
        return {
          surfaceEmotion: this.detectSurfaceEmotion(text),
          underlyingEmotion: this.inferUnderlyingEmotion(text),
          emotionalIntensity: this.calculateIntensity(text),
          cognitiveDistortions: this.detectDistortions(text),
          coreBeliefs: this.extractBeliefs(text),
          copingStyle: this.identifyCopingStyle(text),
          pronounRatio: this.analyzePronouns(text),
          qualifierCount: this.countQualifiers(text),
          passiveLanguage: this.detectPassiveVoice(text),
          riskFactors: this.assessRisk(text),
          protectiveFactors: this.assessProtectiveFactors(text),
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
        
        if (text.match(/\b(always|never|every|nobody|everyone)\b/gi)) {
          distortions.push('black_white_thinking');
        }
        
        if (text.match(/\b(disaster|worst|awful|terrible|end of the world)\b/gi)) {
          distortions.push('catastrophizing');
        }
        
        if (text.match(/\b(they think|he believes|she feels|people say)\b/gi)) {
          distortions.push('mind_reading');
        }
        
        if (text.match(/\b(should|must|have to|ought to)\b/gi)) {
          distortions.push('should_statements');
        }
        
        return distortions;
      }

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
          archetype,
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
        
        if (analysis.qualifierCount > 3 || analysis.vulnerabilitySignal) {
          return affirmations[Math.floor(Math.random() * affirmations.length)];
        }
        
        return null;
      }

      assembleResponse(architecture, userText, state) {
        let response = '';
        
        if (Math.random() > 0.7 && state.trustLevel > 2) {
          const fillers = ["Hmm", "Let me sit with that", "I'm thinking", "You know"];
          response += `<em>${fillers[Math.floor(Math.random() * fillers.length)]}...</em><br><br>`;
        }
        
        architecture.components.forEach((component, index) => {
          if (index > 0) {
            const connectors = [" ", "<br><br>", " I wonder... ", " Maybe... "];
            response += connectors[Math.min(index, connectors.length - 1)];
          }
          
          if (index === 0 && Math.random() > 0.5 && userText.length < 100) {
            response += this.paraphraseWithEmpathy(userText) + " ";
          }
          
          response += component;
        });
        
        if (state.trustLevel > 1) {
          const closers = ["", " I'm here.", " Take your time.", " No rush."];
          if (Math.random() > 0.6) {
            response += closers[Math.floor(Math.random() * closers.length)];
          }
        }
        
        return response;
      }

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

      updateConversationState(userText, analysis) {
        if (analysis.vulnerabilitySignal) {
          this.conversationState.trustLevel += 0.5;
        }
        
        const messageCount = this.shortTermMemory.length;
        if (messageCount < 3) this.conversationState.phase = 'engagement';
        else if (messageCount < 8) this.conversationState.phase = 'exploration';
        else if (messageCount < 15) this.conversationState.phase = 'processing';
        else this.conversationState.phase = 'integration';
        
        this.conversationState.lastEmotion = analysis.underlyingEmotion;
        this.conversationState.emotionalTemperature = analysis.emotionalIntensity;
        
        if (analysis.pronounRatio > 0.7) {
          this.conversationState.unspokenTopics.push('self_focus');
        }
        
        this.shortTermMemory.push({
          text: userText,
          analysis,
          timestamp: Date.now()
        });
        
        if (this.shortTermMemory.length > CONFIG.memoryDepth) {
          this.shortTermMemory.shift();
        }
      }

      learnFromInteraction(userText, botResponse, userReactionTime = 0) {
        if (!CONFIG.learningEnabled) return;
        
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
          
          if (this.longTermMemory.learnedResponses[key].length > 10) {
            this.longTermMemory.learnedResponses[key].shift();
          }
        }
        
        localStorage.setItem('mentivio_brain', JSON.stringify(this.longTermMemory));
      }

      estimateEffectiveness(reactionTime) {
        if (reactionTime < 2000) return 0.9;
        if (reactionTime < 5000) return 0.7;
        if (reactionTime < 10000) return 0.5;
        return 0.3;
      }

      extractKeyPhrase(text) {
        const words = text.toLowerCase().split(' ');
        const keyWords = words.filter(word => 
          word.length > 4 && 
          !['about', 'really', 'actually', 'maybe', 'perhaps'].includes(word)
        );
        
        return keyWords.slice(0, 2).join('_');
      }

      calculateIntensity(text) {
        let intensity = 1;
        
        intensity += (text.match(/!/g) || []).length * 0.3;
        
        const caps = text.match(/[A-Z]{3,}/g) || [];
        intensity += caps.length * 0.5;
        
        const intensifiers = /\b(extremely|incredibly|absolutely|completely|utterly)\b/gi;
        intensity += (text.match(intensifiers) || []).length * 0.4;
        
        if (text.length < 20) intensity += 0.3;
        if (text.length > 200) intensity += 0.2;
        
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

      determinePacing(analysis) {
        if (analysis.emotionalIntensity > 7) return 'slow';
        if (analysis.emotionalIntensity < 3) return 'moderate';
        return 'normal';
      }

      determineTone(analysis) {
        if (analysis.underlyingEmotion === 'shame') return 'gentle';
        if (analysis.riskFactors.length > 0) return 'grounded';
        if (analysis.vulnerabilitySignal) return 'tender';
        return 'warm';
      }
    }

    // ================================
    // SIMPLE, RESPONSIVE CHATBOT UI
    // ================================
    // Create and inject the chatbot HTML
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
              <strong class="mentivio-title">Mentivio (Demo)</strong>
              <small id="currentDay" class="mentivio-subtitle">Thinking with you</small>
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
              <div class="message-text">Hello. I'm here to listen and think alongside you. No judgment, just presence.</div>
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
            <textarea id="mentivioInput" placeholder="What's on your mind?" class="message-input" rows="1"></textarea>
            <button id="sendBtn" class="send-btn" aria-label="Send message">➤</button>
          </div>
          
          <!-- Quick emotional check-in -->
          <div id="quickEmotions" class="quick-emotions">
            <button class="quick-emotion" data-emotion="overwhelmed">😰 Overwhelmed</button>
            <button class="quick-emotion" data-emotion="anxious">😟 Anxious</button>
            <button class="quick-emotion" data-emotion="sad">😔 Sad</button>
            <button class="quick-emotion" data-emotion="angry">😠 Angry</button>
            <button class="quick-emotion" data-emotion="neutral">😐 Neutral</button>
          </div>
        </div>
      </div>
    </div>`;

    document.body.insertAdjacentHTML('beforeend', mentivioHTML);

    // ================================
    // ADD FIXED + RESPONSIVE CSS
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
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 28px;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
        z-index: 10000;
        transition: all 0.3s ease;
        border: 3px solid white;
      }
      
      #mentivioAvatar:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 30px rgba(102, 126, 234, 0.6);
      }
      
      /* DESKTOP VIEW - Fixed size always */
      #mentivioWindow {
        position: fixed;
        display: none;
        flex-direction: column;
        background: white;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        z-index: 9999;
        overflow: hidden;
        width: 380px; /* Fixed width for desktop */
        height: 600px; /* Fixed height for desktop */
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
        background: linear-gradient(135deg, #667eea, #764ba2);
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
        background: linear-gradient(90deg, #667eea 0%, #e2e8f0 100%);
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
      }
      
      .message.user .message-content {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-bottom-right-radius: 6px;
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
        background: #667eea;
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
        padding: 12px 45px 12px 12px;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        resize: none;
        min-height: 20px;
        max-height: 80px;
        font-family: inherit;
        font-size: 14px;
        background: #f8fafc;
        box-sizing: border-box;
        line-height: 1.4;
      }
      
      .message-input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
      }
      
      .send-btn {
        position: absolute;
        right: 8px;
        bottom: 8px;
        background: #667eea;
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
        background: #5a6fd8;
      }
      
      /* Quick Emotions */
      .quick-emotions {
        display: flex;
        justify-content: space-between;
        gap: 6px;
        overflow-x: auto;
        padding-bottom: 2px;
        -webkit-overflow-scrolling: touch;
      }
      
      .quick-emotions::-webkit-scrollbar {
        height: 2px;
      }
      
      .quick-emotions::-webkit-scrollbar-track {
        background: #f1f5f9;
      }
      
      .quick-emotions::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 2px;
      }
      
      .quick-emotion {
        padding: 7px 10px;
        background: #f1f5f9;
        border: none;
        border-radius: 16px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s;
        flex-shrink: 0;
        white-space: nowrap;
      }
      
      .quick-emotion:hover {
        background: #e2e8f0;
        transform: translateY(-1px);
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
      
      /* Scrollbar Styling */
      .messages-container::-webkit-scrollbar {
        width: 5px;
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
      }
    `;
    
    document.head.appendChild(style);

    // ================================
    // INITIALIZATION
    // ================================
    const ai = new NeuralMentivio();
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
      currentDay.textContent = `Thinking with you • ${day}`;
    }

    // ================================
    // SIMPLE WINDOW MANAGEMENT
    // ================================
    function showWindow() {
      if (isWindowOpen) return;
      
      isWindowOpen = true;
      
      // Lock body scroll on mobile
      if (window.innerWidth <= 768) {
        document.body.classList.add('mentivio-open');
      }
      
      // Show window with animation
      windowEl.classList.add('open');
      
      // Focus input
      setTimeout(() => {
        input.focus();
      }, 100);
      
      // Update avatar emoji
      updateAvatarEmoji('listening');
    }
    
    function hideWindow() {
      if (!isWindowOpen) return;
      
      isWindowOpen = false;
      
      // Remove open class
      windowEl.classList.remove('open');
      
      // Remove body scroll lock
      document.body.classList.remove('mentivio-open');
      
      // Update avatar emoji
      updateAvatarEmoji('calm');
    }

    // Toggle window
    avatar.addEventListener('click', showWindow);
    closeBtn.addEventListener('click', hideWindow);

    // Close on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isWindowOpen) {
        hideWindow();
      }
    });

    // ================================
    // MESSAGE HANDLING
    // ================================
    function sendMessage() {
      const text = input.value.trim();
      if (!text || isTyping) return;

      // Add user message
      addMessage(text, 'user');
      input.value = '';
      resetInputHeight();
      
      // Update avatar
      updateAvatarEmoji('thinking');
      
      // Show typing indicator
      showTyping();
      
      // Simulate thinking time
      setTimeout(() => {
        try {
          const analysis = ai.deepAnalyze(text);
          ai.updateConversationState(text, analysis);
          
          // Update emotional indicator
          updateEmotionalIndicator(analysis.underlyingEmotion);
          
          // Generate response
          const response = ai.generateHumanResponse(analysis, text);
          
          // Hide typing and show response
          hideTyping();
          addMessage(response, 'bot');
          updateAvatarEmoji('empathetic');
          
          // Update connection strength
          updateConnectionStrength(ai.conversationState.trustLevel);
          
          // Learn from interaction
          const reactionTime = Date.now() - lastInteractionTime;
          ai.learnFromInteraction(text, response, reactionTime);
          lastInteractionTime = Date.now();
          
          // Auto-scroll
          scrollToBottom();
        } catch (error) {
          console.error('Error generating response:', error);
          hideTyping();
          addMessage("I'm here with you. Let's continue when you're ready.", 'bot');
          updateAvatarEmoji('calm');
        }
      }, 800 + Math.min(text.length * 3, 1000));
    }

    // Quick emotions
    document.querySelectorAll('.quick-emotion').forEach(btn => {
      btn.addEventListener('click', function() {
        const emotion = this.dataset.emotion;
        const prompts = {
          overwhelmed: "I'm feeling completely overwhelmed",
          anxious: "I'm really anxious right now",
          sad: "I'm feeling sad",
          angry: "I'm angry",
          neutral: "I feel neutral"
        };
        
        input.value = prompts[emotion] || "I'm feeling " + emotion;
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
      // Simple line break conversion
      return text.replace(/\n/g, '<br>');
    }

    function resetInputHeight() {
      input.style.height = 'auto';
    }

    function showTyping() {
      isTyping = true;
      typingIndicator.style.display = 'block';
      
      const statuses = [
        "Mentivio is thinking...",
        "Processing with care...",
        "Listening deeply..."
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
        calm: '😌'
      };
      
      const emoji = emojis[state] || '💭';
      document.getElementById('avatarEmoji').textContent = emoji;
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
      
      if (activeEmotion) {
        activeEmotion.style.background = colors[emotion] || colors.neutral;
      }
    }

    function updateConnectionStrength(trust) {
      const percentage = Math.min(100, trust * 15);
      if (connectionBar) {
        connectionBar.style.background = `linear-gradient(90deg, #667eea ${percentage}%, #e2e8f0 ${percentage}%)`;
      }
    }

    function scrollToBottom() {
      messages.scrollTop = messages.scrollHeight;
    }

    // ================================
    // INITIAL PULSE ANIMATION
    // ================================
    setTimeout(() => {
      if (!isWindowOpen) {
        avatar.style.transform = 'scale(1.1)';
        setTimeout(() => {
          avatar.style.transform = '';
        }, 600);
      }
    }, 2000);

    // ================================
    // HANDLE ORIENTATION CHANGES
    // ================================
    window.addEventListener('resize', () => {
      // Just update day on resize
      updateDay();
    });
  }

  // ================================
  // GLOBAL CRISIS FUNCTION
  // ================================
  window.showCrisisResources = function() {
    const modalHTML = `
    <div id="mentivio-crisis-modal" style="
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0,0,0,0.9);
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
        <h2 style="color: #ef4444; margin-top: 0; font-size: 20px; text-align: center;">🆘 Immediate Support</h2>
        <p style="color: #4b5563; margin-bottom: 20px; font-size: 14px; text-align: center;">You're not alone. Help is available:</p>
        
        <div style="margin: 15px 0; padding: 15px; background: #fef2f2; border-radius: 10px;">
          <h3 style="color: #dc2626; margin-top: 0; font-size: 16px;">🇺🇸 United States</h3>
          <p style="margin: 8px 0; font-size: 14px;">
            <strong style="color: #111827;">988</strong> - Crisis Lifeline (24/7)<br>
            <strong style="color: #111827;">741741</strong> - Crisis Text Line
          </p>
        </div>
        
        <div style="margin: 15px 0; padding: 15px; background: #f0f9ff; border-radius: 10px;">
          <h3 style="color: #0369a1; margin-top: 0; font-size: 16px;">🌍 International</h3>
          <p style="margin: 8px 0; font-size: 14px;">
            <strong style="color: #111827;">116 123</strong> - Samaritans (UK)<br>
            <strong style="color: #111827;">13 11 14</strong> - Lifeline Australia
          </p>
        </div>
        
        <p style="font-size: 12px; color: #6b7280; font-style: italic; margin: 15px 0; text-align: center;">
          Mentivio is an AI companion, not a substitute for professional care.
        </p>
        
        <button onclick="document.getElementById('mentivio-crisis-modal').remove()" style="
          margin-top: 15px;
          padding: 12px 20px;
          background: #667eea;
          color: white;
          border: none;
          border-radius: 10px;
          cursor: pointer;
          width: 100%;
          font-size: 14px;
          font-weight: 600;
          transition: background 0.3s;
        ">
          I Understand
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
      showCrisisHelp: window.showCrisisResources,
      quickCheckIn: () => {
        const feelings = ['How are you, really?', 'What needs attention today?', 'Where is your heart at?'];
        const feeling = feelings[Math.floor(Math.random() * feelings.length)];
        alert(feeling);
      }
    };
  }
})();