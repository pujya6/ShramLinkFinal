/* Deterministic, deliberately bounded Hindi/Hinglish profile vocabulary. */
(function (root) {
  "use strict";
  const NUMBER_WORDS =
    "शून्य एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास पचास इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ इकसठ बासठ तिरसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उनासी अस्सी".split(
      " ",
    );
  const NUMBER_ALIASES = {
    जीरो: 0,
    ज़ीरो: 0,
    पांच: 5,
    छः: 6,
    छे: 6,
    पन्द्रह: 15,
    अठ्ठाईस: 28,
    अड़तीस: 38,
    अड़तालीस: 48,
    अड़तालिस: 48,
  };
  const SKILLS = {
    welder: ["वेल्डर", "वेल्डिंग", "welder", "welding"],
    construction: [
      "निर्माण",
      "राजमिस्त्री",
      "राज मिस्त्री",
      "कंस्ट्रक्शन",
      "construction",
      "mason",
      "rajmistri",
      "raj mistri",
    ],
    loader: ["लोडर", "लोडिंग", "loader", "loading"],
    electrician: [
      "बिजली",
      "इलेक्ट्रीशियन",
      "इलेक्ट्रिशियन",
      "electrician",
      "electrical",
      "bijli",
    ],
    painter: ["पेंटर", "पेंटिंग", "रंगाई", "painter", "painting", "rangai"],
    helper: ["हेल्पर", "सहायक", "helper", "मददगार"],
  };
  const DOMAINS = {
    manufacturing: [
      "कारखाना",
      "फैक्ट्री",
      "फ़ैक्ट्री",
      "मैन्युफैक्चरिंग",
      "manufacturing",
      "factory",
      "karkhana",
      "karakhana",
    ],
    construction: ["निर्माण", "कंस्ट्रक्शन", "construction"],
    warehouse: ["गोदाम", "वेयरहाउस", "warehouse", "godam", "godaam"],
    maintenance: [
      "रखरखाव",
      "मेंटेनेंस",
      "maintenance",
      "rakh rakhav",
      "rakhrakhav",
    ],
  };
  const CITIES = {
    "Greater Noida": ["ग्रेटर नोएडा", "greater noida"],
    Delhi: ["दिल्ली", "delhi", "dilli"],
    Noida: ["नोएडा", "noida"],
    Ghaziabad: ["गाजियाबाद", "गाज़ियाबाद", "ghaziabad"],
    Faridabad: ["फरीदाबाद", "फ़रीदाबाद", "faridabad"],
    Gurugram: [
      "गुरुग्राम",
      "गुड़गांव",
      "गुड़गाँव",
      "गुड़गांव",
      "gurugram",
      "gurgaon",
    ],
  };
  const ROMAN =
    "zero ek do teen chaar paanch chhe saat aath nau das gyarah barah terah chaudah pandrah solah satrah atharah unnis bees ikkees bais teis chaubis pachis chhabbis sattais atthais untis tees ikattis battis taintis chauntis paintis chhattis saintis adtis untalis chalis".split(
      " ",
    );
  const ALIASES = {
    ...NUMBER_ALIASES,
    char: 4,
    panch: 5,
    che: 6,
    chhah: 6,
    pachchees: 25,
    pachchis: 25,
    pachees: 25,
    pachis: 25,
    pachaas: 50,
    pachas: 50,
    saath: 60,
    sattar: 70,
    assi: 80,
    shunya: 0,
    शुन्य: 0,
  };
  const STEPS = [
    { key: "name", label: "नाम", question: "आपका पूरा नाम क्या है?" },
    {
      key: "age",
      label: "उम्र",
      question: "आपकी उम्र कितनी है? पूरे साल में बताएँ।",
    },
    {
      key: "skills",
      label: "कौशल",
      question:
        "आपको कौन सा काम आता है? वेल्डिंग, निर्माण, लोडिंग, बिजली, पेंटिंग या हेल्पर।",
    },
    {
      key: "preferred_domain",
      label: "काम का क्षेत्र",
      question: "कहाँ काम करना चाहेंगे? कारखाना, निर्माण, गोदाम या रखरखाव।",
    },
    {
      key: "experience_months",
      label: "अनुभव",
      question:
        "अठारह साल की उम्र के बाद कितना अनुभव है? साल और महीने बताएँ। नए हैं तो शून्य कहें।",
    },
    {
      key: "location",
      label: "शहर",
      question:
        "किस शहर में काम चाहिए? दिल्ली, नोएडा, ग्रेटर नोएडा, गाज़ियाबाद, फ़रीदाबाद या गुरुग्राम।",
    },
    {
      key: "eshram_number",
      label: "ई श्रम नंबर",
      question:
        "आपका बारह अंकों का ई श्रम नंबर क्या है? नहीं है तो छोड़ दो कहें।",
      optional: true,
    },
  ];
  function normalize(value) {
    return String(value)
      .normalize("NFC")
      .toLowerCase()
      .replace(/[०-९]/g, (c) => String(c.charCodeAt(0) - 0x0966))
      .replace(/[।!?;,]/g, " ")
      .replace(/\.(?!\d)/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }
  function numeric(value) {
    if (/^\d{1,3}$/.test(value)) return Number(value);
    if (Object.hasOwn(ALIASES, value)) return ALIASES[value];
    let n = NUMBER_WORDS.indexOf(value);
    if (n >= 0) return n;
    n = ROMAN.indexOf(value);
    return n >= 0 ? n : null;
  }
  function number(text) {
    const value = normalize(text)
      .replace(/^(जी\s+|ji\s+)/u, "")
      .replace(
        /^(मेरी उम्र|मेरी आयु|उम्र|आयु|मुझे|मेरा अनुभव|मैं|meri umar|meri age|main|mein)(?:\s+|$)/u,
        "",
      )
      .replace(
        /\s+(साल|वर्ष|की उम्र|का अनुभव|अनुभव|है|हूँ|हूं|years|year|old|का|की|saal|sal|ki|ka|hoon|hun|hai|umar|experience)\b/gu,
        " ",
      );
    // Devanagari has no JavaScript word boundary; remove only full filler tokens.
    return numeric(
      value
        .split(" ")
        .filter(
          (t) =>
            ![
              "साल",
              "वर्ष",
              "की",
              "उम्र",
              "का",
              "अनुभव",
              "है",
              "हूँ",
              "हूं",
            ].includes(t),
        )
        .join(" ")
        .trim(),
    );
  }
  function duration(text) {
    let v = normalize(text)
      .replace(/^(जी\s+|ji\s+)/u, "")
      .replace(/^(मुझे|मेरे पास|मेरा|मैं|mere paas|mujhe|mera|main)\s+/u, "")
      .replace(
        /(?:^|\s+)(का अनुभव है|का अनुभव|अनुभव है|अनुभव|experience hai|experience|है|हूँ|हूं)\s*$/u,
        "",
      )
      .trim();
    if (
      /^(0|शून्य|जीरो|zero|नया|नए|नयी|नया हूँ|नए हैं|fresher|naya|नहीं|नहीं है|कोई अनुभव नहीं|अनुभव नहीं है|nahi|nahi hai)$/.test(
        v,
      )
    )
      return 0;
    // Approximation, ranges, alternatives and unrecognised residue require clarification.
    if (
      /(?:^|\s)(?:लगभग|करीब|या|लगता|around|about|lagbhag|ya|or)(?=\s|$)|[\-–]/u.test(
        v,
      )
    )
      return null;
    const tokens = v.split(" ");
    let total = 0,
      seen = new Set();
    for (let i = 0; i < tokens.length; ) {
      let n = numeric(tokens[i]);
      if (["डेढ़", "डेढ", "dedh", "derh", "1.5"].includes(tokens[i])) n = 1.5;
      if (["ढाई", "dhai", "2.5"].includes(tokens[i])) n = 2.5;
      if (["आधा", "aadha", "adha", "0.5"].includes(tokens[i])) n = 0.5;
      const unit = tokens[i + 1];
      const kind = ["साल", "वर्ष", "saal", "sal", "year", "years"].includes(
        unit,
      )
        ? "y"
        : [
              "महीना",
              "महीने",
              "महीनों",
              "माह",
              "mahina",
              "mahine",
              "mahiney",
              "month",
              "months",
            ].includes(unit)
          ? "m"
          : null;
      if (
        n === null ||
        !kind ||
        seen.has(kind) ||
        (kind === "m" && !Number.isInteger(n))
      )
        return null;
      seen.add(kind);
      total += n * (kind === "y" ? 12 : 1);
      i += 2;
      if (["और", "aur", "and"].includes(tokens[i])) {
        i++;
        if (i === tokens.length) return null;
      }
    }
    return seen.size && Number.isInteger(total) && total >= 0 && total <= 744
      ? total
      : null;
  }
  function choices(text, dictionary) {
    let v = " " + normalize(text) + " ";
    const found = [];
    // Longest aliases first keep Greater Noida from also matching Noida.
    const aliases = Object.entries(dictionary)
      .flatMap(([key, items]) => items.map((a) => [key, a]))
      .sort((a, b) => b[1].length - a[1].length);
    for (const [key, alias] of aliases)
      if (v.includes(" " + alias + " ")) {
        if (!found.includes(key)) found.push(key);
        v = v.replaceAll(" " + alias + " ", " ");
      }
    return Object.keys(dictionary).filter((k) => found.includes(k));
  }
  function idDigits(text) {
    const value = normalize(text).replace(/[-\s]/g, "");
    if (/^\d{12}$/.test(value)) return value;
    const parts = normalize(text).split(" ").map(numeric);
    return parts.length === 12 && parts.every((n) => n !== null && n <= 9)
      ? parts.join("")
      : null;
  }
  function command(text) {
    const v = normalize(text);
    if (/^(रुको|रुकिए|बंद करो|बंद करें|stop|bas|बस|band karo)$/.test(v))
      return "stop";
    if (/^(ठहरो|pause|थोड़ा रुको|thoda ruko)$/.test(v)) return "pause";
    if (
      /^(हाँ|हां|जी हाँ|जी हां|सही है|हाँ सही है|haan|han|ha|ji haan|sahi hai|yes)$/.test(
        v,
      )
    )
      return "yes";
    if (/^(नहीं|नही|गलत है|नहीं गलत है|nahi|nahin|galat hai|no)$/.test(v))
      return "no";
    if (
      /^(दोबारा पूछो|फिर से बोलो|फिर बोलो|दोहराएँ|दोहराओ|फिर सुनाओ|repeat|dobara poocho|phir se bolo)$/.test(
        v,
      )
    )
      return "repeat";
    if (/^(पिछला सवाल|पिछले सवाल पर जाओ|पीछे|back|pichla sawal)$/.test(v))
      return "back";
    if (/^(आगे बढ़ो|आगे|अगला सवाल|next|aage badho)$/.test(v)) return "next";
    if (
      /^(छोड़ दो|छोड़ें|छोड़ो|skip|chhod do|chhodo|नहीं है|nahi hai|मेरे पास ई[ -]?श्रम नंबर नहीं है|mere paas e[ -]?shram number nahi hai)$/.test(
        v,
      )
    )
      return "skip";
    if (/^(सेव कर दो|सेव करें|सेव करो|save|save kar do|save karo)$/.test(v))
      return "save";
    return null;
  }
  const FIELD_WORDS = {
    name: ["नाम", "naam", "name"],
    age: ["उम्र", "आयु", "umar", "age"],
    skills: ["कौशल", "हुनर", "skills", "kaam"],
    preferred_domain: ["क्षेत्र", "domain"],
    experience_months: ["अनुभव", "experience", "anubhav"],
    location: ["शहर", "city", "shehar"],
    eshram_number: ["ई श्रम", "ई-श्रम", "eshram"],
  };
  function correction(text) {
    const v = normalize(text);
    if (
      !/(?:^|\s)(?:बदलो|बदलें|सुधारो|गलत|badlo|change|correct)(?=\s|$)|^(?:नहीं|नही|nahi|nahin)(?=\s|$)/u.test(
        v,
      )
    )
      return null;
    for (const [key, words] of Object.entries(FIELD_WORDS))
      if (words.some((w) => ` ${v} `.includes(` ${w} `))) {
        const value =
          /(?:^|\s)(?:बदलो|बदलें|सुधारो|badlo|change|correct)(?=\s|$)/u.test(v)
            ? null
            : parse(
                key,
                String(text)
                  .trim()
                  .replace(/^(?:नहीं|नही|nahin|nahi)(?:[\s,।;!?]+|$)/iu, ""),
              );
        return { key, value };
      }
    return null;
  }
  function parse(key, text) {
    if (key === "age" || key === "experience_years") return number(text);
    if (key === "experience_months") return duration(text);
    if (key === "eshram_number") return idDigits(text);
    if (["skills", "preferred_domain", "location"].includes(key)) {
      if (
        /(?:^|\s)(?:नहीं|नही|nahi|nahin|not|or|ya|या)(?=\s|$)/u.test(
          normalize(text),
        )
      )
        return key === "skills" ? [] : null;
      const items = choices(
        text,
        key === "skills" ? SKILLS : key === "location" ? CITIES : DOMAINS,
      );
      return key === "skills" ? items : items.length === 1 ? items[0] : null;
    }
    let value = String(text)
      .trim()
      // A polite/negative prefix must be a whole token. JavaScript \b does
      // not delimit Devanagari: "जीत" and "जीवन" are names, not "जी" + filler.
      .replace(/^(?:नहीं|नही|nahin|nahi)(?:[\s,।;!?]+|$)/iu, "")
      .replace(/^(?:जी|ji)(?:[\s,।;!?]+|$)/iu, "")
      .replace(
        /^(मेरा नाम|नाम|मैं|mera naam|mera nam|my name is|naam)\s+/iu,
        "",
      )
      .replace(/\s+(है|हूँ|हूं|hai|hoon|hun)[।.!?]?$/iu, "")
      .replace(/[।.!?]$/u, "")
      .trim();
    if (
      command(value) ||
      /(?:^|\s)(?:पता नहीं|नहीं पता|नहीं समझा|समझ नहीं|कुछ नहीं|ठीक है|pata nahi|nahi pata|don't know|dont know|not sure|okay|ok)(?=\s|$)/iu.test(
        value,
      )
    )
      return null;
    return value.length >= 2 &&
      value.length <= 100 &&
      /^[\p{L}\p{M} .'-]+$/u.test(value)
      ? value
      : null;
  }
  function displayMonths(months) {
    return months < 24 ? `${months} महीने` : `${Math.floor(months / 12)} वर्ष`;
  }
  const api = {
    number,
    normalize,
    parse,
    idDigits,
    duration,
    command,
    correction,
    displayMonths,
    STEPS,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ShramLanguage = api;
})(typeof window !== "undefined" ? window : globalThis);
