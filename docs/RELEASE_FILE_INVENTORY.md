# Release file inventory

Compared with exact V3 base `0bea8e29aca12a2f48c08b9c748f6b7b6f127f33`. The archive `HANDOFF_REVISION.json` records the corresponding exact final SHA and machine-readable changed paths.

**Schema delta: none.** `app/models/__init__.py`, the `ADDITIONS` map, runtime dependencies, `static/css/app.css`, the conversational state manager, Hindi speech service and xAI/Greenhouse provider implementations are unchanged. Existing V3 documentation is preserved.

| Status | Path | Purpose / integration note |
|---|---|---|
| Modified | `README.md` | Release navigation and bootstrap-first fresh demo instructions; V3 material retained. |
| Modified | `app/__init__.py` | Generic SQLAlchemy 503 handler and hidden SQL parameters; existing security retained. |
| Modified | `app/commands.py` | Adds operator-only bootstrap-demo command; fixed additive DDL unchanged. |
| Modified | `app/demo_fixtures.py` | Refuses NULL/non-demo flags and fixture identity role mismatches; no fixture replacement. |
| Added | `app/demo_setup.py` | New pre-migration guard, combined initialization/seeding, explicit unused-date refresh and counts. |
| Added | `app/discovery_state.py` | New worker-safe discovery reason and recovery selection. |
| Modified | `app/external_jobs.py` | Optional read-only refresh/include-prepared flags; default adapter behaviour retained. |
| Modified | `app/routes/dashboard.py` | Selects discovery from one unfiltered snapshot; supplies safe reason context. |
| Modified | `app/routes/main.py` | Adds public GET /inside; health endpoint retained. |
| Added | `app/showcase.py` | Safe revision/evidence metadata and synthetic examples using the actual matcher. |
| Added | `docs/DEPLOYMENT_CHECKLIST.md` | Release operator/integration documentation. |
| Added | `docs/FINAL_HANDOFF.md` | Release operator/integration documentation. |
| Added | `docs/JUDGE_SHOWCASE.md` | Release operator/integration documentation. |
| Added | `docs/KNOWN_LIMITATIONS.md` | Release operator/integration documentation. |
| Added | `docs/MERGE_GUIDE.md` | Release operator/integration documentation. |
| Added | `docs/QUICK_START_FOR_TEAM.md` | Release operator/integration documentation. |
| Added | `docs/RELEASE_FILE_INVENTORY.md` | Release operator/integration documentation. |
| Added | `docs/RELEASE_TEST_RESULTS.md` | Release operator/integration documentation. |
| Added | `docs/screenshots/release/index.html` | Synthetic visual evidence / local screenshot gallery. |
| Added | `docs/screenshots/release/inside-1440.png` | Synthetic visual evidence / local screenshot gallery. |
| Added | `docs/screenshots/release/inside-390.png` | Synthetic visual evidence / local screenshot gallery. |
| Added | `docs/screenshots/release/inside-768.png` | Synthetic visual evidence / local screenshot gallery. |
| Added | `docs/screenshots/release/populated-stack-390.png` | Synthetic visual evidence / local screenshot gallery. |
| Added | `scripts/package_handoff.py` | Builds source ZIP from committed blobs with exact revision/path/hash manifest. |
| Added | `static/css/showcase.css` | New scoped guide styles; existing app.css is unchanged. |
| Modified | `static/js/discovery.js` | Skipped/applied exhaustion explanations and restore action; gestures/tutorial unchanged. |
| Modified | `static/js/profile-language.js` | Whole-token filler/negation/correction boundaries; preserves original names/case. |
| Added | `static/js/showcase.js` | Read-only examples; no fetch, microphone, persistence or account mutation. |
| Modified | `templates/base.html` | Discreet showcase links in public navigation/footer. |
| Modified | `templates/discovery.html` | Reason-specific empty/recovery and ineligibility messages including no-JS paths. |
| Added | `templates/inside.html` | Architecture, modes, evidence links and synthetic interactive examples. |
| Added | `templates/service_unavailable.html` | Standalone recovery page avoids another database-backed user lookup. |
| Added | `tests/test_browser_release.py` | Voice name persistence, seeded/new worker flows, local preparation, skip recovery and guide layouts. |
| Added | `tests/test_handoff_package.py` | Private-file filtering, provenance manifest and credential-canary rejection. |
| Added | `tests/test_release.py` | Bootstrap, migration refusal, diagnostics, modes, matching and failure tests. |
| Modified | `tests/test_voice.js` | Adds name-prefix, correction/negation and optional-ID regressions. |

No deleted source files. No real environment, database, cookie/session, credential, cache or virtual-environment files are included. New tests use synthetic credentials only. Historical source images/docs are retained in the full source archive; their older evidence dates/counts are not new release claims.

The largest likely release conflicts are discovery routes/template/JS, parser boundaries, app setup/error handling and shared navigation. Model conflicts concern the earlier V3 integration if the team has not incorporated it. See [MERGE_GUIDE.md](MERGE_GUIDE.md) before resolving them.
