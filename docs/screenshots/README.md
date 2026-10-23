# V2 → V3 visual evidence

Open [index.html](index.html) locally to compare landing, onboarding, worker dashboard and job discovery side by side at 390×844, 768×1024 and 1440×1000. Captures are full-page; image heights can exceed the viewport. All 24 core screenshots were visually inspected. Data and identities are synthetic demonstration fixtures, not real workers.

V2 captures use archived commit `06f83a2f6f25eee607922a12b53712a5d97b2907`. V3 captures use the release code. The common page structure, hierarchy, conversation stage, worker action/profile card and job information block materially change; this is more than a colour/spacing adjustment.

From the V3 checkout with development dependencies and Chromium installed:

```bash
python scripts/capture_screenshots.py --label v3
```

To reproduce the before comparison without switching or writing a protected branch:

```bash
mkdir -p /tmp/shramlink-v2-screenshot-source
git archive 06f83a2f6f25eee607922a12b53712a5d97b2907 | tar -x -C /tmp/shramlink-v2-screenshot-source
python scripts/capture_screenshots.py --source /tmp/shramlink-v2-screenshot-source --label v2
```

The script starts a local server with a temporary database and generated credentials, then disposes them. It does not use or persist login cookies from a real account. The displayed date changes with the capture date.

Supplementary current-V3 mobile images show [external preparation](v3/external-prepared-390.png), [tutorial practice](v3/tutorial-390.png) and [voice review](v3/voice-review-390.png). These are emitted by browser tests; the voice review uses simulated speech events. Screenshots do not verify physical audio quality, recognition accuracy or public deployment.
