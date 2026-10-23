"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {
  number,
  parse,
  idDigits,
  STEPS,
} = require("../static/js/voice-assistant.js");
test("Hindi ages and experience use bounded numeric parsing", () => {
  assert.equal(number("मेरी उम्र पच्चीस साल है"), 25);
  assert.equal(number("२६"), 26);
  assert.equal(number("तीन साल का अनुभव है"), 3);
  assert.equal(number("शून्य"), 0);
  assert.equal(number("पांच"), 5);
  assert.equal(number("बीस या तीस"), null);
  assert.equal(number("10000"), null);
});
test("Hindi skill/domain/city aliases map to existing server vocabulary", () => {
  assert.deepEqual(parse("skills", "मुझे वेल्डिंग और बिजली का काम आता है"), [
    "welder",
    "electrician",
  ]);
  assert.deepEqual(parse("skills", "नहीं समझा"), []);
  assert.equal(parse("preferred_domain", "गोदाम"), "warehouse");
  assert.equal(parse("location", "ग्रेटर नोएडा"), "Greater Noida");
  assert.equal(parse("location", "गुड़गांव"), "Gurugram");
  assert.equal(parse("location", "अज्ञात शहर"), null);
});
test("Name cleanup and e-Shram require explicit valid values", () => {
  assert.equal(parse("name", "मेरा नाम परीक्षण श्रमिक है।"), "परीक्षण श्रमिक");
  assert.equal(idDigits("१२३४ ५६७८ ९०१२"), "123456789012");
  assert.equal(
    idDigits("एक दो तीन चार पाँच छह सात आठ नौ शून्य एक दो"),
    "123456789012",
  );
  assert.equal(idDigits("1234 unknown 56789012"), null);
  assert.equal(STEPS.length, 7);
  assert.deepEqual(
    STEPS.filter((s) => s.optional).map((s) => s.key),
    ["eshram_number"],
  );
});

const L = require("../static/js/profile-language.js");
for (const [input, expected] of [
  ["जीत झा", "जीत झा"],
  ["जीवन कुमार", "जीवन कुमार"],
  ["जीतेन्द्र शर्मा", "जीतेन्द्र शर्मा"],
  ["जी, मेरा नाम जीत झा है", "जीत झा"],
  ["मेरा नाम रमेश कुमार है", "रमेश कुमार"],
  ["जी जीवन कुमार", "जीवन कुमार"],
  ["जी।जीत झा", "जीत झा"],
  ["नहीद खान", "नहीद खान"],
  ["Jitendra Sharma", "Jitendra Sharma"],
  ["Nahid Khan", "Nahid Khan"],
  ["नहीं, मेरा नाम जीत झा है", "जीत झा"],
])
  test(`name token boundary: ${input}`, () =>
    assert.equal(L.parse("name", input), expected));
test("correction and negation require whole words and preserve name case", () => {
  assert.deepEqual(L.correction("नहीं, मेरा नाम जीत झा है"), {
    key: "name",
    value: "जीत झा",
  });
  assert.deepEqual(L.correction("Nahi, mera naam Jeet Jha hai"), {
    key: "name",
    value: "Jeet Jha",
  });
  assert.equal(L.correction("Nahid name"), null);
  assert.equal(L.correction("नाम बदलोमत"), null);
  assert.equal(L.correction("surname गलत"), null);
  assert.equal(L.command("नहीद"), null);
  assert.equal(L.parse("location", "नहीद दिल्ली में"), "Delhi");
  assert.equal(L.parse("location", "दिल्ली नहीं"), null);
});
const { direction } = require("../static/js/discovery.js");
test("optional ID absence remains a skip, not a correction", () => {
  for (const input of ["मेरे पास ई-श्रम नंबर नहीं है", "mere paas e-shram number nahi hai"]) {
    assert.equal(L.correction(input), null);
    assert.equal(L.command(input), "skip");
  }
});
for (const [input, months] of [
  ["6 mahine", 6],
  ["1 saal", 12],
  ["1 saal 3 mahine", 15],
  ["ek saal paanch mahine", 17],
  ["dedh saal", 18],
  ["1 saal 11 mahine", 23],
  ["2 saal", 24],
  ["2 saal 8 mahine", 32],
  ["3 saal 6 mahine", 42],
  ["मुझे डेढ़ साल का अनुभव है", 18],
  ["दो साल और आठ महीने", 32],
  ["शून्य", 0],
]) {
  test(`exact months: ${input}`, () => assert.equal(L.duration(input), months));
}
test("ambiguous experience never becomes zero", () => {
  for (const input of [
    "लगभग दो साल",
    "2",
    "दो या तीन साल",
    "6 weeks",
    "2 saal extra",
    "2 saal 1 saal",
    "-3 mahine",
    "1.3 saal",
    "1 saal aur",
    "पता नहीं",
  ])
    assert.equal(L.duration(input), null, input);
});
test("display policy keeps stored precision", () => {
  assert.equal(L.displayMonths(23), "23 महीने");
  assert.equal(L.displayMonths(32), "2 वर्ष");
  assert.equal(L.displayMonths(42), "3 वर्ष");
});
test("natural phrases and ambiguity respect vocabulary", () => {
  assert.equal(L.parse("name", "जी, रमेश कुमार"), "रमेश कुमार");
  assert.equal(L.parse("name", "mera naam Ramesh Kumar hai"), "Ramesh Kumar");
  assert.equal(L.parse("age", "मैं पच्चीस साल का हूँ"), 25);
  assert.equal(L.parse("age", "main pachis saal ka hoon"), 25);
  assert.equal(
    L.parse("location", "मैं नोएडा में काम करना चाहता हूँ"),
    "Noida",
  );
  assert.equal(L.parse("location", "दिल्ली और नोएडा"), null);
  assert.equal(L.parse("preferred_domain", "कारखाना या गोदाम"), null);
  assert.deepEqual(L.parse("skills", "वेल्डिंग नहीं आती है"), []);
  assert.equal(L.parse("name", "12345"), null);
});
test("natural commands are context signals, not profile values", () => {
  for (const [value, expected] of [
    ["जी हाँ", "yes"],
    ["सही है", "yes"],
    ["नहीं", "no"],
    ["गलत है", "no"],
    ["दोबारा पूछो", "repeat"],
    ["फिर से बोलो", "repeat"],
    ["पिछला सवाल", "back"],
    ["रुको", "stop"],
    ["बंद करो", "stop"],
    ["आगे बढ़ो", "next"],
    ["छोड़ दो", "skip"],
    ["सेव कर दो", "save"],
    ["मेरे पास ई-श्रम नंबर नहीं है", "skip"],
  ])
    assert.equal(L.command(value), expected);
  assert.deepEqual(L.correction("नहीं, मेरा नाम सुरेश है"), {
    key: "name",
    value: "सुरेश",
  });
  assert.deepEqual(L.correction("मेरा नाम बदलो"), { key: "name", value: null });
});
for (const [dx, dy, ms, result] of [
  [0, -100, 200, "up"],
  [0, 100, 200, "down"],
  [-100, 0, 200, "left"],
  [100, 0, 200, "right"],
  [20, 0, 200, null],
  [100, 90, 200, null],
  [100, 0, 2000, null],
  [100, 0, 10, null],
])
  test(`gesture intent ${dx}/${dy}/${ms}`, () =>
    assert.equal(direction(dx, dy, ms), result));
test("common Hinglish and uncertain names are not silently guessed", () => {
  assert.deepEqual(L.parse("skills", "mujhe bijli ka kaam aata hai"), [
    "electrician",
  ]);
  assert.equal(
    L.parse("preferred_domain", "main godam mein kaam chahta hoon"),
    "warehouse",
  );
  assert.equal(L.parse("location", "dilli mein"), "Delhi");
  assert.equal(L.duration("120 mahine"), 120);
  assert.equal(L.parse("name", "मुझे नहीं पता"), null);
  assert.equal(L.parse("name", "पता नहीं"), null);
});
