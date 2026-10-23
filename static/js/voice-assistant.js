/* Bounded Hindi registration. Only an explicitly started session may listen.
 * Every turn awaits synthesis, a quiet gap, recognition end, then interpretation.
 * No recording, transcript logging or unreviewed database writes. Optional bounded interpretation never controls saving. */
(function (root) {
  "use strict";
  const L =
    typeof module !== "undefined" && module.exports
      ? require("./profile-language.js")
      : root.ShramLanguage;
  const { STEPS } = L;
  const ERRORS = {
    "not-allowed": "माइक की अनुमति नहीं मिली। अनुमति दें या टाइप करें।",
    "service-not-allowed": "आवाज़ की सेवा उपलब्ध नहीं है। टाइप करें।",
    "audio-capture": "माइक्रोफ़ोन नहीं मिला। माइक जाँचें या टाइप करें।",
    "no-speech": "कोई आवाज़ नहीं मिली।",
    network: "आवाज़ की सेवा से संपर्क नहीं हुआ। इंटरनेट जाँचें या टाइप करें।",
    "language-not-supported": "हिंदी पहचान उपलब्ध नहीं है। टाइप करें।",
    aborted: "माइक रुक गया। फिर शुरू करें या टाइप करें।",
  };
  class ShramLinkVoiceAssistant {
    constructor(win, doc) {
      this.win = win;
      this.doc = doc;
      this.form = doc.getElementById("profile-form");
      this.speech = new win.ShramSpeech.HindiSpeech(win);
      this.Recognition = win.SpeechRecognition || win.webkitSpeechRecognition;
      this.active = false;
      this.token = 0;
      this.index = 0;
      this.phase = "answer";
      this.state = "idle";
      this.recognition = null;
      this.errors = 0;
      this.totalErrors = 0;
      this.turns = 0;
      this.reviewed = null;
      this.el = {};
      for (const id of [
        "start-voice",
        "typed-mode",
        "voice-panel",
        "voice-progress",
        "voice-state",
        "step-progress",
        "voice-question",
        "voice-status",
        "voice-transcript",
        "pause-voice",
        "stop-voice",
        "repeat",
        "previous",
        "next",
        "skip",
        "voice-next-controls",
        "confirmation",
        "confirmed",
        "save-profile",
        "speech-support",
        "save-status",
      ])
        this.el[id] = doc.getElementById(id);
      this.groups = [...this.form.querySelectorAll("[data-step]")];
      this.el["start-voice"].hidden = false;
      this.el["typed-mode"].hidden = false;
      this.el["start-voice"].disabled =
        !this.Recognition || !win.isSecureContext;
      this.el["speech-support"].textContent = this.el["start-voice"].disabled
        ? "इस ब्राउज़र में माइक उपलब्ध नहीं है। नीचे फ़ॉर्म भरें।"
        : "शुरू करने पर सवाल और माइक बारी-बारी से चलेंगे। कभी भी रोक सकते हैं।";
      this.el["start-voice"].addEventListener("click", () => this.start());
      this.el["typed-mode"].addEventListener("click", () => this.typed());
      doc
        .getElementById("type-shortcut")
        .addEventListener("click", () => this.typed());
      this.el["pause-voice"].addEventListener("click", () =>
        this.active ? this.pause() : this.resume(),
      );
      this.el["stop-voice"].addEventListener("click", () => this.stop());
      this.el.repeat.addEventListener("click", () => this.restartTurn());
      this.el.previous.addEventListener("click", () => this.navigate(-1));
      this.el.next.addEventListener("click", () => {
        if (this.valid()) {
          this.navigate(1);
        } else this.message("यह जवाब पूरा करें।");
      });
      this.el.skip.addEventListener("click", async () => {
        const wasActive = this.active;
        this.pause();
        const resumeToken = this.token;
        this.skip();
        if (wasActive && (await this.quiet()) && resumeToken === this.token)
          this.resume();
      });
      this.speech.bindControls(doc, async () => {
        if (this.active) this.pause("आवाज़ की जाँच के लिए बातचीत रुकी है।");
        return await this.quiet();
      });
      this.form.addEventListener("input", (e) => {
        if (e.target.id !== "confirmed") {
          this.el.confirmed.checked = false;
          this.reviewed = null;
          if (this.active)
            this.pause(
              "जवाब बदला है। जाँचकर फिर बातचीत शुरू करें, या नीचे पुष्टि करके सेव करें।",
            );
        }
      });
      this.form.addEventListener("submit", (e) => {
        if (!this.allValid() || !this.el.confirmed.checked) {
          e.preventDefault();
          this.typed();
          this.form.reportValidity();
          return;
        }
        this.halt();
        this.setState("saving", "प्रोफ़ाइल सेव हो रही है…");
      });
      doc.addEventListener("visibilitychange", () => {
        if (doc.hidden)
          this.pause("पेज छिपने पर बातचीत रोक दी। वापस आकर फिर शुरू करें।");
      });
      win.addEventListener("pagehide", () => this.halt());
      const editor = doc.getElementById("profile-editor");
      if (
        editor &&
        this.Recognition &&
        win.isSecureContext &&
        !doc.querySelector(".notice.error")
      )
        editor.open = false;
      this.render();
    }
    message(text) {
      this.el["voice-status"].textContent = text;
    }
    setState(state, message) {
      this.state = state;
      const stage = this.doc.getElementById("conversation-stage");
      if (stage) stage.dataset.state = state;
      this.el["pause-voice"].disabled = state === "idle";
      this.el["voice-state"].dataset.state = state;
      const labels = {
        idle: "तैयार",
        speaking: "◉ बोल रहे हैं",
        listening: "◉ अब आप बोलें",
        interpreting: "जवाब समझ रहे हैं",
        paused: "रुके हैं",
        review: "जानकारी जाँचें",
        saving: "सेव हो रहा है",
      };
      this.el["voice-state"].textContent = labels[state] || state;
      this.el["pause-voice"].textContent = this.active
        ? "Ⅱ विराम / Pause"
        : "▶ जारी रखें";
      if (message) this.message(message);
    }
    halt() {
      this.active = false;
      this.interpretController?.abort();
      this.token++;
      this.speech.cancel();
      if (this.recognition) this.recognition.close({ error: "cancelled" });
    }
    async quiet() {
      for (let n = 0; n < 15 && this.recognition; n++)
        await new Promise((r) => this.win.setTimeout(r, 100));
      return !this.recognition;
    }
    pause(message = "बातचीत रुकी है। जारी रखें या टाइप करें।") {
      this.halt();
      this.setState("paused", message);
      this.el["start-voice"].disabled =
        !this.Recognition || !this.win.isSecureContext;
    }
    stop() {
      this.pause("बातचीत बंद कर दी। जवाब अभी सेव नहीं हुए हैं।");
      this.el["voice-transcript"].textContent = "";
      this.phase = "answer";
      this.reviewed = null;
      this.el.confirmed.checked = false;
      this.showAll();
    }
    typed() {
      this.stop();
      this.doc.body.classList.remove("voice-active");
      this.el["voice-panel"].hidden = true;
      this.el["voice-next-controls"].hidden = true;
      this.showAll();
      this.form.querySelector("input:not([type=hidden])")?.focus();
    }
    showAll() {
      const editor = this.doc.getElementById("profile-editor");
      if (editor) editor.open = true;
      this.groups.forEach((g) => (g.hidden = false));
      this.el.confirmation.hidden = false;
    }
    start() {
      if (this.active || !this.Recognition || !this.win.isSecureContext) return;
      this.halt();
      this.index = 0;
      this.phase = "preflight";
      this.errors = 0;
      this.totalErrors = 0;
      this.turns = 0;
      this.reviewed = null;
      this.returnToReview = false;
      this.el.confirmed.checked = false;
      this.activate();
    }
    resume() {
      if (this.active) return;
      this.errors = 0;
      this.activate();
    }
    activate() {
      if (!this.Recognition || this.doc.hidden) return;
      if (this.recognition) {
        this.pause(
          "माइक बंद होने की प्रतीक्षा है। टाइप करें या पेज फिर खोलें।",
        );
        return;
      }
      this.active = true;
      const welcome = this.doc.getElementById("voice-welcome");
      if (welcome) welcome.hidden = true;
      this.token++;
      this.el["voice-panel"].hidden = false;
      this.el["voice-next-controls"].hidden = false;
      this.el["start-voice"].disabled = true;
      this.doc.body.classList.add("voice-active");
      this.render();
      this.el["voice-panel"].scrollIntoView({
        block: "start",
        behavior: "instant",
      });
      void this.turn();
    }
    snapshot() {
      return JSON.stringify(STEPS.map((s) => this.value(s.key)));
    }
    value(key) {
      return key === "skills"
        ? [...this.form.querySelectorAll("input[name=skills]:checked")].map(
            (e) => e.value,
          )
        : this.form.elements.namedItem(key).value;
    }
    put(key, value) {
      if (key === "skills")
        this.form
          .querySelectorAll("input[name=skills]")
          .forEach((e) => (e.checked = value.includes(e.value)));
      else this.form.elements.namedItem(key).value = value ?? "";
      this.el.confirmed.checked = false;
      this.reviewed = null;
    }
    valid(index = this.index) {
      const { key, optional } = STEPS[index];
      const value = this.value(key);
      if (key === "skills") return value.length > 0;
      if (optional && !value) return true;
      if (!this.form.elements.namedItem(key).checkValidity()) return false;
      if (key === "experience_months")
        return Number(value) <= (Number(this.value("age")) - 18) * 12;
      if (key === "eshram_number")
        return /^\d{12}$/.test(value.replace(/[ -]/g, ""));
      return true;
    }
    allValid() {
      return STEPS.every((_, i) => this.valid(i));
    }
    label(step) {
      const value = this.value(step.key);
      if (step.key === "skills")
        return [...this.form.querySelectorAll("input[name=skills]:checked")]
          .map((e) => e.parentElement.textContent.split("/")[0].trim())
          .join(" और ");
      if (step.key === "experience_months")
        return `${L.displayMonths(Number(value))}। ठीक ${value} महीने`;
      const field = this.form.elements.namedItem(step.key);
      if (field.tagName === "SELECT")
        return field.selectedOptions[0]?.textContent.split("/")[0].trim();
      if (step.key === "eshram_number")
        return value ? value.split("").join(" ") : "नहीं दिया";
      return value;
    }
    prompt() {
      if (this.phase === "preflight")
        return `${this.win.ShramSpeech.TEST} क्या हिंदी आवाज़ साफ़ सुनाई दे रही है? हाँ कहें। आवाज़ गलत लगे तो नहीं कहें या टाइप करें।`;
      if (this.phase === "choose-correction")
        return "क्या बदलना है? नाम बदलो, उम्र बदलो, कौशल बदलो, अनुभव बदलो या शहर बदलो कहें। सभी जवाब नीचे भी बदल सकते हैं।";
      if (this.phase === "review")
        return `आपकी जानकारी सुनिए। ${STEPS.map((s) => `${s.label}। ${this.label(s)}।`).join(" ")} यह आपकी दी हुई जानकारी है। क्या सब सही है और सेव करना है? हाँ या सेव कर दो कहें। बदलाव के लिए जैसे मेरा नाम बदलो कहें।`;
      return STEPS[this.index].question;
    }
    render() {
      const review = ["review", "choose-correction"].includes(this.phase);
      this.el["voice-progress"].textContent = review
        ? "पूरी जानकारी जाँचें"
        : `सवाल ${this.index + 1} / ${STEPS.length}`;
      this.el["step-progress"].value = review ? 7 : this.index + 1;
      this.el["voice-question"].textContent =
        this.phase === "preflight"
          ? "पहले आवाज़ जाँचें"
          : review
            ? "सही है? तभी सेव होगा।"
            : STEPS[this.index].question;
      if (!this.el["voice-panel"].hidden) {
        const editor = this.doc.getElementById("profile-editor");
        if (editor) editor.open = true;
        this.groups.forEach((g, i) => (g.hidden = !review && i !== this.index));
        this.el.confirmation.hidden = !review;
      }
      this.el.previous.disabled = this.index === 0;
      this.el.skip.hidden = !STEPS[this.index].optional || review;
      this.el.next.hidden = review || this.phase === "preflight";
    }
    async turn(prefix = "") {
      const token = this.token;
      if (!this.active || this.doc.hidden) return;
      if (++this.turns > 80 || this.totalErrors >= 6) {
        this.pause(
          "कई बार कोशिश हुई। थोड़ा रुकें और फिर शुरू करें, या टाइप करें।",
        );
        return;
      }
      this.render();
      this.setState("speaking", "सवाल सुनें। आवाज़ खत्म होने पर बोलें।");
      if (this.phase === "review") this.reviewed = null;
      const snapshot = this.snapshot();
      const result = await this.speech.speak(prefix + this.prompt());
      if (token !== this.token || !this.active) return;
      if (!result.ok) {
        this.pause("हिंदी आवाज़ नहीं चल पाई। आवाज़ जाँचें या टाइप करें।");
        return;
      }
      await new Promise((resolve) => this.win.setTimeout(resolve, 300));
      if (token !== this.token || !this.active || this.doc.hidden) return;
      if (this.speech.synth?.speaking || this.speech.synth?.pending) {
        this.pause("आवाज़ पूरी तरह रुकी नहीं। टाइप करें या फिर कोशिश करें।");
        return;
      }
      if (this.phase === "review" && snapshot === this.snapshot())
        this.reviewed = snapshot;
      this.setState("listening", "अब बोलें। माइक सुन रहा है।");
      const answer = await this.capture();
      if (token !== this.token || !this.active) return;
      if (answer.error) {
        if (answer.error === "no-speech" && this.errors < 1) {
          this.errors++;
          this.totalErrors++;
          void this.turn("कोई आवाज़ नहीं मिली। एक बार फिर। ");
        } else
          this.pause(
            ERRORS[answer.error] ||
              "माइक बंद नहीं हो पाया। टाइप करें या पेज फिर खोलें।",
          );
        return;
      }
      this.setState("interpreting", "जवाब समझ रहे हैं…");
      this.el["voice-transcript"].textContent = `आपने कहा: ${answer.text}`;
      if (answer.confidence > 0 && answer.confidence < 0.45) {
        this.clarify("साफ़ नहीं सुन पाया। धीरे से फिर बताएँ। ");
        return;
      }
      const interpreted = await this.interpretAnswer(answer.text, token);
      if (token !== this.token || !this.active) return;
      if (interpreted) return;
      this.receive(answer.text);
    }
    async interpretAnswer(text, token) {
      const key =
        this.phase === "choose-correction" ? "name" : STEPS[this.index].key;
      if (
        this.form.dataset.voiceProvider !== "api" ||
        !["answer", "choose-correction"].includes(this.phase) ||
        key === "eshram_number" ||
        L.command(text) ||
        L.correction(text)
      )
        return false;
      // Clear local answers remain authoritative and do not incur API costs.
      const local = L.parse(key, text);
      if (
        this.phase !== "choose-correction" &&
        local !== null &&
        (!Array.isArray(local) || local.length)
      )
        return false;
      const controller = new AbortController();
      this.interpretController = controller;
      const timer = this.win.setTimeout(() => controller.abort(), 8000);
      const status = this.doc.getElementById("interpretation-status");
      try {
        const age = Number(this.value("age"));
        const response = await this.win.fetch("/api/laborer/interpret", {
          method: "POST",
          credentials: "same-origin",
          signal: controller.signal,
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": this.doc.querySelector('meta[name="csrf-token"]')
              .content,
          },
          body: JSON.stringify({
            transcript: text,
            field: key,
            phase: this.phase,
            age: age >= 18 && age <= 80 ? age : null,
          }),
        });
        const result = await response.json();
        if (token !== this.token || !this.active) return true;
        if (!response.ok || result.fallback || result.provider !== "api") {
          if (status)
            status.textContent =
              "ऑनलाइन मदद उपलब्ध नहीं। सामान्य सवाल-जवाब से जारी हैं।";
          return false;
        }
        if (status)
          status.textContent =
            "ऑनलाइन मदद से समझा। सेव करने से पहले जानकारी जाँचें।";
        if (result.intent === "clarify") {
          this.clarify(result.clarification);
          return true;
        }
        const index = STEPS.findIndex((s) => s.key === result.field);
        if (
          index < 0 ||
          result.field === "eshram_number" ||
          !["answer", "correct"].includes(result.intent) ||
          (result.intent === "answer" && index !== this.index)
        )
          return false;
        if (result.intent === "correct") {
          this.returnToReview = ["review", "choose-correction"].includes(
            this.phase,
          );
          this.index = index;
          this.phase = "answer";
        }
        const old = this.value(result.field);
        this.put(result.field, result.value);
        if (!this.valid(index)) {
          this.put(result.field, old);
          this.clarify("यह जवाब सही नहीं लगा। फिर बताएँ। ");
          return true;
        }
        this.errors = 0;
        this.advance(
          `${STEPS[this.index].label}। ${this.label(STEPS[this.index])}। `,
        );
        return true;
      } catch {
        if (token !== this.token || !this.active) return true;
        if (status)
          status.textContent =
            "ऑनलाइन मदद नहीं मिली। सामान्य सवाल-जवाब से जारी हैं।";
        return false;
      } finally {
        this.win.clearTimeout(timer);
        if (this.interpretController === controller)
          this.interpretController = null;
      }
    }
    capture() {
      return new Promise((resolve) => {
        if (this.recognition) {
          resolve({ error: "audio-capture" });
          return;
        }
        let rec;
        try {
          rec = new this.Recognition();
        } catch {
          resolve({ error: "audio-capture" });
          return;
        }
        let ended = false,
          closing = false,
          answer = null,
          endTimer;
        const listenTimer = this.win.setTimeout(
          () => close({ error: "no-speech" }),
          12000,
        );
        const finish = () => {
          if (ended) return;
          ended = true;
          this.win.clearTimeout(listenTimer);
          this.win.clearTimeout(endTimer);
          if (this.recognition?.rec === rec) this.recognition = null;
          resolve(answer || { error: "no-speech" });
        };
        const close = (result) => {
          if (closing || ended) return;
          closing = true;
          answer = result;
          this.win.clearTimeout(listenTimer);
          // Do not speak until onend confirms the microphone has ended.
          endTimer = this.win.setTimeout(
            () => resolve({ error: "end-timeout" }),
            1500,
          );
          try {
            rec.abort();
          } catch {
            resolve({ error: "audio-capture" });
          }
        };
        this.recognition = { rec, close };
        rec.lang = "hi-IN";
        rec.continuous = false;
        rec.interimResults = false;
        rec.maxAlternatives = 1;
        rec.onresult = (e) => {
          if (closing || ended || !this.active || this.recognition?.rec !== rec)
            return;
          const result = e.results[e.resultIndex];
          if (result?.isFinal)
            close({
              text: result[0].transcript,
              confidence: result[0].confidence || 0,
            });
        };
        rec.onerror = (e) => close({ error: e.error });
        rec.onend = finish;
        try {
          rec.start();
        } catch {
          answer = { error: "audio-capture" };
          finish();
        }
      });
    }
    clarify(message) {
      this.errors++;
      this.totalErrors++;
      if (this.errors >= 3) {
        this.pause(message + " नीचे जवाब लिखें, या जारी रखें दबाएँ।");
        return;
      }
      void this.turn(message);
    }
    receive(text) {
      const command = L.command(text),
        correction = L.correction(text);
      if (command === "stop") {
        this.stop();
        return;
      }
      if (command === "pause") {
        this.pause();
        return;
      }
      if (command === "repeat") {
        void this.turn();
        return;
      }
      if (this.phase === "preflight") {
        if (command === "yes") {
          this.phase = "answer";
          this.errors = 0;
          void this.turn();
        } else if (command === "no") {
          this.pause(
            "आवाज़ सही नहीं है। दूसरी हिंदी आवाज़ जाँचें या टाइप करें।",
          );
        } else this.clarify("आवाज़ साफ़ है तो हाँ कहें। ");
        return;
      }
      if (correction) {
        this.returnToReview = ["review", "choose-correction"].includes(
          this.phase,
        );
        this.index = STEPS.findIndex((s) => s.key === correction.key);
        this.phase = "answer";
        if (correction.value !== null) {
          this.put(correction.key, correction.value);
          if (this.valid()) {
            this.errors = 0;
            this.advance(
              `${STEPS[this.index].label} बदल दिया। ${this.label(STEPS[this.index])}। `,
            );
            return;
          }
        }
        this.errors = 0;
        void this.turn();
        return;
      }
      if (command === "back") {
        this.index = Math.max(0, this.index - 1);
        this.phase = "answer";
        this.errors = 0;
        void this.turn();
        return;
      }
      if (this.phase === "review") {
        if (command === "yes" || command === "save") {
          if (this.reviewed === this.snapshot() && this.allValid()) {
            this.el.confirmed.checked = true;
            this.form.requestSubmit();
          } else {
            this.reviewed = null;
            void this.turn("जानकारी फिर से जाँचें। ");
          }
        } else if (command === "no") {
          this.phase = "choose-correction";
          void this.turn();
        } else this.clarify("सेव करने के लिए हाँ, या बदलाव का नाम बताएँ। ");
        return;
      }
      if (this.phase === "choose-correction") {
        this.clarify("किस जवाब को बदलना है? ");
        return;
      }
      if (
        command === "skip" ||
        (command === "no" && STEPS[this.index].optional)
      ) {
        this.skip();
        return;
      }
      if (command === "no") {
        this.index = Math.max(0, this.index - 1);
        void this.turn("पिछला जवाब फिर बताएँ। ");
        return;
      }
      if (command === "next" || command === "yes") {
        if (this.valid()) {
          this.advance();
        } else this.clarify("पहले यह जवाब बताएँ। ");
        return;
      }
      if (command === "save") {
        this.clarify("पहले सभी सवाल और आखिरी पुष्टि पूरी करें। ");
        return;
      }
      const key = STEPS[this.index].key,
        value = L.parse(key, text);
      if (value === null || (Array.isArray(value) && !value.length)) {
        this.clarify(
          key === "experience_months"
            ? "साल और महीने साफ़ बताएँ, जैसे एक साल तीन महीने। "
            : "एक साफ़ जवाब दें। दिए हुए विकल्पों से चुन सकते हैं। ",
        );
        return;
      }
      const old = this.value(key);
      this.put(key, value);
      if (!this.valid()) {
        this.put(key, old);
        this.clarify(
          key === "experience_months"
            ? "अनुभव आपकी उम्र और अठारह साल के बाद के समय से मेल नहीं खाता। "
            : "यह जवाब मान्य नहीं है। फिर बताएँ। ",
        );
        return;
      }
      this.errors = 0;
      this.advance(
        `${STEPS[this.index].label}। ${this.label(STEPS[this.index])}। `,
      );
    }
    advance(prefix = "") {
      if (this.returnToReview && this.allValid()) {
        this.phase = "review";
        this.returnToReview = false;
      } else if (this.index < STEPS.length - 1) this.index++;
      else if (this.allValid()) this.phase = "review";
      else {
        this.index = STEPS.findIndex((_, i) => !this.valid(i));
        this.phase = "answer";
      }
      this.render();
      void this.turn(prefix);
    }
    skip() {
      if (!STEPS[this.index].optional) {
        if (this.active) this.clarify("यह सवाल ज़रूरी है। ");
        else this.message("यह सवाल ज़रूरी है।");
        return;
      }
      this.put(STEPS[this.index].key, "");
      this.errors = 0;
      this.advance("ई श्रम नंबर छोड़ दिया। ");
    }
    async navigate(delta) {
      const wasActive = this.active;
      const previousIndex = this.index;
      this.pause();
      const resumeToken = this.token;
      this.index = Math.max(0, Math.min(STEPS.length - 1, this.index + delta));
      this.phase =
        delta > 0 && previousIndex === 6 && this.valid() && this.allValid()
          ? "review"
          : "answer";
      this.render();
      if (wasActive && (await this.quiet()) && resumeToken === this.token)
        this.resume();
    }
    async restartTurn() {
      if (this.active) {
        this.pause();
      }
      const resumeToken = this.token;
      if ((await this.quiet()) && resumeToken === this.token) this.resume();
    }
  }
  if (typeof module !== "undefined" && module.exports)
    module.exports = { ...L, ShramLinkVoiceAssistant };
  else if (root.document.getElementById("profile-form"))
    root.shramVoice = new ShramLinkVoiceAssistant(root, root.document);
})(typeof window !== "undefined" ? window : globalThis);
