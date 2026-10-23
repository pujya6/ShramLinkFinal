# ShramLink hackathon demonstration

Target: 5–6 minutes. Use two browser profiles/windows, one worker and one employer,
so their sessions do not overwrite each other. Use an isolated local/demo database.

## Before presenting

- Follow the README, run `init-db` and optionally `seed-demo`; choose your own demo
  password. Use a new worker account to show onboarding.
- On the actual presentation device, confirm Hindi TTS plays, `hi-IN` recognition
  hears a sample answer, the microphone has permission, and the network works.
  Browser/OS speech varies; this physical preflight remains unverified by the
  automated suite. Use localhost on the laptop or HTTPS on a phone.
- Prepare an employer account and plan a future-dated Delhi welding vacancy:
  ₹850/day, one worker, one year minimum experience, 09:00–17:00, clearly marked
  demonstration worksite and safety requirements.
- Never display `.env`, cookie files, real credentials, a full real e-Shram ID or
  other people's profile data. The optional ID can be skipped.

## Live sequence

| Time | Action | Suggested narration |
| --- | --- | --- |
| 0:00–0:30 | Open the ShramLink landing page and show the two entry points. | “ShramLink connects industrial workers and factories in Delhi-NCR, starting with access in Hindi.” |
| 0:30–1:00 | Create a worker account using a presenter-controlled mobile number and a private password. | “The account uses its own password. SMS verification is not integrated in this MVP.” |
| 1:00–2:30 | Start Hindi onboarding. For each question, tap the microphone, answer, then tap again and say **हाँ**. Example answers: a fictional demo name, **पच्चीस**, **वेल्डर**, **कारखाना**, **तीन साल**, **दिल्ली**. | “The assistant asks a bounded set of questions. Every recognised answer can be corrected.” |
| 2:30–3:00 | Intentionally change the name field before submission. Say **दोहराएँ** once. At e-Shram, say **नहीं है**. Review all fields and say **सेव करें**, or check the confirmation and click Save. | “An optional ID is not a verification badge. The worker remains in control of what is saved.” |
| 3:00–3:40 | In the employer window, publish the prepared vacancy. | “The employer specifies skill, location, wages, experience and requirements.” |
| 3:40–4:20 | Refresh the worker dashboard. Open matching details and apply. | “The ranking is explainable: skill, city, domain and experience. It is not an AI suitability prediction.” |
| 4:20–5:00 | Refresh employer applicants, review the self-reported profile and select the worker. Refresh the worker window. | “Both parties now see Selected, persisted against the same application.” |
| 5:00–5:30 | Log the worker out and back in; show the saved profile/status. Briefly show typed mode or a browser with mic access denied. | “The data survives login. Microphone access is helpful, never required to complete the profile.” |

For a shorter demo, publish the vacancy before starting and skip the employer
account-creation screen. Do not use the complete demo worker as evidence of live
onboarding.

## If speech does not cooperate

Say plainly: “This device's browser speech service is unavailable. Here is the
same complete onboarding through typing.” Choose **कीबोर्ड से भरें**, fill the
remaining answers, review and save. Do not present simulated transcript injection
as live speech. The test adapter exists only under `tests/fixtures/` and is never
loaded by the application.

## Closing line

“ShramLink demonstrates one complete recruitment journey: a worker creates a
profile in Hindi or by typing, finds a clearly described vacancy, applies and sees
the employer's decision. The next validation step is physical-device voice testing
with actual workers.”
