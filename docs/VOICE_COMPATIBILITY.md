# Hindi voice compatibility — V2 baseline and V3

**No physical-device Hindi speech combination has been verified during this V2/V3
implementation.** Automated tests simulate speech events in Chromium. They prove
software state transitions and fallbacks, not recognition accuracy or pronunciation.

## What was investigated

The V1 code set `lang = hi-IN` and selected a Hindi voice when present, but could
continue without a selected Hindi voice. Voice enumeration can initially be empty.
V2 waits a bounded interval, subscribes to `voiceschanged`, deliberately selects
only `hi`, `hi-*` or `hi_*` candidates and refuses synthesis if none is available.
The picker is available whenever candidates exist, including multiple choices.
No English voice is silently substituted.

The user's report that one Mac repeatedly spoke “question mark” is **unresolved on
physical hardware**. A fallback voice, engine/OS voice data, or punctuation handling
could contribute; these are hypotheses, not a diagnosed cause. V2 uses explicit
voice objects, correct Devanagari, moderate rate (0.88), short sequential utterances,
and sentence pauses in spoken output. Question punctuation is rendered normally
in the UI and converted to a Devanagari sentence pause for synthesis. There are no
arbitrary English phonetic rewrites. These changes are not proof of a Mac fix.

## Device preflight

1. Use localhost or an HTTPS deployment. Close other speaking tabs and check the
   microphone, speaker volume, network and browser site permissions.
2. Open **आवाज़ जाँचें**. If no Hindi voice appears, install/enable a Hindi system
   voice where supported, reopen the browser and try again. Otherwise use typing.
3. Select a Hindi voice and play **नमस्ते। आपका नाम क्या है?**. A `hi-IN` label
   alone does not establish quality. Reject English-sounding output, spoken
   punctuation, missing words or silence; try a different Hindi voice or typing.
4. Play the retroflex sample: **टमाटर। ठंडा पानी। डिब्बा। ढक्कन। निर्माण।**
   Have a fluent Hindi listener assess ट, ठ, ड, ढ and ण. Confirm ण in निर्माण is
   distinct as appropriate for the selected speaker. No automated score is claimed.
5. Start a conversation, allow the microphone, say yes to the audio check, then
   answer without repeated taps. Verify that speech stops before listening starts.
6. Test correction, repeat, back, silence, permission denial, Stop, background/
   foreground, and typing. Check that a full review needs explicit confirmation.
7. Test a vacancy with actual daily pay/time/month requirement. Replay, interrupt,
   change card and enable/disable automatic reading. Listen to full conditions.

Record **device model, OS version, browser/version, selected voice name/language,
network mode, microphone/speaker setup, listener, date and results**. Do not record
private worker speech or use real IDs in demonstrations.

## Current evidence matrix

| Environment | UI / lifecycle | Physical Hindi audio |
| --- | --- | --- |
| Linux, headless Chromium 141.0.7390.37, Playwright 1.56.0 | Automated forms, real pointer/keyboard actions and simulated speech events | Not tested |
| Chromium at 320, 360, 390, 768 and 1440 CSS px | Responsive browser layout checks; V3 before/after screenshots at 390, 768 and 1440 | Not a physical phone test |
| macOS + Chrome / Safari, including the two reported Macs | Not executed on physical devices in this run | Required; reported discrepancy remains unresolved |
| Android + Chrome | Target for device preflight; not verified | Required |
| iPhone/iPad + Safari | Target for device preflight; not verified | Required |
| Windows + Edge / Chrome | Not verified | Required |
| Firefox or other browser with missing recognition/voice | Missing-API fallback is simulated; typing remains available | No voice-support guarantee |

## Failure and cancellation policy

- No Hindi voice after 2.5 seconds: pause; use voice settings or typing.
- Synthesis error/stall (25 seconds per short utterance): cancel and pause.
- Recognition silence (12 seconds): one retry, then pause. Repeated unclear
  answers and the overall session also have strict budgets.
- Permission, hardware, service/network/language error: pause, explain recovery,
  retain entered values and offer typing. There is no paid speech-service fallback.
- Late/duplicate events are ignored. Recognition must signal its end before the
  next spoken question. Missing shutdown blocks further audio.
- Backgrounding, Stop or Type cancels active speech and listening. Resume needs
  another deliberate action. “Stop” cannot be heard while TTS is speaking because
  the microphone is deliberately off; the persistent Stop button interrupts then.

Browser speech recognition may require the vendor's network service. No offline
claim is made. Some engines require further gestures after interruption; this is
an explicit resume/fallback situation, not a universal hands-free guarantee.
Employer-provided English text and names remain verbatim; fluent Hindi translation
of arbitrary job descriptions is outside the bounded system.

## V3 additions and evidence (2026-10-23)

The native speech infrastructure and bounded V2 turn manager remain in place.
The redesigned interface keeps Pause, Stop and Type visible; on unsupported
recognition, permission failure or other voice errors, the typing form opens.
All 32 previous browser tests pass on V3, alongside 13 new browser tests.

The tutorial now separates **Listen/Replay** from **Stop**. Opening it automatically
does not speak. An explicit Listen click starts narration and enables automatic
reading of subsequent lessons. The same Hindi voice picker and synthesis service
are used as onboarding and job descriptions. Simulated browser tests verify each
lesson, replay, stop, missing voice and synthesis failure. They do not establish
physical pronunciation quality or prove the reported manual audio defect fixed.

Optional API interpretation changes text understanding only; it does not replace
recognition or synthesis. Known local answers, e-Shram input and final confirmation
remain local. Unresolved short answers may be sent to xAI only in a configured,
disclosed API session. Timeout/error returns to local clarification. Pausing
ignores late provider results. No paid xAI request was made in this environment.

Before a live demonstration, extend the device preflight above with tutorial
Listen → replay → next lesson → Stop → close, and a monthly-pay vacancy summary.
No additional physical browser/device combinations have been verified for V3.

## Reference documentation

- [MDN: getVoices](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis/getVoices)
- [MDN: voiceschanged](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis/voiceschanged_event)
- [MDN: SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)
- [MDN: SpeechSynthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis)

These API references inform the implementation; their availability tables do not
substitute for ShramLink device and pronunciation testing.
