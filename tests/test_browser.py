"""Real Chromium UI tests. Speech APIs are explicitly mocked in voice tests.

Run: python -m playwright install chromium --only-shell
     python -m pytest -q tests/test_browser.py
"""

from datetime import date, timedelta
from pathlib import Path

import pytest
from conftest import TEST_PASSWORD, account
from playwright.sync_api import expect

from app.models import UserRole

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "test-results"


def layout(page):
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        page.url
    )


def fill_profile(page, name="परीक्षण श्रमिक"):
    page.locator("#name").fill(name)
    page.locator("#age").fill("26")
    page.locator("input[name=skills][value=welder]").check()
    page.locator("#preferred_domain").select_option("manufacturing")
    page.locator("#experience_months").fill("36")
    page.locator("#location").select_option("Delhi")
    page.locator("#confirmed").check()


def login_ui(page, url, email):
    page.goto(url + "/login")
    page.locator("#identifier").fill(email)
    page.locator("#password").fill(TEST_PASSWORD)
    page.locator("button[type=submit]").click()


def worker_page(app, browser, live, mock=False, **options):
    account(app, UserRole.LABORER, "voice-test@example.invalid")
    context = browser.new_context(viewport={"width": 390, "height": 844}, **options)
    if mock:
        context.add_init_script(path=str(ROOT / "tests/fixtures/mock_speech.js"))
    page = context.new_page()
    login_ui(page, live, "voice-test@example.invalid")
    expect(page).to_have_url(live + "/onboarding")
    return context, page


def say(page, text):
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    page.evaluate("(text)=>window.__speech.result(text)", text)


def test_mobile_typed_recruitment_journey(app, browser, live):
    errors = []
    bad_responses = []
    worker_context = browser.new_context(viewport={"width": 390, "height": 844})
    worker_context.add_init_script(
        "Object.defineProperty(window,'SpeechRecognition',{value:undefined});Object.defineProperty(window,'webkitSpeechRecognition',{value:undefined});"
    )
    worker = worker_context.new_page()
    worker.on("pageerror", lambda error: errors.append(str(error)))
    worker.on(
        "response",
        lambda response: (
            bad_responses.append(response.status) if response.status >= 400 else None
        ),
    )
    worker.goto(live + "/")
    layout(worker)
    RESULTS.mkdir(exist_ok=True)
    worker.screenshot(path=str(RESULTS / "home-mobile.png"), full_page=True)
    worker.goto(live + "/register/laborer")
    worker.locator("#phone").fill("6999999902")
    worker.locator("#password").fill(TEST_PASSWORD)
    worker.locator("#confirm_password").fill(TEST_PASSWORD)
    worker.locator("button[type=submit]").click()
    expect(worker.locator("#start-voice")).to_be_disabled()
    fill_profile(worker)
    worker.locator("#save-profile").click()
    expect(worker).to_have_url(live + "/dashboard/laborer")
    layout(worker)
    employer_context = browser.new_context(viewport={"width": 390, "height": 844})
    employer = employer_context.new_page()
    employer.on("pageerror", lambda error: errors.append(str(error)))
    employer.goto(live + "/register/manager")
    for field, value in dict(
        name="Demo hiring lead",
        factory_name="Demo Fabrication",
        factory_address="Demo Delhi worksite",
        email="ui-employer@example.invalid",
        password=TEST_PASSWORD,
        confirm_password=TEST_PASSWORD,
    ).items():
        employer.locator("#" + field).fill(value)
    employer.locator("button[type=submit]").click()
    layout(employer)
    employer.get_by_role("link", name="+ Post a vacancy").click()
    layout(employer)
    for field, value in dict(
        title="Arc welder — demo shift",
        worksite_address="Demo industrial area, Delhi",
        wage="850",
        workers="1",
        min_experience_months="12",
        start_date=(date.today() + timedelta(days=1)).isoformat(),
        shift="09:00–17:00",
        requirements="Arc welding; safety equipment provided.",
    ).items():
        employer.locator("#" + field).fill(value)
    for field, value in dict(
        skill="welder", domain="manufacturing", location="Delhi", employment_category="direct_informal", wage_unit="day"
    ).items():
        employer.locator("#" + field).select_option(value)
    employer.get_by_role("button", name="Publish vacancy").click()
    layout(employer)
    expect(employer.get_by_text("No applicants in this view yet.")).to_be_visible()
    worker.reload()
    worker.get_by_role("link", name="⌕ काम खोजें →").click()
    worker.locator("#tutorial-skip").click()
    worker.locator("#apply-job").click()
    worker.locator("#confirm-apply").click()
    expect(worker.locator("#discovery-status")).to_contain_text("आवेदन भेज दिया")
    worker.get_by_role("link", name="मेरे आवेदन →").click()
    expect(worker.locator("#applications .status")).to_contain_text("Applied")
    employer.reload()
    employer.get_by_role("button", name="Select worker").click()
    expect(employer.locator(".applicant-card .status")).to_have_text("Selected")
    layout(employer)
    worker.reload()
    expect(worker.locator("#applications .status")).to_contain_text("Selected")
    layout(worker)
    worker.screenshot(path=str(RESULTS / "worker-selected-mobile.png"), full_page=True)
    employer.screenshot(
        path=str(RESULTS / "employer-selected-mobile.png"), full_page=True
    )
    worker.get_by_role("button", name="लॉग आउट").click()
    login_ui(worker, live, "6999999902")
    expect(worker.locator("#applications .status")).to_contain_text("Selected")
    assert not errors and not bad_responses
    employer_context.close()
    worker_context.close()


def start_voice(page):
    page.locator("#start-voice").click()
    say(page, "जी हाँ")  # Audio preflight, then no further button taps.


def test_mocked_hindi_voice_all_questions_correction_repeat_skip_save(
    app, browser, live
):
    context, page = worker_page(app, browser, live, mock=True)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    start_voice(page)
    say(page, "मेरा नाम गलत नाम है")
    say(page, "नहीं, मेरा नाम परीक्षण श्रमिक है")
    expect(page.locator("#name")).to_have_value("परीक्षण श्रमिक")
    say(page, "दोबारा पूछो")
    say(page, "मैं पच्चीस साल का हूँ")
    say(page, "मुझे वेल्डिंग और बिजली का काम आता है")
    say(page, "कारखाना")
    say(page, "ek saal paanch mahine")
    say(page, "मैं नोएडा में काम करना चाहता हूँ")
    say(page, "मेरे पास ई-श्रम नंबर नहीं है")
    expect(page.locator("#confirmation")).to_be_visible()
    expect(page.locator("#experience_months")).to_have_value("17")
    expect(page.locator("#confirmed")).not_to_be_checked()
    say(page, "नहीं")
    say(page, "मेरा नाम बदलो")
    say(page, "सही किया गया नाम")
    expect(page.locator("#confirmation")).to_be_visible()
    page.screenshot(path=str(RESULTS / "v2-voice-review-mobile.png"), full_page=True)
    layout(page)
    assert page.evaluate("window.__speech.overlaps") == []
    assert all(
        row["lang"] == "hi-IN" for row in page.evaluate("window.__speech.spoken")
    )
    say(page, "सेव कर दो")
    expect(page).to_have_url(live + "/dashboard/laborer")
    page.reload()
    expect(page.get_by_role("heading", name="नमस्ते, सही किया गया नाम।")).to_be_visible()
    data = page.request.get(live + "/api/laborer/profile").json()["profile"]
    assert data["experience_months"] == 17 and data["experience_years"] == 1
    assert not errors
    context.close()


@pytest.mark.parametrize(
    "error",
    [
        "not-allowed",
        "audio-capture",
        "no-speech",
        "network",
        "language-not-supported",
        "service-not-allowed",
        "aborted",
    ],
)
def test_mocked_recognition_errors_keep_typed_fallback(app, browser, live, error):
    context, page = worker_page(app, browser, live, mock=True)
    start_voice(page)
    say(page, "परीक्षण श्रमिक")
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    page.evaluate("code=>window.__speech.error(code)", error)
    if error == "no-speech":
        expect(page.locator("#voice-state")).to_have_attribute(
            "data-state", "listening"
        )
        page.evaluate("window.__speech.error('no-speech')")
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    assert page.evaluate("window.__speech.starts") <= 4
    assert page.evaluate("window.__speech.overlaps") == []
    page.locator("#typed-mode").click()
    fill_profile(page)
    page.locator("#save-profile").click()
    expect(page).to_have_url(live + "/dashboard/laborer")
    context.close()


def test_mocked_silence_timeout_and_late_results_are_ignored(app, browser, live):
    context, page = worker_page(app, browser, live, mock=True)
    page.clock.install()
    start_voice(page)
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    page.evaluate("window.oldRecognition=window.__speech.last")
    page.clock.fast_forward(12001)
    page.clock.fast_forward(301)
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    page.clock.fast_forward(12001)
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    page.evaluate(
        "()=>{const r=[{transcript:'देर से आया जवाब'}];r.isFinal=true;window.oldRecognition.onresult({resultIndex:0,results:[r]});}"
    )
    expect(page.locator("#name")).to_have_value("")
    count = page.evaluate("window.__speech.starts")
    page.clock.fast_forward(120000)
    assert page.evaluate("window.__speech.starts") == count == 3
    context.close()


@pytest.mark.parametrize("failure", ["ttsError", "noVoices", "startError"])
def test_mocked_tts_failure_missing_voices_and_start_exception(
    app, browser, live, failure
):
    context, page = worker_page(app, browser, live, mock=True)
    page.evaluate("key=>window.__speech[key]=true", failure)
    page.locator("#start-voice").click()
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    assert page.evaluate("window.__speech.starts") == 0
    if failure == "noVoices":
        assert page.evaluate("window.__speech.spoken.length") == 0
    page.locator("#typed-mode").click()
    fill_profile(page)
    page.locator("#save-profile").click()
    expect(page).to_have_url(live + "/dashboard/laborer")
    context.close()


def test_without_javascript_full_typed_profile_works(app, browser, live):
    context, page = worker_page(app, browser, live, java_script_enabled=False)
    fill_profile(page)
    page.locator("#save-profile").click()
    expect(page).to_have_url(live + "/dashboard/laborer")
    expect(page.get_by_role("heading", name="नमस्ते, परीक्षण श्रमिक।")).to_be_visible()
    context.close()


def test_desktop_landing_and_narrow_layouts(browser, live):
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    page.goto(live + "/")
    page.evaluate("document.fonts.ready")
    layout(page)
    RESULTS.mkdir(exist_ok=True)
    page.screenshot(path=str(RESULTS / "home-desktop.png"), full_page=True)
    for width in [320, 360, 390, 768]:
        page.set_viewport_size({"width": width, "height": 844})
        for route in ["/", "/register/laborer", "/register/manager", "/login"]:
            page.goto(live + route)
            layout(page)
    context.close()
