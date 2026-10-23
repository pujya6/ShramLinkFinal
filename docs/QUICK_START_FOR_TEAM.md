# Quick start for the ShramLink team

Start with a separate demonstration database. No paid API account is needed. If you are combining the team's own changes, read [MERGE_GUIDE.md](MERGE_GUIDE.md) first.

## Fresh local demonstration

Tested runtime: Python 3.12 and SQLite. Git is needed only for cloning; the clean source ZIP can also be extracted into a new folder.

```bash
git clone --branch feature/shramlink-v3-release --single-branch https://github.com/Je37-arch/ShramLink.git
cd ShramLink
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
export DATABASE_URL="sqlite:///$PWD/instance/demo-release.sqlite3"
export SHRAMLINK_DEMO=true
export VOICE_PROVIDER=deterministic
export JOB_SOURCE=demo
python -m flask --app run.py bootstrap-demo
python run.py
```

On Windows, activate with `.venv\Scripts\Activate.ps1` and set `$env:DATABASE_URL` to an absolute SQLite URL such as `sqlite:///C:/ShramLink/instance/demo-release.sqlite3`. Set the other variables in PowerShell or your private `.env`. Windows execution is not verified here.

At the hidden prompt, choose a password of 10–128 characters and confirm it. Do not put it in source code, screenshots, command history or chat. The first bootstrap initializes the schema and fixtures together. It should report:

```text
Visible direct: 6; eligible direct: 3; external demo previews: 2; total visible cards: 8.
```

Open **http://127.0.0.1:5000**. The count applies to the seeded welder/helper with 32 months of experience, no explicit filters and no prior actions. It is not a promise that every job matches every worker. Profiles with less experience or different skills still see cards with unmet requirements; the backend prevents an ineligible direct application.

For an existing application database without fixtures, `init-db` remains the schema command. It does not seed jobs. Do not register participants first and then try to seed their database: the safety check will refuse. Choose a new demo database path instead of deleting accounts or changing their demo flags.

## Reopen or repeat

Use the same environment/database path and run `python run.py`. Ordinary startup does not seed/reset anything. Repeat bootstrap on an all-demo database preserves passwords, profiles and decisions. If a new ordinary account has been registered, bootstrap refuses; that is expected protection, not a broken server.

Fresh fixtures start seven days after initialization. For an old isolated all-demo database, an operator may explicitly run:

```bash
python -m flask --app run.py bootstrap-demo --refresh-unused-dates
```

Only expired ACTIVE fixture jobs with **zero application history and zero hires** move seven days ahead. Used, filled, cancelled and completed jobs keep their history and dates. For a clean repeat event, use another empty database file. Never silently recycle old applications.

## Seven-step evaluator demonstration

1. **Landing:** show the Worker and Employer entry points and Hindi three-step journey.
2. **Onboarding:** register a new synthetic worker using an unused demonstration phone number and your chosen password. Use Hindi audio preflight; say “जी, मेरा नाम जीत झा है”, age 25, welder, manufacturing, “दो साल आठ महीने”, Delhi; skip e-Shram. Inspect the intact name and 32 months, then explicitly confirm. If device speech fails, use the visible Type control. Do not call that a successful physical voice test.
3. **Ready profile:** for a short reliable path, separately log in as `worker.v3@example.invalid` with the bootstrap password. It already has welder/helper, Delhi and 32 months.
4. **Populated stack:** open Find Work. Expect 1 / 8 on a fresh database. Open Help, click Listen, replay, Stop and practise; practice cannot apply. Navigate up/down or Next/Previous. Skip and undo. Clear any explicit city/skill filters if needed.
5. **Direct recruitment:** on the Delhi welder card, Apply → explicit confirmation. In a separate browser profile/private window, log in as `employer1.v3@example.invalid`, review applicants and select. Reload the worker dashboard to see Selected. Repeated confirmation must not create a duplicate.
6. **External demonstration:** navigate to the labelled external helper/welder card. Review source, saved profile and missing information. Confirm local preparation. Show **Demo application prepared — not submitted externally** and the persistent Hindi/English notice. No application reaches a third party.
7. **Judge guide:** open **Inside ShramLink** in the footer or `/inside`. Follow the architecture, requested/effective modes and synthetic examples. Open the release evidence and integration guide.

Employer accounts `employer1.v3@example.invalid` through `employer4.v3@example.invalid` share the initial operator-chosen password on first creation. No default password is shipped. Employer 1 owns the Delhi welder/helper fixtures; employer 2 owns the Noida monthly welder.

## If the stack is empty

| Message / situation | Recovery |
|---|---|
| Demo jobs not prepared | Ask the operator to use the fresh bootstrap sequence; workers never receive admin controls |
| No vacancies at all | Wait for a posting or use a separate initialized demo installation |
| No filter matches | Clear city/skill filters with All jobs |
| Direct eligibility unmet | Inspect requirements; correct genuinely incorrect profile data, never invent skills/experience |
| All cards skipped | Use Restore skipped jobs; skips are browser-session state |
| Already applied/prepared | Open My applications; these cards are deliberately excluded from the active stack |
| Dates passed / filled / cancelled | Start a new isolated event database, or explicitly refresh only unused fixture dates |
| Server unavailable | Retry later; check My applications after recovery before assuming a request failed |

## No local tooling?

The team can review the source, documentation and screenshot evidence in GitHub without running it. For an interactive hosted demonstration later, use the browser-dashboard setup described in [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md). That needs a team-owned hosting account and persistent storage; no hosting has been set up on the team's behalf. Public deployment is not a condition of this handoff.
