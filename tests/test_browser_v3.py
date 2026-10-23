"""V3 UI integration in headless Chromium. Speech/provider responses are mocks."""

import pytest
from conftest import post, vacancy
from playwright.sync_api import expect
from test_browser import RESULTS, layout, login_ui, say, start_voice, worker_page
from test_browser_v2 import discovery_page, swipe
from test_v3_core import external

from app.models import DemoPreparation, JobApplication
from app.settings import configure


def test_external_preview_real_controls_local_record_only(app, browser, live, journey):
    row_id = external(app)
    context = browser.new_context(viewport={"width": 390, "height": 844})
    page = context.new_page()
    requests = []
    page.on("request", lambda req: requests.append((req.method, req.url)))
    login_ui(page, live, "worker@example.invalid")
    page.goto(live + "/discover")
    page.locator("#tutorial-skip").click()
    expect(page.locator("#job-wage-unit")).to_have_text("/ महीना")
    expect(page.locator("#external-notice")).to_be_visible()
    swipe(page, "#swipe-pad", 100, 0)
    expect(page.locator("#external-preview")).to_be_visible()
    expect(page.locator("#preview-matches")).to_contain_text("कौशल")
    expect(page.locator("#preview-missing")).to_contain_text("प्रमाणपत्र")
    with app.app_context():
        assert DemoPreparation.query.count() == 0
    page.locator("#confirm-apply").dblclick()
    expect(page.locator("#discovery-status")).to_contain_text(
        "Demo application prepared — not submitted externally"
    )
    page.get_by_role("link", name="मेरे आवेदन →").click()
    expect(page.locator("#preparations .status")).to_have_text(
        "Demo application prepared — not submitted externally"
    )
    page.reload()
    expect(page.locator("#preparations .status")).to_be_visible()
    with app.app_context():
        assert DemoPreparation.query.count() == 1 and JobApplication.query.count() == 0
    assert all(url.startswith(live) for method, url in requests if method == "POST")
    layout(page)
    RESULTS.mkdir(exist_ok=True)
    page.screenshot(
        path=str(RESULTS / "v3-external-prepared-mobile.png"), full_page=True
    )
    context.close()


def test_external_preview_failure_cannot_confirm(app, browser, live, journey):
    external(app)
    context = browser.new_context(viewport={"width": 390, "height": 844})
    page = context.new_page()
    login_ui(page, live, "worker@example.invalid")
    page.route(
        "**/api/laborer/external/*/preview",
        lambda route: route.fulfill(status=503, json={"error": "Unavailable"}),
    )
    page.goto(live + "/discover")
    page.locator("#tutorial-skip").click()
    page.locator("#apply-job").click()
    expect(page.locator("#apply-error")).not_to_be_empty()
    expect(page.locator("#confirm-apply")).to_be_disabled()
    with app.app_context():
        assert DemoPreparation.query.count() == 0
    context.close()


def test_no_javascript_external_preparation_requires_explicit_review(
    app, browser, live, journey
):
    external(app)
    context = browser.new_context(
        java_script_enabled=False, viewport={"width": 390, "height": 844}
    )
    page = context.new_page()
    login_ui(page, live, "worker@example.invalid")
    page.goto(live + "/discover")
    page.get_by_role("link", name="प्रदर्शन तैयारी जाँचें →").click()
    page.get_by_role("button", name="हाँ, प्रदर्शन तैयारी सेव करें").click()
    with app.app_context():
        assert DemoPreparation.query.count() == 0
    page.locator('input[name="confirmed"]').check()
    page.get_by_role("button", name="हाँ, प्रदर्शन तैयारी सेव करें").click()
    expect(page.locator("#preparations .status")).to_have_text(
        "Demo application prepared — not submitted externally"
    )
    layout(page)
    context.close()


def test_tutorial_audio_replay_each_lesson_and_stop(browser, live, journey):
    context, page, _ = discovery_page(browser, live, journey)
    assert page.evaluate("window.__speech.spoken.length") == 0  # no audio on auto-open
    page.locator("#tutorial-audio").click()
    page.wait_for_function(
        "!speechSynthesis.speaking && window.__speech.spoken.length>0"
    )
    first = page.evaluate("window.__speech.spoken.length")
    page.locator("#tutorial-audio").click()  # replay, not a silent toggle-off
    page.wait_for_function("(n)=>window.__speech.spoken.length>n", arg=first)
    for expected in ["नीचे", "बाएँ", "दाएँ"]:
        page.locator("#tutorial-next").click()
        page.wait_for_function(
            "(word)=>window.__speech.spoken.some(s=>s.text.includes(word))",
            arg=expected,
        )
    page.evaluate("window.__speech.holdTTS=true")
    page.locator("#tutorial-audio").click()
    page.wait_for_function("speechSynthesis.speaking")
    page.locator("#tutorial-stop-audio").click()
    assert page.evaluate("speechSynthesis.speaking") is False
    count = page.evaluate("window.__speech.spoken.length")
    page.locator("#tutorial-next").click()
    assert page.evaluate("window.__speech.spoken.length") == count
    assert journey[0].get("/api/laborer/my-jobs").json["applications"] == []
    assert page.evaluate("window.__speech.overlaps") == []
    context.close()


@pytest.mark.parametrize("failure", ["missing", "synthesis"])
def test_tutorial_audio_failure_leaves_visible_practice(
    browser, live, journey, failure
):
    context, page, _ = discovery_page(browser, live, journey)
    page.evaluate(
        "window.__speech.noVoices=true"
        if failure == "missing"
        else "window.__speech.ttsError='synthesis-failed'"
    )
    page.locator("#tutorial-audio").click()
    expect(page.locator("#tutorial-progress")).to_contain_text("हिंदी आवाज़ नहीं चली")
    page.locator("#tutorial-next").click()
    expect(page.locator("#tutorial-progress")).to_contain_text("2 / 5")
    page.locator("#tutorial-skip").click()
    expect(page.locator("#apply-job")).to_be_visible()
    context.close()


def api_page(app, browser, live):
    app.config.update(
        VOICE_PROVIDER="api",
        XAI_API_KEY="synthetic-server-only-key",
        XAI_MODEL="grok-4.3",
    )
    configure(app)
    context, page = worker_page(app, browser, live, mock=True)
    start_voice(page)
    say(page, "परीक्षण श्रमिक")
    say(page, "अट्ठाईस")
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    return context, page


def test_api_assisted_answer_is_read_back_and_still_requires_review(app, browser, live):
    context, page = api_page(app, browser, live)
    page.route(
        "**/api/laborer/interpret",
        lambda route: route.fulfill(
            json=dict(
                provider="api",
                fallback=False,
                intent="answer",
                field="skills",
                value=["welder"],
            )
        ),
    )
    say(page, "mujhe metal jodne ka kaam aata hai")
    expect(page.locator("input[value=welder]")).to_be_checked()
    expect(page.locator("#interpretation-status")).to_contain_text("ऑनलाइन मदद से समझा")
    for answer in ["कारखाना", "2 saal 8 mahine", "दिल्ली", "छोड़ दो"]:
        say(page, answer)
    expect(page.locator("#confirmation")).to_be_visible()
    assert page.request.get(live + "/api/laborer/profile").json()["complete"] is False
    assert "synthetic-server-only-key" not in page.content()
    say(page, "हाँ")
    expect(page).to_have_url(live + "/dashboard/laborer")
    assert (
        page.request.get(live + "/api/laborer/profile").json()["profile"][
            "experience_months"
        ]
        == 32
    )
    assert page.evaluate("window.__speech?.overlaps || []") == []
    context.close()


def test_api_failure_returns_to_local_clarification_and_typed_fallback(
    app, browser, live
):
    context, page = api_page(app, browser, live)
    page.route(
        "**/api/laborer/interpret",
        lambda route: route.fulfill(
            json=dict(provider="deterministic", fallback=True, reason="provider_error")
        ),
    )
    say(page, "mujhe metal jodne ka kaam aata hai")
    expect(page.locator("#interpretation-status")).to_contain_text("सामान्य सवाल-जवाब")
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    say(page, "वेल्डिंग")
    expect(page.locator("input[value=welder]")).to_be_checked()
    page.locator("#type-shortcut").click()
    expect(page.locator("#name")).to_be_visible()
    context.close()


def test_pause_discards_pending_api_result(app, browser, live):
    context, page = api_page(app, browser, live)
    page.evaluate(
        "window.__realFetch=window.fetch;window.fetch=(...args)=>String(args[0]).includes('/interpret') ? new Promise(resolve=>window.__deliver=()=>resolve({ok:true,json:async()=>({provider:'api',fallback:false,intent:'answer',field:'skills',value:['welder']})})) : window.__realFetch(...args)"
    )
    say(page, "mujhe metal jodne ka kaam aata hai")
    page.wait_for_function("typeof window.__deliver === 'function'")
    page.locator("#stop-voice").click()
    page.evaluate("window.__deliver()")
    expect(page.locator("input[value=welder]")).not_to_be_checked()
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    assert page.evaluate("window.__speech.overlaps") == []
    context.close()


def test_api_correction_during_final_review_cannot_save_automatically(
    app, browser, live
):
    context, page = api_page(app, browser, live)
    for answer in ["वेल्डिंग", "कारखाना", "2 saal 8 mahine", "दिल्ली", "छोड़ दो"]:
        say(page, answer)
    say(page, "नहीं")
    page.route(
        "**/api/laborer/interpret",
        lambda route: route.fulfill(
            json=dict(
                provider="api",
                fallback=False,
                intent="correct",
                field="name",
                value="सुरेश",
            )
        ),
    )
    say(page, "pehli baat badal kar सुरेश rakho")
    expect(page.locator("#name")).to_have_value("सुरेश")
    expect(page.locator("#confirmation")).to_be_visible()
    assert page.request.get(live + "/api/laborer/profile").json()["complete"] is False
    say(page, "हाँ")
    expect(page).to_have_url(live + "/dashboard/laborer")
    assert (
        page.request.get(live + "/api/laborer/profile").json()["profile"]["name"]
        == "सुरेश"
    )
    context.close()


@pytest.mark.parametrize("width,height", [(390, 844), (768, 1024), (1440, 1000)])
def test_v3_responsive_shared_screens(app, browser, live, journey, width, height):
    post(
        journey[1],
        "/api/manager/post-job",
        json=vacancy(
            wage_unit="month", wage=24000, employment_category="direct_formal"
        ),
    )
    context = browser.new_context(viewport={"width": width, "height": height})
    page = context.new_page()
    for path in ["/", "/register/laborer", "/login"]:
        page.goto(live + path)
        layout(page)
    login_ui(page, live, "worker@example.invalid")
    for path in ["/onboarding", "/dashboard/laborer", "/discover"]:
        page.goto(live + path)
        layout(page)
        if path == "/discover":
            page.locator("#tutorial-skip").click()
        assert page.evaluate(
            "[...document.querySelectorAll('.button')].filter(x=>x.getClientRects().length&&!x.disabled).every(x=>x.getBoundingClientRect().height>=44)"
        )
    context.close()
