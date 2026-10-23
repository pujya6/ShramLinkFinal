# ShramLink V3 release candidate — team handoff

This is an integration handoff, not a deployment. No hosting was provisioned or published. The original team's repository, `main`, V2 and the V3 baseline are not write targets.

## Revision identity

- Repository: https://github.com/Je37-arch/ShramLink
- Release branch: `feature/shramlink-v3-release`
- Exact protected base: **`0bea8e29aca12a2f48c08b9c748f6b7b6f127f33`** (`feature/shramlink-v3`).
- Exact final revision: recorded in the delivered source archive's **`HANDOFF_REVISION.json`**, alongside the base, every changed path and SHA-256 hashes of included files. In a Git checkout, `git rev-parse HEAD` must equal that final revision. The final handoff message also provides the full SHA. A commit cannot embed its own hash in its contents.

## Bounded changes

1. Hindi filler/negation removal now requires whole tokens. `जीत झा`, `जीवन कुमार` and `जीतेन्द्र शर्मा` survive parsing. Corrections preserve Roman name case. Final profile review remains mandatory. Previously truncated stored names are **not guessed or automatically repaired**; edit those profiles explicitly.
2. `bootstrap-demo` inspects a configured SQLite database before migration, initializes a fresh demo file, seeds the existing six direct/two external fixtures and reports the seeded worker's actual visible/eligible counts. Repeat calls preserve passwords, outcomes and dates. Date renewal is a separate explicit flag for expired, unused, active fixtures only.
3. Discovery explains uninitialized demonstrations, no jobs, filter misses, unavailable jobs, already reviewed opportunities and skipped cards. Ineligible direct cards remain inspectable with a profile-check action. City remains a ranking factor unless the worker explicitly filters by city.
4. `/inside` is a public, read-only judge guide with the actual architecture, four settings combinations, configuration/fallback distinction, fixed synthetic matching examples and the real duration parser. It has no microphone, cloud requests, saving, application or administration controls.
5. Database failures return a generic recoverable 503 without SQL parameters/connection details. Existing authentication, CSRF, authorization, uniqueness and vacancy-capacity rules remain.
6. Clean source packaging, integration instructions and operator documentation complete the handoff. The worker/employer visual design and all optional V3 adapters are retained.

## Start here

- [Quick start and seven-step browser demo](QUICK_START_FOR_TEAM.md)
- [Judge showcase guide](JUDGE_SHOWCASE.md)
- [Newly executed release tests](RELEASE_TEST_RESULTS.md)
- [Known limitations](KNOWN_LIMITATIONS.md)
- [Merge, migration and rollback guide](MERGE_GUIDE.md)
- [File-by-file release inventory](RELEASE_FILE_INVENTORY.md)
- [Deployment readiness checklist and environment reference](DEPLOYMENT_CHECKLIST.md)

## Database impact

**No new tables, columns or migrations relative to the exact V3 base.** `app/models/__init__.py` and the fixed additive DDL map are unchanged. The new bootstrap calls the existing initializer only after inspecting for non-demo/unknown data. It never deletes records, resets accounts, changes decisions or reopens filled/cancelled jobs.

Older team branches still need the inherited V1/V2/V3 additive migration; see the merge guide. Never seed a genuine worker database. A demonstration database containing a newly registered non-demo participant makes repeat bootstrap refuse safely; normal app startup and recruitment still work. Seed before registering participants. For a new event, use a new isolated database path and retain the old database.

## Demonstration policy

Direct ShramLink applications operate within the isolated demo. External preparation is stored separately with **Demo application prepared — not submitted externally**. No application sender exists. Fictional jobs remain explicitly labelled. Identities, skills and employment categories are unverified self-reported/source claims.

V3b is the no-paid-service default. API interpretation and public feed sourcing remain configurable independently; their implementations have not been removed. Physical Hindi audio, live authenticated xAI behaviour and public hosting remain unverified.

## Source package

After checkout of the final commit:

```bash
python scripts/package_handoff.py --output ../ShramLink-v3-release-source.zip
```

The command reads committed Git blobs, not the working directory. It excludes private environment files, databases, cookies/sessions, keys, caches, virtual environments and Git internals, and rejects common credential patterns. `.env.example` is an empty configuration template; tests contain explicitly synthetic credentials only. `HANDOFF_REVISION.json` records exclusions and exact content hashes. Review it before distributing. The archive contains no Git history, so secrets in old history are not copied; any historically exposed credentials still require rotation.

The ZIP is for inspection and clean setup. Use the Git-based procedure for merging, not a blanket ZIP overwrite of the team's working tree. The presentation remains unchanged.
