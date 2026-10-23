/* One job at a time. Gestures only express intent; only dialog confirmation POSTs. */
(function (root) {
  "use strict";
  function direction(dx, dy, ms) {
    if (ms < 40 || ms > 1600 || Math.max(Math.abs(dx), Math.abs(dy)) < 70)
      return null;
    if (Math.abs(dx) > Math.abs(dy) * 1.4) return dx > 0 ? "right" : "left";
    if (Math.abs(dy) > Math.abs(dx) * 1.4) return dy > 0 ? "down" : "up";
    return null;
  }
  function gestures(element, callback, win = root) {
    let start = null;
    element.addEventListener("pointerdown", (e) => {
      if (
        !e.isPrimary ||
        e.button !== 0 ||
        e.clientX < 24 ||
        e.clientX > win.innerWidth - 24
      )
        return;
      start = {
        x: e.clientX,
        y: e.clientY,
        time: e.timeStamp,
        id: e.pointerId,
      };
      element.setPointerCapture?.(e.pointerId);
    });
    element.addEventListener("pointerup", (e) => {
      if (!start || e.pointerId !== start.id) return;
      const value = direction(
        e.clientX - start.x,
        e.clientY - start.y,
        e.timeStamp - start.time,
      );
      start = null;
      if (value) callback(value);
    });
    element.addEventListener("pointercancel", () => (start = null));
    element.addEventListener("lostpointercapture", () => (start = null));
    element.addEventListener("keydown", (e) => {
      const value = {
        ArrowUp: "up",
        ArrowDown: "down",
        ArrowLeft: "left",
        ArrowRight: "right",
      }[e.key];
      if (value && !e.repeat) {
        e.preventDefault();
        callback(value);
      }
    });
  }
  const LESSONS = [
    ["up", "↑", "अगला काम देखने के लिए ऊपर स्वाइप करें।"],
    ["down", "↓", "पिछला काम देखने के लिए नीचे स्वाइप करें।"],
    [
      "left",
      "←",
      "यह काम नहीं चाहिए तो बाएँ स्वाइप करें। बाद में वापस ला सकते हैं।",
    ],
    [
      "right",
      "→",
      "आवेदन करने के लिए दाएँ स्वाइप करें। भेजने से पहले आपसे पूछा जाएगा।",
    ],
    [
      "buttons",
      "✓",
      "स्वाइप मुश्किल लगे तो बड़े बटन दबाएँ। अब काम देखना शुरू करें।",
    ],
  ];
  class Discovery {
    constructor(win, doc) {
      this.win = win;
      this.doc = doc;
      this.jobs = JSON.parse(doc.getElementById("job-data").textContent);
      this.index = 0;
      this.applied = new Set();
      this.skips = [];
      this.autoRead = false;
      this.readToken = 0;
      this.pending = null;
      this.sending = false;
      this.key =
        "shramlink-skips-v2-" + doc.getElementById("discovery").dataset.worker;
      try {
        const ids = JSON.parse(win.sessionStorage.getItem(this.key) || "[]");
        if (Array.isArray(ids))
          this.skips = ids.filter((id) => this.jobs.some((j) => j.id === id));
      } catch {}
      this.speech = new win.ShramSpeech.HindiSpeech(win);
      this.el = {};
      for (const id of [
        "discovery-app",
        "job-list-fallback",
        "discovery-status",
        "job-card",
        "stack-empty",
        "stack-empty-title",
        "stack-empty-message",
        "stack-recover",
        "empty-restore",
        "job-position",
        "job-title",
        "job-skill",
        "job-factory",
        "job-wage",
        "job-wage-unit",
        "job-category",
        "job-source",
        "job-source-link",
        "external-notice",
        "job-city",
        "job-shift",
        "job-experience",
        "job-address",
        "job-eligibility",
        "job-requirements",
        "job-reasons",
        "job-speech-text",
        "previous-job",
        "next-job",
        "skip-job",
        "apply-job",
        "undo-skip",
        "restore-skips",
        "apply-dialog",
        "apply-summary",
        "apply-title",
        "direct-apply-note",
        "external-preview",
        "preview-source",
        "preview-profile",
        "preview-matches",
        "preview-missing",
        "apply-error",
        "confirm-apply",
        "cancel-apply",
        "voice-discovery",
        "tutorial",
        "tutorial-title",
        "tutorial-text",
        "tutorial-progress",
        "tutorial-audio",
        "practice-card",
      ])
        this.el[id] = doc.getElementById(id);
      this.el["job-list-fallback"].hidden = true;
      this.el["discovery-app"].hidden = false;
      const bind = (id, fn) =>
        doc.getElementById(id).addEventListener("click", fn);
      bind("previous-job", () => this.move(-1));
      bind("next-job", () => this.move(1));
      bind("skip-job", () => this.skip());
      bind("apply-job", () => this.confirm());
      bind("undo-skip", () => this.undo());
      bind("empty-restore", () => this.el["restore-skips"].click());
      bind("restore-skips", () => {
        this.skips = [];
        this.persist();
        this.index = 0;
        this.render();
        this.message("छोड़े हुए काम वापस आ गए।");
      });
      bind("read-job", () => this.read());
      bind("read-requirements", () => this.read(true));
      bind("stop-job-audio", () => this.stopAudio());
      bind("voice-discovery", () => {
        this.autoRead = !this.autoRead;
        this.el["voice-discovery"].setAttribute(
          "aria-pressed",
          String(this.autoRead),
        );
        this.el["voice-discovery"].textContent = this.autoRead
          ? "■ अपने आप सुनाना बंद करें"
          : "♬ हर काम अपने आप सुनाएँ";
        if (this.autoRead) this.read();
        else this.stopAudio();
      });
      bind("confirm-apply", () => this.submit());
      bind("cancel-apply", () => this.closeConfirm());
      this.el["apply-dialog"].addEventListener("cancel", (e) => {
        e.preventDefault();
        if (!this.sending) this.closeConfirm();
      });
      this.speech.bindControls(doc, () => this.stopAudio());
      gestures(
        doc.getElementById("swipe-pad"),
        (value) => this.action(value),
        win,
      );
      bind("help-discovery", () => this.tutorial());
      bind("tutorial-next", () => this.lessonNext());
      bind("tutorial-skip", () => this.closeTutorial());
      bind("tutorial-audio", () => {
        this.tutorialAudio = true;
        this.el["tutorial-audio"].setAttribute("aria-pressed", "true");
        this.el["tutorial-audio"].textContent = "↻ निर्देश फिर सुनें";
        this.readLesson();
      });
      bind("tutorial-stop-audio", () => {
        this.tutorialAudio = false;
        this.stopAudio();
        this.el["tutorial-audio"].setAttribute("aria-pressed", "false");
        this.el["tutorial-progress"].textContent =
          "आवाज़ रोक दी। तीर देखकर अभ्यास जारी रखें।";
      });
      this.el.tutorial.addEventListener("cancel", (e) => {
        e.preventDefault();
        this.closeTutorial();
      });
      gestures(
        this.el["practice-card"],
        (value) => {
          if (this.el.tutorial.open && value === LESSONS[this.lesson][0])
            this.lessonNext();
        },
        win,
      );
      doc.addEventListener("visibilitychange", () => {
        if (doc.hidden) {
          this.stopAudio();
          this.autoRead = false;
          this.el["voice-discovery"].setAttribute("aria-pressed", "false");
          this.el["voice-discovery"].textContent = "♬ हर काम अपने आप सुनाएँ";
          this.tutorialAudio = false;
          this.el["tutorial-audio"].setAttribute("aria-pressed", "false");
          this.el["tutorial-audio"].textContent = "♬ निर्देश सुनें";
        }
      });
      win.addEventListener("pagehide", () => this.stopAudio());
      this.render();
      let seen = false;
      try {
        seen = win.localStorage.getItem("shramlink-tutorial-v2") === "seen";
      } catch {}
      if (!seen) this.tutorial();
    }
    activeJobs() {
      return this.jobs.filter(
        (j) => !this.applied.has(j.id) && !this.skips.includes(j.id),
      );
    }
    current() {
      return this.activeJobs()[this.index];
    }
    message(text) {
      this.el["discovery-status"].textContent = text;
    }
    persist() {
      try {
        this.win.sessionStorage.setItem(this.key, JSON.stringify(this.skips));
      } catch {}
    }
    stopAudio() {
      this.readToken++;
      this.speech.cancel();
    }
    render() {
      this.stopAudio();
      const jobs = this.activeJobs();
      this.index = Math.max(0, Math.min(this.index, jobs.length - 1));
      const job = jobs[this.index];
      this.el["job-card"].hidden = !job;
      this.el["stack-empty"].hidden = !!job;
      this.el["previous-job"].disabled = !job || this.index === 0;
      this.el["next-job"].disabled = !job || this.index >= jobs.length - 1;
      this.el["undo-skip"].disabled = !this.skips.length;
      this.el["restore-skips"].disabled = !this.skips.length;
      this.el["empty-restore"].hidden = !this.skips.length;
      if (!job) {
        if (this.skips.length) {
          this.el["stack-empty"].dataset.reason = "skipped";
          this.el["stack-empty-title"].textContent =
            "आपने ये काम छोड़ दिए हैं।";
          this.el["stack-empty-message"].textContent =
            "काम वापस लाएँ। कोई आवेदन अपने आप नहीं भेजा जाएगा।";
        } else if (this.applied.size) {
          this.el["stack-empty"].dataset.reason = "reviewed";
          this.el["stack-empty-title"].textContent =
            "इन कामों पर कार्रवाई हो चुकी है।";
          this.el["stack-empty-message"].textContent =
            "आवेदन या प्रदर्शन तैयारी की स्थिति मेरे आवेदन में देखें।";
        }
        if (this.skips.length || this.applied.size) {
          this.el["stack-recover"].href = "/dashboard/laborer#applications";
          this.el["stack-recover"].textContent = "मेरे आवेदन";
        }
        return;
      }
      const skillLabels = {
        welder: "वेल्डर",
        construction: "निर्माण मिस्त्री",
        loader: "लोडर",
        electrician: "बिजली मिस्त्री",
        painter: "पेंटर",
        helper: "हेल्पर",
      };
      const values = {
        "job-title": job.title,
        "job-position": `${this.index + 1} / ${jobs.length}`,
        "job-skill": skillLabels[job.skill] || "स्रोत का अवसर",
        "job-category": job.category_label || "सीधा · प्रकार नहीं बताया",
        "job-wage-unit": job.wage
          ? job.wage_unit === "month"
            ? "/ महीना"
            : "/ दिन"
          : "",
        "job-source": `${job.source || "ShramLink"} · ${job.category_claim || "जानकारी स्वयं दी गई"}${job.retrieved_at ? " · प्राप्त: " + new Intl.DateTimeFormat("hi-IN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Kolkata" }).format(new Date(job.retrieved_at)) : ""}`,
        "job-factory": job.factory + (job.demo ? " · DEMO" : ""),
        "job-wage": job.wage
          ? `₹${job.wage.toLocaleString("en-IN")}`
          : "नहीं बताया",
        "job-city": `शहर · ${job.location}`,
        "job-shift": `${job.shift || "समय नहीं बताया"} · ${job.start_date ? new Intl.DateTimeFormat("hi-IN", { dateStyle: "medium", timeZone: "Asia/Kolkata" }).format(new Date(job.start_date + "T12:00:00+05:30")) : "तारीख नहीं बताई"}`,
        "job-experience":
          job.experience_label +
          (job.min_experience_months >= 24 && job.min_experience_months % 12
            ? ` · ठीक ${job.min_experience_months} महीने`
            : ""),
        "job-address":
          job.worksite_address ||
          (job.external ? "पूरा पता नहीं दिया गया" : job.location),
        "job-requirements": job.requirements,
        "job-speech-text": job.spoken_summary,
        "job-eligibility": job.external
          ? "केवल प्रदर्शन तैयारी। पूरी योग्यता और दस्तावेज़ जाँचना बाकी है।"
          : job.match.eligible
            ? "✓ आपके कौशल और अनुभव की शर्तें पूरी हैं।"
            : "कौशल या अनुभव की शर्त पूरी नहीं है। प्रोफ़ाइल जाँचें।",
      };
      for (const [id, value] of Object.entries(values))
        this.el[id].textContent = value;
      const reasons = this.el["job-reasons"];
      reasons.replaceChildren();
      for (const value of [...job.match.reasons, ...job.match.unmet]) {
        const li = this.doc.createElement("li");
        li.textContent = value;
        reasons.append(li);
      }
      this.el["apply-job"].disabled = !job.external && !job.match.eligible;
      this.el["apply-job"].textContent = job.external
        ? "प्रदर्शन तैयारी →"
        : "आवेदन करें →";
      this.el["external-notice"].hidden = !job.external;
      this.el["job-source-link"].hidden = !job.external;
      if (job.external) {
        this.el["job-source-link"].href = job.original_url;
        this.el["job-source-link"].textContent = job.demo
          ? "काल्पनिक स्रोत लिंक ↗"
          : "मूल अवसर देखें ↗";
      }
      this.el["job-card"].querySelector("details").open = false;
      this.message(`काम ${this.index + 1} / ${jobs.length}। ${job.title}।`);
      if (this.autoRead && !this.el.tutorial.open) void this.read();
    }
    move(delta) {
      if (this.el["apply-dialog"].open || this.el.tutorial.open) return;
      const next = this.index + delta;
      if (next < 0 || next >= this.activeJobs().length) {
        this.message(delta > 0 ? "यह आखिरी काम है।" : "यह पहला काम है।");
        return;
      }
      this.index = next;
      this.render();
    }
    action(value) {
      if (this.el.tutorial.open || this.el["apply-dialog"].open) return;
      ({
        up: () => this.move(1),
        down: () => this.move(-1),
        left: () => this.skip(),
        right: () => this.confirm(),
      })[value]?.();
    }
    skip() {
      const job = this.current();
      if (!job || this.el["apply-dialog"].open || this.el.tutorial.open) return;
      this.skips.push(job.id);
      this.persist();
      this.render();
      this.message("काम छोड़ दिया। ‘पिछला छोड़ा काम लौटाएँ’ से वापस मिलेगा।");
    }
    undo() {
      const id = this.skips.pop();
      this.persist();
      const index = this.activeJobs().findIndex((j) => j.id === id);
      if (index >= 0) this.index = index;
      this.render();
      this.message("छोड़ा हुआ काम वापस आ गया।");
    }
    async confirm() {
      const job = this.current();
      if (!job || this.el.tutorial.open || this.sending) return;
      if (!job.external && !job.match.eligible) {
        this.message("इस काम के लिए कौशल और अनुभव की शर्त पूरी नहीं है।");
        return;
      }
      this.stopAudio();
      this.pending = job.id;
      this.el["apply-summary"].textContent =
        `${job.title} · ${job.factory} · ${job.wage ? "₹" + job.wage + (job.wage_unit === "month" ? "/महीना" : "/दिन") : "वेतन नहीं बताया"} · ${job.location} · ${job.shift || "समय नहीं बताया"} · ${job.start_date || "तारीख नहीं बताई"}`;
      this.pendingJob = job;
      this.reviewToken = null;
      this.el["apply-error"].textContent = "";
      this.el["external-preview"].hidden = !job.external;
      this.el["direct-apply-note"].hidden = !!job.external;
      this.el["apply-title"].textContent = job.external
        ? "स्थानीय प्रदर्शन तैयारी सेव करें?"
        : "यह आवेदन भेजें?";
      this.el["confirm-apply"].textContent = job.external
        ? "हाँ, प्रदर्शन तैयारी सेव करें"
        : "हाँ, आवेदन भेजें";
      this.el["confirm-apply"].disabled = !!job.external;
      this.el["apply-dialog"].showModal();
      this.el["cancel-apply"].focus();
      if (job.external) {
        this.el["preview-matches"].replaceChildren();
        this.el["preview-missing"].replaceChildren();
        this.el["preview-profile"].textContent =
          "आपकी सेव की हुई प्रोफ़ाइल जाँच रहे हैं…";
        this.el["preview-source"].href = job.original_url;
        const controller = new AbortController();
        this.previewController?.abort();
        this.previewController = controller;
        const timer = this.win.setTimeout(() => controller.abort(), 8000);
        try {
          const response = await this.win.fetch(
            `/api/laborer/external/${job.external_id}/preview`,
            { signal: controller.signal, credentials: "same-origin" },
          );
          const preview = await response.json();
          if (
            this.previewController !== controller ||
            this.pending !== job.id ||
            !this.el["apply-dialog"].open
          )
            return;
          if (!response.ok || !preview.confirmation_token)
            throw new Error(preview.error || "विवरण नहीं मिला। फिर खोलें।");
          this.reviewToken = preview.confirmation_token;
          this.el["preview-profile"].textContent =
            `${preview.profile.name} · ${preview.profile.location} · ठीक ${preview.profile.experience_months} महीने अनुभव। जानकारी स्वयं दी गई है।`;
          for (const [id, values] of [
            ["preview-matches", preview.job.match.reasons],
            ["preview-missing", preview.job.match.unmet],
          ]) {
            for (const value of values) {
              const li = this.doc.createElement("li");
              li.textContent = value;
              this.el[id].append(li);
            }
          }
          this.el["confirm-apply"].disabled = false;
        } catch (error) {
          if (
            this.previewController === controller &&
            this.el["apply-dialog"].open
          )
            this.el["apply-error"].textContent =
              error.name === "AbortError"
                ? "स्रोत विवरण समय पर नहीं मिला। फिर खोलें।"
                : "विवरण नहीं मिला। फिर खोलें।";
        } finally {
          this.win.clearTimeout(timer);
        }
      }
    }
    closeConfirm() {
      this.previewController?.abort();
      this.previewController = null;
      this.reviewToken = null;
      this.pending = null;
      this.el["apply-dialog"].close();
      this.el["apply-job"].focus();
    }
    async submit() {
      if (
        this.sending ||
        this.pending === null ||
        !this.el["apply-dialog"].open
      )
        return;
      const id = this.pending;
      const job = this.pendingJob;
      if (job.external && !this.reviewToken) return;
      this.sending = true;
      this.el["confirm-apply"].disabled = true;
      this.el["cancel-apply"].disabled = true;
      this.el["confirm-apply"].textContent = job.external
        ? "प्रदर्शन तैयारी सेव हो रही है…"
        : "भेज रहे हैं…";
      const controller = new AbortController(),
        timer = this.win.setTimeout(() => controller.abort(), 15000);
      try {
        const response = await this.win.fetch(
          job.external
            ? `/api/laborer/external/${job.external_id}/prepare`
            : "/api/laborer/apply",
          {
            method: "POST",
            credentials: "same-origin",
            signal: controller.signal,
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": this.doc.querySelector('meta[name="csrf-token"]')
                .content,
            },
            body: JSON.stringify(
              job.external
                ? { confirmed: "yes", confirmation_token: this.reviewToken }
                : { job_id: id },
            ),
          },
        );
        const result = await response.json();
        if (
          !response.ok ||
          !result.success ||
          (job.external
            ? !result.preparation_id || result.status !== "demo_prepared"
            : !result.application_id)
        )
          throw new Error(
            result.error || "आवेदन नहीं भेजा जा सका। फिर कोशिश करें।",
          );
        this.applied.add(id);
        this.pending = null;
        this.el["apply-dialog"].close();
        this.render();
        const labels = {
          applied: "आवेदन भेज दिया",
          shortlisted: "आवेदन पहले से विचाराधीन है",
          selected: "इस आवेदन में आपका चयन हो चुका है",
          rejected: "इस आवेदन में चयन नहीं हुआ",
          withdrawn: "यह आवेदन वापस लिया गया था",
        };
        this.message(
          job.external
            ? "Demo application prepared — not submitted externally। यह प्रदर्शन है। बाहरी कंपनी को कोई आवेदन नहीं भेजा गया है।"
            : `✓ ${labels[result.status] || "आवेदन की स्थिति अपडेट हुई"}। ‘मेरे आवेदन’ में स्थिति देखें।`,
        );
        this.el["job-title"].focus();
      } catch (error) {
        this.el["apply-error"].textContent =
          error.name === "AbortError" || error instanceof TypeError
            ? "सर्वर का जवाब नहीं मिला। ‘मेरे आवेदन’ में स्थिति जाँचें। फिर भेजने पर दोहरा आवेदन नहीं बनेगा।"
            : error.message;
      } finally {
        this.win.clearTimeout(timer);
        this.sending = false;
        this.el["confirm-apply"].disabled = false;
        this.el["cancel-apply"].disabled = false;
        this.el["confirm-apply"].textContent = "हाँ, आवेदन भेजें";
      }
    }
    async read(requirements = false) {
      const job = this.current();
      if (!job || this.el.tutorial.open || this.doc.hidden) return;
      this.stopAudio();
      const token = this.readToken;
      this.message(
        requirements ? "काम की शर्तें सुनें।" : "काम की जानकारी सुनें।",
      );
      const result = await this.speech.speak(
        requirements ? job.spoken_requirements : job.spoken_summary,
      );
      if (token !== this.readToken) return;
      if (!result.ok && result.reason !== "cancelled") {
        this.autoRead = false;
        this.el["voice-discovery"].setAttribute("aria-pressed", "false");
        this.el["voice-discovery"].textContent = "♬ हर काम अपने आप सुनाएँ";
        this.message(
          "हिंदी आवाज़ नहीं चल पाई। आवाज़ जाँचें। पूरी जानकारी और बटन नीचे उपलब्ध हैं।",
        );
      }
    }
    tutorial() {
      this.stopAudio();
      this.lesson = 0;
      this.tutorialAudio = false;
      this.el["tutorial-audio"].setAttribute("aria-pressed", "false");
      this.el["tutorial-audio"].textContent = "♬ निर्देश सुनें";
      this.el.tutorial.showModal();
      this.renderLesson();
    }
    renderLesson() {
      const [direction, arrow, text] = LESSONS[this.lesson];
      this.stopAudio();
      this.el["tutorial-text"].textContent = text;
      this.el["tutorial-progress"].textContent =
        `कदम ${this.lesson + 1} / ${LESSONS.length}। स्वाइप करें या अगला कदम दबाएँ।`;
      this.el["practice-card"].dataset.direction = direction;
      this.el["practice-card"].querySelector(".practice-arrow").textContent =
        arrow;
      if (this.tutorialAudio) this.readLesson();
    }
    async readLesson() {
      if (!this.el.tutorial.open || this.doc.hidden || !this.tutorialAudio)
        return;
      this.stopAudio();
      const token = this.readToken;
      this.el["tutorial-progress"].textContent =
        `कदम ${this.lesson + 1} / ${LESSONS.length}। निर्देश सुनें।`;
      const result = await this.speech.speak(LESSONS[this.lesson][2]);
      if (token !== this.readToken || !this.el.tutorial.open) return;
      if (!result.ok && result.reason !== "cancelled") {
        this.tutorialAudio = false;
        this.el["tutorial-audio"].setAttribute("aria-pressed", "false");
        this.el["tutorial-progress"].textContent =
          "हिंदी आवाज़ नहीं चली। डिवाइस की आवाज़ और हिंदी भाषा जाँचें। तीर देखकर अभ्यास करें या अगला कदम दबाएँ।";
      } else if (result.ok)
        this.el["tutorial-progress"].textContent =
          `कदम ${this.lesson + 1} / ${LESSONS.length}। स्वाइप करें या अगला कदम दबाएँ। फिर सुनने के लिए ↻ दबाएँ।`;
    }
    lessonNext() {
      if (!this.el.tutorial.open) return;
      if (this.lesson < LESSONS.length - 1) {
        this.lesson++;
        this.renderLesson();
      } else this.closeTutorial();
    }
    closeTutorial() {
      this.stopAudio();
      this.el.tutorial.close();
      try {
        this.win.localStorage.setItem("shramlink-tutorial-v2", "seen");
      } catch {}
      this.el["job-title"].focus();
      if (this.autoRead) this.read();
    }
  }
  if (typeof module !== "undefined" && module.exports)
    module.exports = { direction, LESSONS };
  else if (root.document.getElementById("discovery"))
    root.shramDiscovery = new Discovery(root, root.document);
})(typeof window !== "undefined" ? window : globalThis);
