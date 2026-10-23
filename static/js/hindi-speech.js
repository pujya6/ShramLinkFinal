/* Shared cancellable Hindi synthesis. A language tag is a candidate, not a
 * pronunciation guarantee. The user must listen to the preflight on each device. */
(function (root) {
  "use strict";
  const TEST = "नमस्ते। आपका नाम क्या है?";
  const RETROFLEX = "टमाटर। ठंडा पानी। डिब्बा। ढक्कन। निर्माण।";
  class HindiSpeech {
    constructor(win = root) {
      this.win = win;
      this.synth = win.speechSynthesis;
      this.version = 0;
      this.finish = null;
      this.selected = "";
      this.listeners = new Set();
      this.synth?.addEventListener("voiceschanged", () => this.refresh());
      this.refresh();
    }
    key(v) {
      return v.voiceURI || `${v.name}|${v.lang}`;
    }
    refresh() {
      try {
        this.voices = (this.synth?.getVoices() || []).filter((v) =>
          /^hi(?:[-_]|$)/i.test(v.lang),
        );
      } catch {
        this.voices = [];
      }
      if (!this.voices.some((v) => this.key(v) === this.selected))
        this.selected = this.voices.length ? this.key(this.voices[0]) : "";
      for (const callback of this.listeners) callback(this.voices);
      return this.voices;
    }
    async ready() {
      if (!this.synth || !this.win.SpeechSynthesisUtterance) return false;
      if (this.refresh().length) return true;
      // Bounded polling also covers engines that fail to dispatch voiceschanged.
      for (let n = 0; n < 10; n++) {
        await new Promise((r) => this.win.setTimeout(r, 250));
        if (this.refresh().length) return true;
      }
      return false;
    }
    cancel() {
      this.version++;
      if (this.finish) this.finish({ ok: false, reason: "cancelled" });
      this.finish = null;
      try {
        this.synth?.cancel();
      } catch {
        /* Still invalidate every callback. */
      }
    }
    async speak(text) {
      this.cancel();
      const token = this.version;
      if (!(await this.ready())) return { ok: false, reason: "missing-voice" };
      if (token !== this.version) return { ok: false, reason: "cancelled" };
      const voice = this.voices.find((v) => this.key(v) === this.selected);
      if (!voice) return { ok: false, reason: "missing-voice" };
      // Short utterances avoid long-utterance stalls. Use Devanagari punctuation,
      // not phonetic English substitutions. Each chunk must end before the next.
      const sentences =
        String(text)
          .replace(/[?!]/g, "।")
          .match(/[^।\n]+[।]?/g) || [];
      const chunks = [];
      for (const sentence of sentences) {
        let chunk = "";
        for (const word of sentence.trim().split(/\s+/)) {
          if (chunk && chunk.length + word.length > 180) {
            chunks.push(chunk);
            chunk = "";
          }
          chunk += (chunk ? " " : "") + word;
        }
        if (chunk) chunks.push(chunk);
      }
      for (const chunk of chunks) {
        if (token !== this.version) return { ok: false, reason: "cancelled" };
        const result = await new Promise((resolve) => {
          let done = false;
          const utterance = new this.win.SpeechSynthesisUtterance(chunk);
          utterance.voice = voice;
          utterance.lang = voice.lang.replace("_", "-");
          utterance.rate = 0.88;
          utterance.pitch = 1;
          let timer;
          const finish = (result) => {
            if (done) return;
            done = true;
            this.win.clearTimeout(timer);
            if (this.finish === finish) this.finish = null;
            resolve(result);
          };
          this.finish = finish;
          utterance.onend = () =>
            finish(
              token === this.version
                ? { ok: true }
                : { ok: false, reason: "cancelled" },
            );
          utterance.onerror = (e) =>
            finish({ ok: false, reason: e.error || "synthesis-failed" });
          timer = this.win.setTimeout(() => {
            finish({ ok: false, reason: "timeout" });
            this.cancel();
          }, 25000);
          try {
            this.synth.speak(utterance);
          } catch {
            finish({ ok: false, reason: "synthesis-failed" });
          }
        });
        if (!result.ok) {
          if (token === this.version) this.cancel();
          return result;
        }
      }
      return {
        ok: token === this.version,
        reason: token === this.version ? null : "cancelled",
      };
    }
    bindControls(doc, before = () => {}) {
      const select = doc.getElementById("hindi-voice"),
        status = doc.getElementById("audio-status");
      if (!select || !status) return;
      const render = (voices) => {
        const previous = select.value;
        select.replaceChildren();
        if (!voices.length)
          select.add(new Option("हिंदी आवाज़ अभी नहीं मिली", ""));
        for (const voice of voices)
          select.add(
            new Option(`${voice.name} (${voice.lang})`, this.key(voice)),
          );
        select.value = this.selected;
        select.disabled = !voices.length;
        if (previous !== select.value)
          status.textContent = voices.length
            ? "पहले आवाज़ सुनकर जाँचें। हिंदी साफ़ न सुनाई दे तो दूसरी आवाज़ चुनें या टाइप करें।"
            : "हिंदी आवाज़ नहीं मिली। डिवाइस में हिंदी आवाज़ जोड़ें या टाइप करें।";
      };
      this.listeners.add(render);
      render(this.voices);
      select.addEventListener("change", () => {
        before();
        this.cancel();
        this.selected = select.value;
        status.textContent = "नई आवाज़ चुन ली। सुनकर जाँचें।";
      });
      for (const [id, text] of [
        ["test-audio", TEST],
        ["test-pronunciation", RETROFLEX],
      ]) {
        doc.getElementById(id)?.addEventListener("click", async () => {
          const permission = before();
          const token = this.version;
          const allowed = await permission;
          if (token !== this.version) return;
          if (allowed === false) {
            status.textContent =
              "माइक अभी बंद नहीं हुआ। टाइप करें या पेज फिर खोलें।";
            return;
          }
          status.textContent = "आवाज़ जाँच रहे हैं…";
          const result = await this.speak(text);
          status.textContent = result.ok
            ? "क्या आवाज़ साफ़ थी? गलत उच्चारण हो तो दूसरी आवाज़ चुनें या टाइप करें।"
            : result.reason === "cancelled"
              ? "आवाज़ रोक दी।"
              : "हिंदी आवाज़ नहीं चल पाई। टाइप करके आगे बढ़ें।";
        });
      }
      doc.getElementById("stop-audio")?.addEventListener("click", () => {
        before();
        this.cancel();
        status.textContent = "आवाज़ रोक दी।";
      });
      void this.ready();
    }
  }
  const api = { HindiSpeech, TEST, RETROFLEX };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ShramSpeech = api;
})(typeof window !== "undefined" ? window : globalThis);
