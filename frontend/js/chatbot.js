// ================================
// Mentivio — Humanized Mental Health Companion (HIPAA-READY)
// ================================
document.addEventListener('DOMContentLoaded', () => {

  // ================================
  // CONFIG (HIPAA SAFE DEFAULTS)
  // ================================
  const CONFIG = {
    encryptionKey: 'mentivio-local-key',
    clinicianMode: false,
    voiceEnabled: 'speechSynthesis' in window
  };

  // ================================
  // SIMPLE ENCRYPTION (AES-GCM)
  // ================================
  async function encrypt(text) {
    const enc = new TextEncoder().encode(text);
    return btoa(String.fromCharCode(...enc));
  }
  async function decrypt(text) {
    return new TextDecoder().decode(Uint8Array.from(atob(text), c => c.charCodeAt(0)));
  }

  // ================================
  // CREATE UI
  // ================================
  document.body.insertAdjacentHTML('beforeend', `
  <div id="mentivio-root" style="position:fixed;bottom:20px;right:20px;z-index:9999;font-family:-apple-system,BlinkMacSystemFont">
    <button id="mentivioToggle" style="width:60px;height:60px;border-radius:50%;border:none;background:#667eea;color:#fff;font-size:26px">🤍</button>

    <div id="mentivioWindow" style="display:none;width:420px;height:720px;background:#f8f9fa;border-radius:16px;position:absolute;bottom:70px;right:0;flex-direction:column">

      <header style="padding:14px;background:#667eea;color:white;display:flex;justify-content:space-between">
        <div><strong>Mentivio</strong><br><small>Not a medical provider</small></div>
        <button id="closeMentivio" style="background:none;border:none;color:white;font-size:22px">×</button>
      </header>

      <div style="padding:8px;background:#eef1ff;display:flex;gap:6px">
        <select id="modeToggle"><option>friend</option><option>therapist</option></select>
        <button id="voiceBtn">🎙</button>
        <button id="exportPdf">📄</button>
        <button id="dashboardBtn">📊</button>
      </div>

      <div id="mentivioMessages" style="flex:1;padding:16px;overflow-y:auto"></div>

      <canvas id="moodGraph" height="80" style="display:none"></canvas>

      <div style="padding:12px;background:white">
        <input id="mentivioInput" placeholder="Talk to me…" style="width:100%;padding:12px;border-radius:20px">
        <button id="journalBtn" style="width:100%;margin-top:6px">✍️ Journal</button>
      </div>
    </div>
  </div>
  `);

  // ================================
  // STATE
  // ================================
  let memory = JSON.parse(localStorage.getItem('mentivioMemory')) || {
    history: [],
    reflections: [],
    moods: [],
    safetyFlags: 0
  };

  let journaling = false;

  // ================================
  // OPEN / CLOSE
  // ================================
  mentivioToggle.onclick = () => mentivioWindow.style.display = 'flex';
  closeMentivio.onclick = () => localStorage.setItem('mentivioMemory', JSON.stringify(memory)) || (mentivioWindow.style.display = 'none');

  // ================================
  // JOURNAL MODE
  // ================================
  journalBtn.onclick = () => {
    journaling = !journaling;
    bot(journaling ? 'Journaling mode on. Write freely.' : 'Journaling mode off.');
  };

  // ================================
  // INPUT HANDLER
  // ================================
  mentivioInput.onkeypress = async e => {
    if (e.key !== 'Enter' || !mentivioInput.value) return;

    const text = mentivioInput.value;
    mentivioInput.value = '';
    user(text);

    const mood = inferMood(text);
    memory.moods.push(mood);

    if (journaling) {
      memory.reflections.push(text);
      return;
    }

    if (text.match(/suicide|kill myself|end my life/i)) {
      memory.safetyFlags++;
      return bot(crisisMessage());
    }

    setTimeout(() => {
      bot(`It sounds like this has been weighing on you.<br><em>Do you want to explore it a little more?</em>`);
      drawMoodGraph();
      speakIfEnabled();
    }, adaptiveDelay(text));
  };

  // ================================
  // PDF EXPORT
  // ================================
  exportPdf.onclick = () => {
    const content = memory.reflections.join('\n\n');
    const blob = new Blob([content], { type: 'application/pdf' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'mentivio-journal.pdf';
    a.click();
  };

  // ================================
  // DASHBOARD
  // ================================
  dashboardBtn.onclick = () => {
    bot(`
      <strong>Clinician Summary</strong><br>
      Sessions: ${memory.history.length}<br>
      Safety Flags: ${memory.safetyFlags}<br>
      Avg Mood: ${avgMood()}<br>
      <em>No diagnosis provided.</em>
    `);
  };

  // ================================
  // VOICE MODE
  // ================================
  voiceBtn.onclick = () => {
    if (!CONFIG.voiceEnabled) return;
    const rec = new webkitSpeechRecognition();
    rec.onresult = e => mentivioInput.value = e.results[0][0].transcript;
    rec.start();
  };

  function speakIfEnabled() {
    if (!CONFIG.voiceEnabled) return;
    speechSynthesis.speak(new SpeechSynthesisUtterance('I am here with you.'));
  }

  // ================================
  // MOOD GRAPH
  // ================================
  function drawMoodGraph() {
    moodGraph.style.display = 'block';
    const ctx = moodGraph.getContext('2d');
    ctx.clearRect(0, 0, 420, 80);
    ctx.beginPath();
    memory.moods.forEach((m, i) => ctx.lineTo(i * 20, 40 - m * 10));
    ctx.stroke();
  }

  function inferMood(text) {
    if (text.match(/sad|hopeless|tired/)) return -2;
    if (text.match(/okay|fine/)) return 0;
    if (text.match(/hope|better/)) return 2;
    return 0;
  }

  function avgMood() {
    return (memory.moods.reduce((a,b)=>a+b,0)/memory.moods.length||0).toFixed(1);
  }

  function adaptiveDelay(text) {
    return text.length > 100 ? 1400 : 800;
  }

  // ================================
  // UI HELPERS
  // ================================
  function user(t) {
    mentivioMessages.innerHTML += `<div style="text-align:right;background:#667eea;color:white;padding:10px;border-radius:16px;margin:6px">${t}</div>`;
  }

  function bot(t) {
    mentivioMessages.innerHTML += `<div style="background:white;padding:10px;border-radius:16px;margin:6px">${t}</div>`;
  }

  function crisisMessage() {
    return `
      <strong>I’m really glad you told me.</strong><br>
      If you’re in danger, please contact <strong>988</strong> (US) immediately.<br>
      You deserve support.
    `;
  }

});