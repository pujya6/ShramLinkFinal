// Test-only simulation. No physical microphone or pronunciation verification.
window.__speech = {
  last: null,
  spoken: [],
  starts: 0,
  startError: false,
  ttsError: false,
  noVoices: false,
  holdTTS: false,
  holdEnd: false,
  overlaps: [],
  activeMic: false,
  voices: [
    { name: "Mock Hindi voice", lang: "hi-IN", voiceURI: "mock-hi" },
    { name: "Second Hindi voice", lang: "hi_IN", voiceURI: "mock-hi-two" },
  ],
  voiceListeners: [],
};
class MockRecognition {
  start() {
    if (window.__speech.startError)
      throw new Error("Mock microphone unavailable");
    if (window.speechSynthesis.speaking || window.__speech.activeMic)
      window.__speech.overlaps.push("recognition");
    window.__speech.last = this;
    window.__speech.starts++;
    window.__speech.activeMic = true;
    this.onstart?.();
  }
  abort() {
    if (!window.__speech.holdEnd)
      queueMicrotask(() => {
        window.__speech.activeMic = false;
        this.onend?.();
      });
  }
}
Object.defineProperty(window, "SpeechRecognition", {
  configurable: true,
  value: MockRecognition,
});
Object.defineProperty(window, "webkitSpeechRecognition", {
  configurable: true,
  value: undefined,
});
Object.defineProperty(window, "SpeechSynthesisUtterance", {
  configurable: true,
  value: class {
    constructor(text) {
      this.text = text;
    }
  },
});
Object.defineProperty(window, "speechSynthesis", {
  configurable: true,
  value: {
    speaking: false,
    pending: false,
    getVoices() {
      return window.__speech.noVoices
        ? [{ name: "English only", lang: "en-US" }]
        : window.__speech.voices;
    },
    cancel() {
      this.speaking = false;
      this.pending = false;
    },
    addEventListener(name, cb) {
      if (name === "voiceschanged") window.__speech.voiceListeners.push(cb);
    },
    speak(utterance) {
      if (window.__speech.activeMic) window.__speech.overlaps.push("synthesis");
      this.speaking = true;
      window.__speech.utterance = utterance;
      window.__speech.spoken.push({
        text: utterance.text,
        lang: utterance.lang,
        voice: utterance.voice?.name,
      });
      if (!window.__speech.holdTTS)
        queueMicrotask(() => window.__speech.endTTS(utterance));
    },
  },
});
window.__speech.endTTS = (utterance = window.__speech.utterance) => {
  window.speechSynthesis.speaking = false;
  if (window.__speech.ttsError)
    utterance.onerror?.({ error: "synthesis-failed" });
  else utterance.onend?.();
};
window.__speech.result = (text, confidence = 0.9) => {
  const result = [{ transcript: text, confidence }];
  result.isFinal = true;
  window.__speech.last.onresult({ resultIndex: 0, results: [result] });
};
window.__speech.error = (code) => window.__speech.last.onerror({ error: code });
window.__speech.voicesChanged = () =>
  window.__speech.voiceListeners.forEach((cb) => cb());
