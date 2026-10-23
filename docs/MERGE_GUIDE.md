# Integration, migration and rollback guide

This guide is for the original team to run in its own checkout. No merge, push to `main`, or change to `pujya6/ShramLink` has been performed by this handoff.

## Exact revisions and scope

Protected V3 base: **`0bea8e29aca12a2f48c08b9c748f6b7b6f127f33`**.

The delivered source ZIP contains **`HANDOFF_REVISION.json`** with the exact `final_commit`, `base_commit`, changed-file statuses and per-file hashes. Use that full final SHA from the handoff message/manifest, not a guessed latest branch head. In the following commands, replace `<FINAL_SHA>` and `<TEAM_BASE>` with reviewed literal revisions.

The release is one bounded commit above V3. It assumes the V3 architecture exists. Cherry-picking only this release into a pre-V3 application is **not** sufficient: it depends on V3 profiles, recruitment, months, categories, fixtures and external preparation models.

## Option A — team already includes V3 (preferred small integration)

Start with a clean team working tree; commit or safely set aside existing work first. Create an integration branch, never work directly on main:

```bash
git status --short
git switch -c integrate/shramlink-release <TEAM_BASE>
git remote add shramlink-handoff https://github.com/Je37-arch/ShramLink.git
git fetch shramlink-handoff feature/shramlink-v3-release
git show --stat <FINAL_SHA>
git merge-base --is-ancestor 0bea8e29aca12a2f48c08b9c748f6b7b6f127f33 HEAD
git diff --name-status 0bea8e29aca12a2f48c08b9c748f6b7b6f127f33 <FINAL_SHA>
git cherry-pick <FINAL_SHA>
```

If `shramlink-handoff` already exists, inspect its URL rather than overwriting it. The ancestor check must exit successfully for this path. After resolving conflicts, stage only reviewed files and use `git cherry-pick --continue`; abandon with `git cherry-pick --abort` if necessary. Do not discard the team's work with a blanket ours/theirs resolution.

## Option B — team has not integrated V3

Use a dedicated integration branch and fetch as above. Inspect the complete ancestry and shared base:

```bash
git merge-base HEAD <FINAL_SHA>
git log --graph --oneline --left-right HEAD...<FINAL_SHA>
git merge --no-commit --no-ff <FINAL_SHA>
```

This brings the earlier MVP/V2/V3 history as well as release hardening. It may produce substantial conflicts with the team's parallel changes. Review retained authentication, database and recruitment contracts before committing the merge. If there is no common ancestor, stop and plan a reviewed component port; do not automatically use `--allow-unrelated-histories` or copy the ZIP over the team repository. Abort an unsuitable merge with `git merge --abort`.

The complete inherited history can be large; a release-only patch is suitable only after the V3 base has been reconciled. The clean source ZIP is an inspection/setup artifact, not a substitute for Git merge ancestry.

## Likely conflict areas

| Area | Release overlap and resolution invariant |
|---|---|
| `static/js/profile-language.js` | Keep Unicode token/separator boundaries, original script/case, ambiguity handling and regression cases. JavaScript `\b` does not delimit Devanagari. |
| `static/js/discovery.js`, `templates/discovery.html` | Keep the new empty-state element IDs together with JS bindings. Preserve gesture thresholds, confirmation, undo, CSRF and explicit tutorial Listen/Replay/Stop. |
| `templates/base.html` | Retain the discreet `/inside` links while respecting the team's navigation. Do not expose configuration controls or admin routes. |
| `static/css/showcase.css`, `templates/inside.html`, `static/js/showcase.js` | New scoped files. Existing `static/css/app.css` is unchanged in this release. Integrate new styles without replacing worker styles; retain CSP-compatible external scripts. |
| `app/routes/dashboard.py`, `app/discovery_state.py` | Discovery now selects from a single unfiltered snapshot to distinguish empty causes. Do not re-enable applied/prepared cards or bypass eligibility/capacity checks. |
| `app/external_jobs.py` | New keyword-only `refresh`/`include_prepared` arguments preserve defaults for existing callers. Public preview remains local-only and signed. |
| `app/commands.py`, `app/demo_setup.py`, `app/demo_fixtures.py` | Preserve the preflight before initialization, explicit seeding, no password reset, and history-aware optional date refresh. Never call bootstrap from a public route or every server request. |
| `app/__init__.py`, `templates/service_unavailable.html` | Merge the generic SQLAlchemy 503 handler and `hide_parameters` into any team engine options without discarding their configuration. The failure template deliberately avoids another database-backed session lookup. |
| `app/routes/main.py`, `app/showcase.py` | `/inside` is a read-only page, not an operator API. Only safe configuration enums and synthetic examples are passed to its template. |
| Models / migrations | **No release model or DDL change.** If integrating V3 for the first time, reconcile its exact-month, pay/category and external preparation models with the team's schema. Never drop existing data to resolve a model conflict. |
| README / tests / docs | Keep the team's instructions and add release navigation. Keep historical V3 reports labelled historical. Update public evidence counts only after the merged code has actually been tested. |

See [RELEASE_FILE_INVENTORY.md](RELEASE_FILE_INVENTORY.md) and the archive manifest for every changed path.

## Database migration procedure

For an existing V3 installation, this release adds **zero tables and zero columns**. The existing initializer remains repeatable. Before any integration, stop writers and make a consistent database backup. Use SQLite's backup API, or copy only while all writers are stopped; an arbitrary live file copy can omit pending/WAL state.

1. Make a separate working copy of the database and point `DATABASE_URL` to its absolute path. Keep the original untouched.
2. Install the release requirements in a separate virtual environment and run `python -m flask --app run.py init-db` against the copy, then repeat it once.
3. Verify old logins, profiles, exact months, daily/monthly pay and application statuses. Do **not** run demo bootstrap on this user database.
4. Only after the merged code and migration pass review should the team schedule its own controlled upgrade with another backup.

For pre-V3 schemas, the retained additive initializer adds (when absent): user domain/years/months/location/profile completion/credential version/demo flag; job domain/years/months/worksite plus employment category, pay amount/unit and fixture key. SQLAlchemy creates missing application/security and V3 external-vacancy, demo-preparation and service-counter tables. See the exact fixed `ADDITIONS` map in `app/commands.py`, models and [V3_CONFIGURATION.md](V3_CONFIGURATION.md).

Backfill only writes month fields that are NULL. It does not round existing month precision away. Unknown legacy categories remain unspecified. Monthly pay is stored as its actual amount/unit, not converted to a fictitious daily wage. Legacy payment tables/data are not dropped and do not gate recruiting. Legacy credentials may require the retained operator password-reset process after ownership checks. PostgreSQL migration is not verified.

## Keep or disable optional services

Keep `app/interpretation.py`, `app/job_feed.py` and their models/routes in the merge. Disable through private server configuration, not code deletion:

```text
VOICE_PROVIDER=deterministic
JOB_SOURCE=demo
XAI_DAILY_REQUEST_LIMIT=0
XAI_USER_DAILY_LIMIT=0
```

Remove unused provider secrets from the host configuration if appropriate; never add them to the repository. Restart after changing environment variables. Disabling services does not delete source snapshots, profiles or preparation history.

To retain later testing, set the desired two switches independently. xAI additionally needs a private key, the allowlisted documented model and nonzero bounded quotas; establish provider billing controls first. Greenhouse needs a reviewed public board token, employer label and explicit formal-category attestation. Both retain deterministic/fixture fallback. A selected mode is not evidence of a live connection. Full variables and limits are in [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) and [V3_CONFIGURATION.md](V3_CONFIGURATION.md).

## Validation before the team merges

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium --only-shell
python -m pytest -q
node --test tests/test_voice.js
```

Also execute the new bootstrap on a fresh **separate** demo path, inspect `/inside`, complete the seven-step browser demo and check a copy of the team's real schema. Automated speech/provider mocks are not device/provider verification. Resolve any failures in the integration branch; only the team decides whether/when to merge its branch.

## Revert / rollback

- Before committing an integration, use the corresponding Git abort command above.
- After a simple release cherry-pick, use `git revert <CHERRY_PICK_SHA>` on a new rollback branch. The cherry-picked SHA differs from the source SHA. For a merge commit, identify the correct first-parent/team baseline before considering `git revert -m 1 <MERGE_SHA>`; review the resulting diff and rerun tests.
- To return a standalone installation to the protected V3 base, deploy that exact base code with its matching requirements. This hardening pass changed no schema, so V3 can read the release database. It will reintroduce the name parser defect and remove new diagnostics/showcase. New jobs/applications and explicitly refreshed fixture dates remain data; code rollback does not undo them.
- If exact pre-release data is required, stop writers, back up the current database, then restore the pre-release backup knowingly; restoring discards later activity. Do not overwrite it without review.
- Rolling back **past V3** to V2 requires the matching pre-V3 database snapshot: V2 cannot represent V3 monthly pay and external preparation correctly. Do not run V2 readers/writers against new V3 monthly vacancies.
