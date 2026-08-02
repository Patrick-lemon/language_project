const translations = {
  en: {
    "eyebrow": "Voice-First Cantonese Tutor",
    "hero-title": "Talk to a tutor, with the transcript on screen.",
    "hero-copy": "The tutor still follows its own lesson system, but now it teaches by speaking first, modeling the line, and then talking with you in a browser conversation.",
    "loading-runtime": "Loading runtime...",
    "checking-speech": "Checking speech support...",
    "start-session": "Start Session",
    "learner-name": "Learner Name",
    "focus-mode": "Focus Mode",
    "elective-topics": "Elective Topics",
    "start-button": "Start Conversation",
    "hint-1": "Use the same learner name to resume saved progress. Electives are mixed into the suggested roadmap when they fit your level.",
    "lesson-board": "Lesson Board",
    "current-topic": "Current Topic",
    "not-started": "Not started",
    "flow": "Flow",
    "spoken-line": "Spoken Line",
    "focus": "Focus",
    "confidence": "Confidence",
    "review-queue": "Review Queue",
    "voice-setup": "Voice Setup",
    "speech-recognition": "Speech Recognition",
    "auto-play-teacher": "Auto-play teacher voice",
    "show-demo": "Show Demo Again",
    "replay-teacher": "Replay Teacher",
    "apply-focus": "Apply Current Focus",
    "next-lesson": "Next Lesson",
    "hint-2": "Speak naturally. If you want the tutor to model it again, just say \"repeat again\". If you want to move on, say \"next lesson\".",
    "start-speaking": "Start Speaking",
    "reply-placeholder": "Reply by voice, or type here if the mic misses you...",
    "reply-button": "Reply",
  },
  zh: {
    "eyebrow": "语音优先粤语导师",
    "hero-title": "与导师交谈，屏幕上显示记录。",
    "hero-copy": "导师仍遵循自己的课程系统，但现在先通过说话教学，示范语句，然后与您进行浏览器对话。",
    "loading-runtime": "加载中...",
    "checking-speech": "检查语音支持...",
    "start-session": "开始课程",
    "learner-name": "学习者名称",
    "focus-mode": "学习模式",
    "elective-topics": "选修主题",
    "start-button": "开始对话",
    "hint-1": "使用相同的学习者名称可恢复已保存的进度。选修科目会根据您的水平混入建议的学习路线。",
    "lesson-board": "课程板",
    "current-topic": "当前主题",
    "not-started": "未开始",
    "flow": "阶段",
    "spoken-line": "学习语句",
    "focus": "重点",
    "confidence": "掌握度",
    "review-queue": "复习队列",
    "voice-setup": "语音设置",
    "speech-recognition": "语音识别",
    "auto-play-teacher": "自动播放导师语音",
    "show-demo": "再次显示演示",
    "replay-teacher": "重播导师",
    "apply-focus": "应用当前焦点",
    "next-lesson": "下一课",
    "hint-2": "自然说话。如果您希望导师再次示范，只需说'repeat again'。如果您想继续，说'next lesson'。",
    "start-speaking": "开始说话",
    "reply-placeholder": "用语音回复，或在麦克风无法识别时在此输入...",
    "reply-button": "回复",
  }
};

function t(key, lang = 'en') {
  return translations[lang]?.[key] || translations.en[key] || key;
}

function setLanguage(lang) {
  localStorage.setItem('tutorLanguage', lang);
  applyTranslations(lang);
}

function getLanguage() {
  return localStorage.getItem('tutorLanguage') || 'en';
}

function applyTranslations(lang) {
  // Update all elements with data-i18n attribute
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      el.placeholder = t(key, lang);
    } else {
      el.textContent = t(key, lang);
    }
  });

  // Update select options for focus mode
  const focusSelect = document.querySelector('#focusMode');
  if (focusSelect && focusSelect.options.length > 0) {
    const focusTranslations = {
      en: { balanced: 'Balanced', 'survival-only': 'Survival Only', questions: 'Questions', scenarios: 'Scenarios' },
      zh: { balanced: '均衡', 'survival-only': '生存必备', questions: '问题', scenarios: '情景' }
    };
    Array.from(focusSelect.options).forEach(opt => {
      const value = opt.value;
      opt.textContent = focusTranslations[lang]?.[value] || opt.textContent;
    });
  }

  // Update language toggle button
  const langButton = document.querySelector('#languageToggle');
  if (langButton) {
    langButton.textContent = lang === 'en' ? '中文' : 'English';
  }

  // Store current language
  document.documentElement.lang = lang;
}
