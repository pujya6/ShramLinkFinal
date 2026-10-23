"""Actual local Flask/Chromium release journeys; speech is explicitly simulated."""

import pytest
from conftest import TEST_PASSWORD
from playwright.sync_api import expect
from test_browser import ROOT, RESULTS, layout, login_ui, say, start_voice, worker_page
from test_browser_v2 import swipe
from test_release import boot

from app.models import DemoPreparation, JobApplication, User, db


@pytest.mark.parametrize("name", ["जीत झा", "जीवन कुमार", "जीतेन्द्र शर्मा"])
def test_spoken_name_prefix_survives_review_save_and_reload(app, browser, live, name):
    context, page = worker_page(app, browser, live, mock=True)
    start_voice(page)
    for answer in [
        name,
        "पच्चीस",
        "वेल्डिंग",
        "कारखाना",
        "दो साल आठ महीने",
        "दिल्ली",
        "छोड़ दो",
    ]:
        say(page, answer)
    expect(page.locator("#name")).to_have_value(name)
    expect(page.locator("#confirmation")).to_be_visible()
    expect(page.locator("#confirmed")).not_to_be_checked()
    say(page, "सेव कर दो")
    expect(page).to_have_url(live + "/dashboard/laborer")
    page.reload()
    assert (
        page.request.get(live + "/api/laborer/profile").json()["profile"]["name"]
        == name
    )
    context.close()


def test_bootstrapped_mobile_stack_internal_application_and_external_preparation(
    app, browser, live
):
    result = app.test_cli_runner().invoke(
        args=["bootstrap-demo", "--password", TEST_PASSWORD]
    )
    assert result.exit_code == 0
    context = browser.new_context(viewport={"width": 390, "height": 844})
    page = context.new_page()
    errors = []
    requests = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda request: requests.append((request.method, request.url)))
    login_ui(page, live, "worker.v3@example.invalid")
    page.goto(live + "/discover")
    page.locator("#tutorial-skip").click()
    expect(page.locator("#job-position")).to_have_text("1 / 8")
    swipe(page, "#swipe-pad", 0, -100)
    expect(page.locator("#job-position")).to_have_text("2 / 8")
    page.locator("#previous-job").click()
    selected = page.evaluate("window.shramDiscovery.current().id")
    RESULTS.mkdir(exist_ok=True)
    page.screenshot(
        path=str(RESULTS / "release-populated-stack-390.png"), full_page=True
    )
    page.locator("#apply-job").click()
    with app.app_context():
        assert JobApplication.query.count() == 0
    page.locator("#confirm-apply").dblclick()
    expect(page.locator("#discovery-status")).to_contain_text("आवेदन भेज दिया")
    with app.app_context():
        assert JobApplication.query.count() == 1
    # Explicit next-button navigation to a separate external demonstration card.
    for _ in range(7):
        if page.evaluate("window.shramDiscovery.current().external"):
            break
        page.locator("#next-job").click()
    expect(page.locator("#external-notice")).to_be_visible()
    page.locator("#apply-job").click()
    expect(page.locator("#confirm-apply")).to_be_enabled()
    page.locator("#confirm-apply").click()
    expect(page.locator("#discovery-status")).to_contain_text(
        "not submitted externally"
    )
    page.goto(live + "/dashboard/laborer")
    expect(page.locator("#preparations")).to_contain_text(
        "Demo application prepared — not submitted externally"
    )
    manager_context = browser.new_context()
    manager = manager_context.new_page()
    login_ui(manager, live, "employer1.v3@example.invalid")
    manager.goto(live + f"/jobs/{selected}/applicants")
    manager.get_by_role("button", name="Select worker").click()
    page.reload()
    expect(page.locator("#applications")).to_contain_text("Selected")
    assert all(url.startswith(live) for method, url in requests if method == "POST")
    assert not errors
    context.close()
    manager_context.close()


def test_new_worker_registration_to_seeded_stack(app, browser, live):
    boot(app)
    context = browser.new_context(viewport={"width": 390, "height": 844})
    context.add_init_script(path=str(ROOT / "tests/fixtures/mock_speech.js"))
    page = context.new_page()
    page.goto(live + "/")
    page.goto(live + "/register/laborer")
    page.locator("#phone").fill("6999999982")
    page.locator("#password").fill(TEST_PASSWORD)
    page.locator("#confirm_password").fill(TEST_PASSWORD)
    page.locator("button[type=submit]").click()
    start_voice(page)
    for answer in [
        "जी, मेरा नाम जीत झा है",
        "पच्चीस",
        "वेल्डिंग",
        "कारखाना",
        "दो साल आठ महीने",
        "दिल्ली",
        "छोड़ दो",
    ]:
        say(page, answer)
    say(page, "सेव कर दो")
    expect(page).to_have_url(live + "/dashboard/laborer")
    page.goto(live + "/discover")
    page.locator("#tutorial-skip").click()
    expect(page.locator("#job-position")).to_have_text("1 / 8")
    expect(page.locator("#apply-job")).to_be_enabled()
    assert (
        page.evaluate(
            "window.shramDiscovery.jobs.filter(j=>!j.external&&j.match.eligible).length"
        )
        == 2
    )
    layout(page)
    context.close()


def test_empty_skipped_stack_recovers_without_application(app, browser, live):
    boot(app)
    context = browser.new_context(viewport={"width": 390, "height": 844})
    page = context.new_page()
    login_ui(page, live, "worker.v3@example.invalid")
    page.goto(live + "/discover")
    page.locator("#tutorial-skip").click()
    for _ in range(8):
        page.locator("#skip-job").click()
    expect(page.locator("#stack-empty")).to_have_attribute("data-reason", "skipped")
    page.reload()
    expect(page.locator("#empty-restore")).to_be_visible()
    page.locator("#empty-restore").click()
    expect(page.locator("#job-position")).to_have_text("1 / 8")
    with app.app_context():
        assert JobApplication.query.count() == DemoPreparation.query.count() == 0
    context.close()


@pytest.mark.parametrize("width,height", [(390, 844), (768, 1024), (1440, 1000)])
def test_showcase_visual_examples_no_network_mutations(
    app, browser, live, width, height
):
    context = browser.new_context(
        viewport={"width": width, "height": height}, reduced_motion="reduce"
    )
    page = context.new_page()
    requests = []
    errors = []
    page.on("request", lambda r: requests.append((r.method, r.url)))
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(live + "/inside")
    page.evaluate("document.fonts.ready")
    page.locator("#parse-example").click()
    expect(page.locator("#duration-result")).to_contain_text("32 months")
    page.locator("#duration-example").fill("लगभग दो साल")
    page.locator("#parse-example").click()
    expect(page.locator("#duration-result")).to_contain_text("Clarification needed")
    page.locator("#match-example").click()
    expect(page.locator("#match-result")).to_contain_text("100/100")
    page.locator("#example-skill").select_option("helper")
    page.locator("#match-example").click()
    expect(page.locator("#match-result")).to_contain_text("requirement not met")
    page.locator("summary").click()
    expect(page.locator(".illustration-preview")).to_contain_text("NO RECORD CREATED")
    assert all(method == "GET" and url.startswith(live) for method, url in requests)
    assert not errors
    layout(page)
    assert page.evaluate(
        "[...document.querySelectorAll('.button')].every(x=>x.getBoundingClientRect().height>=44)"
    )
    RESULTS.mkdir(exist_ok=True)
    page.screenshot(path=str(RESULTS / f"release-inside-{width}.png"), full_page=True)
    with app.app_context():
        assert (
            User.query.count()
            == JobApplication.query.count()
            == DemoPreparation.query.count()
            == 0
        )
    context.close()


def test_showcase_without_javascript_is_readable(browser, live):
    context = browser.new_context(
        java_script_enabled=False, viewport={"width": 390, "height": 844}
    )
    page = context.new_page()
    page.goto(live + "/inside")
    expect(page.locator("#architecture-title")).to_be_visible()
    expect(page.locator("#duration-result")).to_contain_text("32 months")
    expect(page.get_by_role("link", name="Release handoff ↗")).to_be_visible()
    layout(page)
    context.close()
