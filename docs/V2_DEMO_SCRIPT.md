# ShramLink V2 hackathon demo

Allow 6–8 minutes. Use synthetic worker details and two browser profiles/windows.
The operator should rehearse on the actual presentation device first. If physical
speech has not passed preflight, demonstrate the typed fallback and describe the
voice state machine as automated-test evidence; do not present mock recognition
as live audio recognition.

## Prepare

1. Follow README installation, run `init-db`, then `seed-demo` in a private demo
   database. Choose your own demo password. Do not project terminal secrets.
2. Log in as `employer.demo@example.invalid` in one browser profile. Post three
   vacancies dated today or later so next/previous/skip are visible. Use real demo
   requirements, for example a welder in Delhi at ₹850/day, 09:00–17:00,
   minimum experience **12 months**, safety equipment provided, two openings.
   Other cards can vary daily wage/city. Label all as demonstration vacancies.
3. In a separate browser profile, create a new worker account using synthetic
   test details. Account creation/password entry is typed. Do not use a real ID.
4. Check Hindi voice pronunciation, microphone permissions and HTTPS/localhost.
   Open the retroflex sample if useful. Keep typing available.

## 1. Speak and create a profile — 2 minutes

Press **बातचीत शुरू करें** once. After hearing the audio check, say **जी हाँ**.
Answer each automatically opened listening turn:

| Prompt | Example response |
| --- | --- |
| Name | मेरा नाम परीक्षण श्रमिक है |
| Age | मैं पच्चीस साल का हूँ |
| Skill | मुझे वेल्डिंग आती है |
| Domain | कारखाना |
| Experience | ek saal paanch mahine |
| City | मैं दिल्ली में काम करना चाहता हूँ |
| Optional e-Shram | मेरे पास ई-श्रम नंबर नहीं है |

Show that experience becomes **17 months**. During a question, say **दोबारा पूछो**
once; the assistant repeats and resumes listening. During final review say
**नहीं**, then **मेरा नाम बदलो**, then provide a corrected synthetic name.
The profile is read again. Say **सेव कर दो**. Reload to show database persistence.

Explain: “This is a bounded conversation using browser speech. The profile is
self-reported; speaking an e-Shram number would not verify it.”

## 2. Hear and choose a job — 2 minutes

Press **काम खोजें**. Use the optional practice card: up, down, left, right.
Point out that this sample cannot submit an application. Skip or finish the lesson.

On real cards, press **काम सुनें**. Hear the daily wage, role, city, date, shift and
experience requirement. Use **शर्तें सुनें** for full employer conditions. Optionally
enable automatic reading of each new card, then stop it visibly.

Within the marked strip, swipe up/down to navigate. Swipe left to skip, then
restore it with **पिछला छोड़ा काम लौटाएँ**. Show the equivalent buttons.

## 3. Apply and see the decision — 1–2 minutes

Swipe right. Pause on the confirmation dialog: no application exists yet.
Press **अभी नहीं** once to show safe cancellation. Then Apply → **हाँ, आवेदन भेजें**.
Show successful submission and **मेरे आवेदन**. Reload discovery: the applied job
is absent from the active stack.

In the employer window, open the vacancy, inspect the applicant's self-reported
skills and exact months, then select the worker. In the worker window, reload
applications to show **आप चुने गए / Selected**, the shift and worksite.
No payment step is involved.

## 4. Demonstrate recovery — 1 minute

Open profile editing. Stop/Pause the voice session, switch to **लिखकर भरें** and
show all fields. A microphone-denied or unsupported browser must still complete
this path. Edit a value, check the review checkbox and save.

Explain the honest boundary: “Automated tests cover software flow and failure
handling. Hindi recognition and pronunciation depend on the actual device, voice,
network and browser; we test the device before demonstrating.”

## If something fails on stage

- Unclear pronunciation / no Hindi voice: use another available Hindi voice or
  switch to typing. Do not claim the two-Mac problem is resolved without testing.
- Silence / recognition error: read the paused-state message; resume deliberately
  once or use typing. There is no endless microphone restart.
- Job filled / request fails: show the server error, cancel and choose another
  vacancy. Do not describe a failed request as a successful application.
- No jobs: post a fresh future-dated demo vacancy. Previously applied jobs are
  intentionally absent; use another vacancy/new synthetic worker for rehearsal.

Do not use an automated test's mocked speech adapter in the live product demo.
