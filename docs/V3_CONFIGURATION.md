# V3 configuration and migration guide

## One shared application

`VOICE_PROVIDER=deterministic|api` and `JOB_SOURCE=demo|integrated` are independent server settings. All modes share templates, CSS, database models, login, CSRF, profiles and direct recruitment. Invalid enum values fail startup; API request limits are restricted to 0–240. Workers cannot change server configuration.

V3b (`deterministic` + `demo`) is the default. `SHRAMLINK_DEMO=true` permits explicitly seeded fixtures; it does not automatically seed users or label ordinary accounts as fictional. Use a dedicated demonstration database. Demo credentials must be chosen by the operator.

A demo/admin-only banner reports effective versus requested mode. API errors are also reported in the conversation, which returns to the deterministic parser. Feed errors/empty results get worker-visible messages. A missing integration does not disable direct jobs, profiles or typed onboarding.

## xAI adapter

Set `VOICE_PROVIDER=api`, `XAI_API_KEY` privately and `XAI_MODEL=grok-4.3`. This bounded implementation deliberately allowlists that documented model because it supports disabling reasoning; arbitrary future models may have different cost/parameter behaviour. No key or model means deterministic fallback.

The adapter uses `POST https://api.x.ai/v1/responses`, `store:false`, `reasoning.effort:none`, a strict JSON schema, 384 visible output tokens and no tools. It sends one unresolved answer and its field identifier, without prior dialogue, saved profile, phone, email or e-Shram field. Input is limited to 400 characters and the full serialized provider request to 12,000 bytes. Network timeout is six seconds; browser timeout eight seconds; responses are limited to 32 KB. There is no automatic provider retry. Cancellation ignores late output but cannot guarantee cancellation of provider billing.

The local parser handles known answers first. The model can suggest an answer, correction or ambiguity only. A local fixed-schema validator checks keys, types, bounds, allowed vocabularies, quoted evidence and current-field constraints. Name extraction must occur literally in the input. Clarification suggestions are reduced to a fixed Hindi question for that field; arbitrary model instructions never reach the dialogue controller. The complete profile is validated again at explicit save. Semantic extraction can still be wrong; review is essential.

Database-backed atomic counters limit attempts to eight/minute/worker, 30/day/worker and 60/day globally by default, across app processes sharing the same database. Failed attempts consume the budget. Set both daily limits to 0 to disable paid requests. Maximum configurable daily limit is 240. These caps and token limits bound usage; they are not a provider-side monetary hard limit. Set a provider billing cap as well.

`/admin/service-status` is administrator-only. It reports attempts, successes, failures, rate-limit events and provider-reported input/output tokens. Optional prices in `XAI_INPUT_USD_PER_MILLION` and `XAI_OUTPUT_USD_PER_MILLION` produce a cumulative USD estimate; zero means no estimate. Timeouts/missing usage can make the estimate incomplete. No prompts, credentials or transcripts are stored in counters.

No xAI key was present in this implementation environment. **No paid xAI request was made; real latency, extraction quality, token billing and error behaviour are unverified.** Mock responses exercise the contract and fallback without pretending to be a cloud connection.

Official documentation checked 2026-10-23:

- [Responses API](https://docs.x.ai/developers/rest-api-reference/inference/responses)
- [Structured outputs](https://docs.x.ai/developers/model-capabilities/text/structured-outputs)
- [Grok 4.3 model and reasoning options](https://docs.x.ai/developers/models/grok-4.3)
- [Output limits and sampling](https://docs.x.ai/developers/model-capabilities/text/best-practices)

The documented output cap applies to visible output; reasoning is explicitly disabled. Verify availability and current prices in your provider account before enabling.

## Greenhouse adapter

Set `JOB_SOURCE=integrated`, `GREENHOUSE_BOARD` to a public board token, and `GREENHOUSE_EMPLOYER` to the actual employer. Before setting `GREENHOUSE_FORMAL_ATTESTED=true`, the operator must review the source and explicitly attest the category. A structured listing alone is not proof of formal employment. The UI states that the category is an operator/source claim, not ShramLink verification. With missing settings, the app falls back to demonstration mode.

Only `GET https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true` is implemented. The hostname is fixed, tokens are validated, redirects are refused, responses are limited to 2 MB / 2,000 posts and the socket timeout is five seconds. A database counter permits at most one refresh per 15-minute bucket and 48 attempts/day/board. Old cache entries expire after 24 hours; a successful refresh retires vanished posts. Failures preserve only unexpired cached opportunities and display a warning. Each card carries source, original HTTPS Greenhouse URL and retrieval time. Missing fields stay unknown; source text is sanitized to plain text and may be shortened.

Only explicit welder, electrician, helper, loader, painter and mason/construction-worker titles in Delhi, Noida, Greater Noida, Gurugram/Gurgaon, Faridabad or Ghaziabad are accepted. The adapter does not mistake a software or sales job mentioning manufacturing for industrial work. External eligibility is never marked verified; local preparation can show missing qualifications without allowing an internal hire.

Evaluation: Impinj's public `impinjexternal` board returned 20 postings on 2026-10-23, with **zero** supported NCR industrial-role matches. Quince's board timed out/was unavailable in this environment. No live imported opportunity is claimed for the recorded demonstration. Use the clearly labelled fixtures. The adapter is reusable with an operator-reviewed relevant public board; relevance is not guaranteed.

Sources: [official Job Board API](https://docs.greenhouse.io/job-board), [Impinj public board](https://job-boards.greenhouse.io/impinjexternal). Neither an application POST nor an application API key exists in this integration.

## Safe database upgrade

Supported/tested database: SQLite. Use a persistent disk for hosting; PostgreSQL migrations have not been validated.

1. Stop writers and back up the existing SQLite database using the SQLite backup facility (include the consistent database state, not an arbitrary copy during writes).
2. Check out `feature/shramlink-v3`; install `requirements.txt` in your virtual environment.
3. Point `DATABASE_URL` to the absolute path of the copied/target database, then run `python -m flask --app run.py init-db`.
4. Run `init-db` again to check repeatability, start the app and verify an existing login, exact experience months, old vacancy and application status.

The command adds `jobs.employment_category`, `wage_amount`, `wage_unit`, `fixture_key` and four separate tables: `external_vacancies`, `demo_preparations`, `service_budgets`, `service_metrics`. Legacy years-to-month backfill runs only where months are NULL. Category NULL renders “Direct · category unspecified”, rather than silently labelling old records formal/informal. Legacy wages remain per day. New monthly jobs store their amount/unit in V3 columns; the old required daily-wage column holds 0, never a fabricated conversion.

No legacy records or payment tables are dropped. V3 never reads payment status to permit recruiting. Do not run V2 readers/writers on a V3 monthly-pay dataset. For rollback, stop V3, restore the pre-V3 database backup and V2 code together. New V3 activity cannot be represented faithfully in V2.

## Service counter maintenance

Counters contain identifiers and counts, not transcripts. Time-window budget rows are retained; their count grows over use. For a long-lived service, add an operator-managed retention job for expired buckets after reviewing audit requirements. Do not clear current-day counters to work around spending caps. Provider snapshots and local demonstration preparations persist until the operator resets the isolated demonstration database or implements a reviewed retention policy.
