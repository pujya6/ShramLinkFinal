# ShramLink Development Log

## 23 October 2026 — Documentation refresh

### Current status

- The application source and its existing implementation documentation are unchanged.
- Documentation describes the current Flask, SQLite, and V3 demo workflow in this repository.

### Next steps

- Keep this log updated as features, configuration, testing, or deployment status changes.
- Add an explicit license before distributing or reusing the project outside the intended scope.
- Record production deployment details only after they have been verified.


### tech stack
1. BACKEND (PYTHON FLASK)
- Flask (Version 3.1.3): Core web framework
- Flask-SQLAlchemy (Version 3.1.1): ORM / database abstraction layer
- Flask-Login (Version 0.6.3): User session authentication
- Flask-WTF (Version 1.2.2): CSRF-protected form handling
- Werkzeug (Version 3.1.9): WSGI utilities and password hashing
- SQLAlchemy (Version 2.1.6): Core database ORM engine
- python-dotenv (Version 1.2.2): Environment configuration management
- gunicorn (Version 23.0.0): Production WSGI server
- tzdata (Version 2025.2): Timezone database



2. DATABASE
- Primary Database: SQLite (file-based at instance/shramlink.db)
- Migrations: Manual schema evolution via init_database() + ALTER TABLE execution
- Core Models: User, Job, JobApplication, VerificationRequest, and associated entities



3. FRONTEND (SERVER-RENDERED & VANILLA JS)
- Templates: Jinja2 (server-rendered HTML)
- Styling: Custom CSS (static/css/app.css) — framework-free
- Typography: Noto Sans Devanagari (self-hosted WOFF2)
- Icons: Inline SVG (templates/_icons.html)
- JavaScript Architecture: Vanilla ES6 modules (bundler-free)



4. VOICE / SPEECH (BROWSER APIS)
- SpeechRecognition: Hindi voice input (hi-IN, with en-IN fallback)
- SpeechSynthesis: Hindi text-to-speech (TTS) responses
- MediaRecorder: Audio capture for review and processing
- Web Audio API: Real-time audio visualization (voice waves)
- Optional X AI




5. KEY JAVASCRIPT MODULES (static/js/)
- voice-assistant.js: Manages conversational AI flow and Hindi Q&A interactions
- hindi-speech.js: Wrapper utility for SpeechRecognition and SpeechSynthesis
- discovery.js: Handles the job feed interface with voice search capabilities
- profile-language.js: Manages Hindi/English profile text toggles and rendering
- app.js: Global initialization, navigation routing, and shared utilities
