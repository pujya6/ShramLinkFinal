/* Read-only synthetic examples. No fetch, microphone, form submission or persistence. */
(function () {
  "use strict";
  const byId = (id) => document.getElementById(id);
  byId("parse-example").addEventListener("click", () => {
    const months = window.ShramLanguage.duration(
      byId("duration-example").value,
    );
    byId("duration-result").textContent =
      months === null
        ? "Clarification needed / कितने साल और कितने महीने? Nothing was saved."
        : `${months} months stored in the example → ${window.ShramLanguage.displayMonths(months)} displayed. Extra months remain available for eligibility. Nothing was saved.`;
  });
  const examples = JSON.parse(byId("match-examples").textContent);
  byId("match-example").addEventListener("click", () => {
    const key = ["skill", "city", "months"]
      .map((x) => byId("example-" + x).value)
      .join(":");
    const result = examples[key];
    if (!result) return;
    byId("match-result").textContent =
      `Illustrative rank points: ${result.score}/100. ${result.eligible ? "Skill and experience requirements met." : "Skill or experience requirement not met."} Not a probability, verification or hiring guarantee.`;
    byId("match-reasons").replaceChildren();
    for (const text of [...result.reasons, ...result.unmet]) {
      const item = document.createElement("li");
      item.textContent = text;
      byId("match-reasons").append(item);
    }
  });
})();
