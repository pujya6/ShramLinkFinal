# ShramLink

ShramLink is a Hindi-first employment demonstrator that helps industrial workers in Delhi–NCR discover suitable opportunities and helps employers manage applicants. It is built as a server-rendered Flask application with SQLite for local development.

> This project is a demonstrator. Job listings, accounts, and application outcomes created by the demo tools are fictional. ShramLink does not verify identities or qualifications, guarantee employment, process payments, or submit applications to third-party services.

## What it does

- Provides distinct worker and employer journeys with Hindi and English guidance.
- Guides workers through profile setup, including skills, location, domain, and exact experience in months.
- Shows eligible and ineligible job cards with clear requirements and filters.
- Supports internal job applications and employer-side applicant decisions.
- Includes accessible controls alongside swipe-style job discovery interactions.
- Provides optional speech-assisted onboarding; every flow also works with typed input.
- Supports labelled external-vacancy previews and local application preparation only—nothing is submitted to an external provider.
- Includes a guarded, repeatable demo bootstrap with fictional accounts and vacancies.

## Technology

- Python 3.10+
- Flask, Flask-Login, Flask-WTF, and SQLAlchemy
- SQLite by default (configurable with `DATABASE_URL`)
- Jinja templates and browser JavaScript
- Pytest, Playwright, and Node’s built-in test runner for verification

## Quick start

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/pujya6/ShramLinkFinal.git
cd ShramLinkFinal
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Choose an isolated database for the demonstration, enable demo tools, and prepare the fictional data:

```bash
export DATABASE_URL="sqlite:///$PWD/instance/demo.sqlite3"
export SHRAMLINK_DEMO=true
export VOICE_PROVIDER=deterministic
export JOB_SOURCE=demo
python -m flask --app run.py bootstrap-demo
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The bootstrap command prompts for a demonstration password and creates only fictional demo data.

On Windows, activate the environment with `.venv\Scripts\activate` and set environment variables with PowerShell syntax. The app can be initialized without demo data by running `python init_db.py`.

## Demo accounts

After `bootstrap-demo`, use the password chosen at the prompt with these seeded accounts:

| Account | Purpose |
| --- | --- |
| `worker.v3@example.invalid` | Worker with a completed welder/helper profile |
| `employer1.v3@example.invalid` – `employer4.v3@example.invalid` | Fictional employer accounts |

For the most reliable workflow, use a fresh database before bootstrapping. The command intentionally refuses to seed a database that contains ordinary (non-demo) accounts. It preserves existing demo profiles, decisions, and application history rather than resetting them.

## Configuration

Copy `.env.example` to `.env` for local configuration. Important settings include:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Database URL; defaults to `instance/shramlink.sqlite3` |
| `SECRET_KEY` | Session-signing key; production requires a fresh value of at least 32 characters |
| `SHRAMLINK_ENV` | Set to `production` to enable production session and transport safeguards |
| `SHRAMLINK_DEMO` | Enables explicit demo fixture commands |
| `VOICE_PROVIDER` | `deterministic` for the local demo or `api` when optional API configuration is complete |
| `JOB_SOURCE` | `demo` for local fixtures or `integrated` for configured external retrieval |
| `GREENHOUSE_BOARD` / `GREENHOUSE_EMPLOYER` | Optional public Greenhouse board configuration |
| `XAI_API_KEY` / `XAI_MODEL` | Optional server-side interpretation configuration |

Never commit `.env`, databases, session keys, or API credentials. See [docs/V3_CONFIGURATION.md](docs/V3_CONFIGURATION.md) for the full configuration and migration notes.

## Running tests

Install development dependencies and run the test suites:

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium --only-shell
python -m pytest -q
node --test tests/test_voice.js
```

The browser tests use temporary databases and synthetic accounts. Speech and authenticated external-service responses are simulated in automated tests.

## Security and privacy notes

- Passwords are hashed; sessions use HTTP-only cookies and CSRF protection.
- The app applies restrictive security headers, including CSP and clickjacking protection.
- Raw audio and speech transcript histories are not stored by the application.
- Optional services use server-side configuration only; never place keys in client-side code.
- Browser speech recognition may rely on a browser vendor’s online service.

Before any deployment, use a persistent database, generate a new `SECRET_KEY`, set `SHRAMLINK_ENV=production`, rotate any previously exposed credentials, and follow the [deployment checklist](docs/DEPLOYMENT_CHECKLIST.md).

## Documentation

- [Team quick start](docs/QUICK_START_FOR_TEAM.md)
- [Demo script](docs/V3_DEMO_SCRIPT.md)
- [Configuration and migration guide](docs/V3_CONFIGURATION.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [Deployment checklist](docs/DEPLOYMENT_CHECKLIST.md)
- [Release test results](docs/RELEASE_TEST_RESULTS.md)

## License

No license file is currently included in this repository. All rights remain with the project owner unless a license is added.
