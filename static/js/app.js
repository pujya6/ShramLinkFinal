"use strict";
document.documentElement.classList.add("js-ready");
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (event.defaultPrevented) return;
      const button = event.submitter;
      if (button) button.setAttribute("aria-busy", "true");
      // Do not disable named submitters: their action must reach the server.
    });
  });
  const errors = document.getElementById("form-errors");
  if (errors) errors.focus();
});
