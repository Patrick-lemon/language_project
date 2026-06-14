const state = {
  sessionId: null,
  speechRecognition: null,
  isRecording: false,
  config: null,
  lastPayloadMessages: [],
  voices: [],
};

const els = {
  runtimeBadge: document.querySelector("#runtimeBadge"),
  speechBadge: document.querySelector("#speechBadge"),
  learnerName: document.querySelector("#learnerName"),
  focusMode: document.querySelector("#focusMode"),
  customTopicsField: document.querySelector("#customTopicsField"),
  customTopics: document.querySelector("#customTopics"),
  startButton: document.querySelector("#startButton"),
  updateFocusButton: document.querySelector("#updateFocusButton"),
  nextLessonButton: document.querySelector("#nextLessonButton"),
  speechLocale: document.querySelector("#speechLocale"),
  autoSpeak: document.querySelector("#autoSpeak"),
  readyButton: document.querySelector("#readyButton"),
  replayButton: document.querySelector("#replayButton"),
  transcript: document.querySelector("#transcript"),
  recordButton: document.querySelector("#recordButton"),
  sendButton: document.querySelector("#sendButton"),
  messageInput: document.querySelector("#messageInput"),
  topicLabel: document.querySelector("#topicLabel"),
  stageLabel: document.querySelector("#stageLabel"),
  targetCharacters: document.querySelector("#targetCharacters"),
  targetRomanization: document.querySelector("#targetRomanization"),
  targetEnglish: document.querySelector("#targetEnglish"),
  supportTip: document.querySelector("#supportTip"),
  quickReplies: document.querySelector("#quickReplies"),
  focusLabel: document.querySelector("#focusLabel"),
  confidenceLabel: document.querySelector("#confidenceLabel"),
  reviewQueue: document.querySelector("#reviewQueue"),
  messageTemplate: document.querySelector("#messageTemplate"),
};

function setRuntimeMessage(message) {
  els.runtimeBadge.textContent = message;
}

function normalizedLang(value) {
  return String(value || "").toLowerCase();
}

function voiceMatches(voice, wantedLang) {
  const lang = normalizedLang(voice?.lang);
  const wanted = normalizedLang(wantedLang);
  if (!lang || !wanted) {
    return false;
  }
  if (wanted === "zh-hk") {
    return lang.startsWith("zh-hk") || lang.startsWith("yue") || /cantonese/i.test(voice?.name || "");
  }
  return lang.startsWith(wanted);
}

function hasCantoneseVoice() {
  return state.voices.some((voice) => voiceMatches(voice, "zh-HK"));
}

function pickVoice(lang) {
  const exact = state.voices.find((voice) => voiceMatches(voice, lang));
  if (exact) {
    return exact;
  }
  if (normalizedLang(lang) === "en-us") {
    return state.voices.find((voice) => normalizedLang(voice.lang).startsWith("en")) || null;
  }
  return null;
}

function refreshVoiceInventory() {
  if (!("speechSynthesis" in window)) {
    state.voices = [];
    return;
  }
  state.voices = window.speechSynthesis.getVoices();
}

function updateSpeechBadge() {
  const micMessage = speechSupport()
    ? "Mic ready"
    : "Mic unavailable";
  if (!("speechSynthesis" in window)) {
    els.speechBadge.textContent = `${micMessage} | Speaker unavailable`;
    return;
  }
  const teacherVoice = hasCantoneseVoice()
    ? "Cantonese voice ready"
    : "No Cantonese voice detected";
  els.speechBadge.textContent = `${micMessage} | ${teacherVoice}`;
}

function showTranscriptNotice(title, body) {
  els.transcript.innerHTML = "";
  els.transcript.appendChild(
    createMessageElement({
      role: "system",
      text: `${title}\n\n${body}`,
      speech: `${title}. ${body}`,
    })
  );
}

async function requestJson(url, payload = null) {
  const response = await fetch(url, {
    method: payload ? "POST" : "GET",
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function createMessageElement(message) {
  const fragment = els.messageTemplate.content.cloneNode(true);
  const article = fragment.querySelector(".message");
  article.dataset.role = message.role;
  fragment.querySelector(".message-role").textContent = message.role;
  fragment.querySelector(".message-body").textContent = message.text;
  return fragment;
}

function renderTranscript(messages) {
  els.transcript.innerHTML = "";
  messages.forEach((message) => {
    els.transcript.appendChild(createMessageElement(message));
  });
  els.transcript.scrollTop = els.transcript.scrollHeight;
}

function renderQuickReplies(lesson) {
  els.quickReplies.innerHTML = "";
  const replies = Array.isArray(lesson?.target?.quick_replies) ? lesson.target.quick_replies : [];
  replies.forEach((reply) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "quick-reply-button";
    button.textContent = reply;
    button.addEventListener("click", () => {
      sendReply(reply).catch((error) => {
        setRuntimeMessage(error.message);
      });
    });
    els.quickReplies.appendChild(button);
  });
}

function updateLessonBoard(payload) {
  const lesson = payload.lesson;
  const learner = payload.learner || {};
  const target = lesson?.target || {};
  els.topicLabel.textContent = target.label || "Waiting for lesson";
  els.stageLabel.textContent = lesson?.stage_label || lesson?.stage || "-";
  els.targetCharacters.textContent = target.spoken_characters || target.characters || "-";
  els.targetRomanization.textContent = target.spoken_romanization || target.romanization || "-";
  els.targetEnglish.textContent = target.spoken_english || target.english || "-";
  els.supportTip.textContent = target.support_tip || "-";
  els.focusLabel.textContent = payload.focus || "-";
  els.confidenceLabel.textContent =
    typeof learner.confidence === "number" ? learner.confidence.toFixed(2) : "-";
  const reviewQueue = Array.isArray(learner.review_queue) ? learner.review_queue : [];
  els.reviewQueue.textContent = reviewQueue.length ? reviewQueue.join(", ") : "No active review items";
  els.nextLessonButton.disabled = !payload.awaiting_next_lesson;
  els.readyButton.disabled = !(lesson && lesson.can_advance);
  els.readyButton.textContent = lesson?.advance_label || "Show Demo Again";
  renderQuickReplies(lesson);
}

function buildSpeechQueue(message) {
  const segments = Array.isArray(message?.speech_segments) ? message.speech_segments : [];
  if (segments.length) {
    return segments;
  }
  const fallback = String(message?.speech || message?.text || "").trim();
  return fallback ? [{ text: fallback, lang: "en-US", rate: 1 }] : [];
}

function speakQueue(queue, index = 0) {
  if (index >= queue.length) {
    return;
  }
  const segment = queue[index];
  const utterance = new SpeechSynthesisUtterance(segment.text);
  utterance.lang = segment.lang || "en-US";
  utterance.rate = typeof segment.rate === "number" ? segment.rate : 1;
  const voice = pickVoice(utterance.lang);
  if (voice) {
    utterance.voice = voice;
  }
  utterance.onend = () => speakQueue(queue, index + 1);
  utterance.onerror = () => speakQueue(queue, index + 1);
  window.speechSynthesis.speak(utterance);
}

function speakTeacherMessage(messages, force = false) {
  if ((!els.autoSpeak.checked && !force) || !("speechSynthesis" in window) || !messages.length) {
    return;
  }
  const latest = messages[messages.length - 1];
  if (!latest || latest.role === "learner") {
    return;
  }
  refreshVoiceInventory();
  updateSpeechBadge();
  const queue = buildSpeechQueue(latest);
  if (!queue.length) {
    return;
  }
  window.speechSynthesis.cancel();
  speakQueue(queue);
}

function applyPayload(payload) {
  state.lastPayloadMessages = payload.messages || [];
  renderTranscript(payload.messages || []);
  updateLessonBoard(payload);
  speakTeacherMessage(payload.messages || []);
}

function updateFocusFieldVisibility() {
  const isCustom = els.focusMode.value === "custom";
  els.customTopicsField.style.display = isCustom ? "grid" : "none";
}

function speechSupport() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function configureSpeechRecognition() {
  const Recognition = speechSupport();
  if (!Recognition) {
    updateSpeechBadge();
    els.recordButton.disabled = true;
    return;
  }

  const recognition = new Recognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.maxAlternatives = 5;
  recognition.lang = els.speechLocale.value || "zh-HK";

  recognition.onstart = () => {
    state.isRecording = true;
    els.recordButton.textContent = "Listening...";
    els.recordButton.classList.add("is-recording");
  };

  recognition.onend = () => {
    state.isRecording = false;
    els.recordButton.textContent = "Start Speaking";
    els.recordButton.classList.remove("is-recording");
  };

  recognition.onresult = async (event) => {
    const alternatives = Array.from(event.results?.[0] || [])
      .map((item) => item?.transcript?.trim())
      .filter(Boolean);
    const transcript = alternatives[0];
    if (!transcript) {
      return;
    }
    els.messageInput.value = transcript;
    await sendReply(transcript, alternatives);
  };

  recognition.onerror = () => {
    state.isRecording = false;
    els.recordButton.textContent = "Start Speaking";
    els.recordButton.classList.remove("is-recording");
  };

  state.speechRecognition = recognition;
  updateSpeechBadge();
}

async function startSession() {
  if (location.protocol === "file:") {
    showTranscriptNotice(
      "Open the app through the local server",
      "Run `python web_app.py`, then open http://127.0.0.1:8765 in Chrome or Edge. Opening index.html directly will not connect to the lesson APIs."
    );
    setRuntimeMessage("This page was opened directly from disk. Start the local server first.");
    return;
  }
  const payload = await requestJson("/api/session/start", {
    learner_name: els.learnerName.value.trim() || "Student",
    focus_mode: els.focusMode.value,
    custom_topics: els.customTopics.value.trim(),
  });
  state.sessionId = payload.session_id;
  applyPayload(payload);
}

async function sendReply(textOverride = null, alternatives = null) {
  if (!state.sessionId) {
    return;
  }
  const learnerText = (textOverride ?? els.messageInput.value).trim();
  if (!learnerText) {
    return;
  }
  const payload = await requestJson("/api/session/respond", {
    session_id: state.sessionId,
    learner_text: learnerText,
    alternatives: Array.isArray(alternatives) ? alternatives : undefined,
  });
  els.messageInput.value = "";
  applyPayload(payload);
}

async function updateFocus() {
  if (!state.sessionId) {
    return;
  }
  const payload = await requestJson("/api/session/focus", {
    session_id: state.sessionId,
    focus_mode: els.focusMode.value,
    custom_topics: els.customTopics.value.trim(),
  });
  applyPayload(payload);
}

async function nextLesson() {
  if (!state.sessionId) {
    return;
  }
  const payload = await requestJson("/api/session/next", {
    session_id: state.sessionId,
  });
  applyPayload(payload);
}

async function advanceLesson() {
  if (!state.sessionId) {
    return;
  }
  const payload = await requestJson("/api/session/advance", {
    session_id: state.sessionId,
  });
  applyPayload(payload);
}

function replayTeacher() {
  if (!state.lastPayloadMessages.length) {
    return;
  }
  speakTeacherMessage(state.lastPayloadMessages, true);
}

function toggleRecording() {
  if (!state.speechRecognition) {
    return;
  }
  if (state.isRecording) {
    state.speechRecognition.stop();
    return;
  }
  state.speechRecognition.lang = els.speechLocale.value || "zh-HK";
  state.speechRecognition.start();
}

async function init() {
  if (location.protocol === "file:") {
    setRuntimeMessage("Opened from disk. Start `python web_app.py` and use http://127.0.0.1:8765.");
    refreshVoiceInventory();
    updateSpeechBadge();
    showTranscriptNotice(
      "Local server required",
      "This interface needs the Python web server. In PowerShell run `python web_app.py`, then open http://127.0.0.1:8765."
    );
    updateFocusFieldVisibility();
    configureSpeechRecognition();
    return;
  }

  const config = await requestJson("/api/config");
  state.config = config;
  setRuntimeMessage(config.runtime_mode);
  refreshVoiceInventory();
  updateSpeechBadge();

  config.focus_modes.forEach((mode) => {
    const option = document.createElement("option");
    option.value = mode;
    option.textContent = mode;
    els.focusMode.appendChild(option);
  });
  els.focusMode.value = "balanced";

  config.speech_locales.forEach((locale) => {
    const option = document.createElement("option");
    option.value = locale.value;
    option.textContent = locale.label;
    els.speechLocale.appendChild(option);
  });
  els.speechLocale.value = "zh-HK";

  updateFocusFieldVisibility();
  configureSpeechRecognition();
  if ("speechSynthesis" in window) {
    window.speechSynthesis.onvoiceschanged = () => {
      refreshVoiceInventory();
      updateSpeechBadge();
    };
  }
}

els.focusMode.addEventListener("change", updateFocusFieldVisibility);
els.startButton.addEventListener("click", () => {
  startSession().catch((error) => {
    setRuntimeMessage(error.message);
  });
});
els.sendButton.addEventListener("click", () => {
  sendReply().catch((error) => {
    setRuntimeMessage(error.message);
  });
});
els.updateFocusButton.addEventListener("click", () => {
  updateFocus().catch((error) => {
    setRuntimeMessage(error.message);
  });
});
els.readyButton.addEventListener("click", () => {
  advanceLesson().catch((error) => {
    setRuntimeMessage(error.message);
  });
});
els.replayButton.addEventListener("click", replayTeacher);
els.nextLessonButton.addEventListener("click", () => {
  nextLesson().catch((error) => {
    setRuntimeMessage(error.message);
  });
});
els.recordButton.addEventListener("click", toggleRecording);
els.messageInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    sendReply().catch((error) => {
      setRuntimeMessage(error.message);
    });
  }
});

init().catch((error) => {
  setRuntimeMessage(error.message);
  showTranscriptNotice(
    "Could not reach the lesson server",
    "Start `python web_app.py` in the project folder, then reload this page. If the server is already running, make sure you opened http://127.0.0.1:8765."
  );
});
