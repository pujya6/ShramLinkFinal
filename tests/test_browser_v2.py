"""V2 browser lifecycle and gesture checks. All audio is simulated, never physical."""

import pytest
from playwright.sync_api import expect
from conftest import post, vacancy
from test_browser import ROOT, RESULTS, worker_page, start_voice, say, layout, login_ui


def finish_answers(page):
    for answer in [
        "मेरा नाम परीक्षण श्रमिक है",
        "पच्चीस",
        "वेल्डिंग",
        "कारखाना",
        "2 saal 8 mahine",
        "दिल्ली",
        "छोड़ दो",
    ]:
        say(page, answer)
    expect(page.locator("#confirmation")).to_be_visible()
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")


def test_review_edit_invalidates_voice_confirmation_and_rereads(app, browser, live):
    context, page = worker_page(app, browser, live, mock=True)
    start_voice(page)
    finish_answers(page)
    assert page.request.get(live + "/api/laborer/profile").json()["complete"] is False
    page.locator("#name").fill("बदला हुआ नाम")
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    expect(page.locator("#confirmed")).not_to_be_checked()
    page.evaluate(
        "window.__speech.result('सेव कर दो')"
    )  # stale callback cannot save edits
    assert page.request.get(live + "/api/laborer/profile").json()["complete"] is False
    page.locator("#pause-voice").click()
    say(page, "हाँ")
    expect(page).to_have_url(live + "/dashboard/laborer")
    assert (
        page.request.get(live + "/api/laborer/profile").json()["profile"]["name"]
        == "बदला हुआ नाम"
    )
    context.close()


def test_pause_stop_rapid_start_and_background_never_overlap(app, browser, live):
    context, page = worker_page(app, browser, live, mock=True)
    page.evaluate("window.__speech.holdTTS=true")
    page.locator("#start-voice").click()
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "speaking")
    assert page.evaluate("window.__speech.starts") == 0
    page.locator("#stop-voice").click()
    page.evaluate("window.__speech.endTTS()")  # delayed cancelled utterance end
    assert page.evaluate("window.__speech.starts") == 0
    page.evaluate("window.__speech.holdTTS=false")
    start_voice(page)
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    page.locator("#pause-voice").click()
    page.evaluate("window.__speech.result('गलत नाम')")
    expect(page.locator("#name")).to_have_value("")
    page.locator("#pause-voice").click()
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    page.evaluate(
        "Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))"
    )
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    assert page.evaluate("window.__speech.overlaps") == []
    context.close()


def test_duplicate_results_and_missing_recognition_end_cannot_advance(
    app, browser, live
):
    context, page = worker_page(app, browser, live, mock=True)
    start_voice(page)
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    page.evaluate(
        "window.__speech.result('परीक्षण श्रमिक');window.__speech.result('दूसरा गलत नाम')"
    )
    expect(page.locator("#name")).to_have_value("परीक्षण श्रमिक")
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    page.evaluate("window.__speech.holdEnd=true;window.__speech.result('25')")
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    expect(page.locator("#age")).to_have_value("")
    assert page.evaluate("window.__speech.overlaps") == []
    # Even preflight buttons must not speak while the recogniser failed to end.
    page.locator(".audio-settings summary").click()
    count = page.evaluate("window.__speech.spoken.length")
    page.locator("#test-audio").click()
    expect(page.locator("#audio-status")).to_contain_text("माइक अभी बंद नहीं हुआ")
    assert page.evaluate("window.__speech.spoken.length") == count
    context.close()


def test_delayed_voice_discovery_selection_and_pronunciation_preflight(
    app, browser, live
):
    context, page = worker_page(app, browser, live, mock=True)
    page.evaluate("window.__speech.noVoices=true;window.__speech.voicesChanged()")
    page.locator("#start-voice").click()
    assert page.evaluate("window.__speech.spoken.length") == 0
    page.evaluate("window.__speech.noVoices=false;window.__speech.voicesChanged()")
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    say(page, "नहीं")
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    page.locator(".audio-settings summary").click()
    page.locator("#hindi-voice").select_option("mock-hi-two")
    page.locator("#test-pronunciation").click()
    expect(page.locator("#audio-status")).to_contain_text("क्या आवाज़ साफ़ थी")
    spoken = page.evaluate("window.__speech.spoken")
    assert all(row["lang"] == "hi-IN" for row in spoken)
    assert spoken[-1]["voice"] == "Second Hindi voice"
    assert "निर्माण" in spoken[-1]["text"]
    assert page.evaluate("window.__speech.overlaps") == []
    context.close()


def test_low_confidence_ambiguity_and_repeat_are_bounded(app, browser, live):
    context, page = worker_page(app, browser, live, mock=True)
    start_voice(page)
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    page.evaluate("window.__speech.result('अनिश्चित नाम',0.2)")
    expect(page.locator("#name")).to_have_value("")
    say(page, "परीक्षण श्रमिक")
    say(page, "बीस या तीस")
    expect(page.locator("#age")).to_have_value("")
    say(page, "पता नहीं")
    say(page, "पता नहीं")
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    assert page.evaluate("window.__speech.starts") <= 7
    assert page.request.get(live + "/api/laborer/profile").json()["complete"] is False
    context.close()


def discovery_page(browser, live, journey, **options):
    RESULTS.mkdir(exist_ok=True)
    worker, manager = journey
    jobs = []
    for n in range(3):
        jobs.append(
            post(
                manager,
                "/api/manager/post-job",
                json=vacancy(
                    title=f"Demo welder {n + 1}", wage=850 + n * 50, workers=2
                ),
            ).json["job"]
        )
    context = browser.new_context(viewport={"width": 390, "height": 844}, **options)
    context.add_init_script(path=str(ROOT / "tests/fixtures/mock_speech.js"))
    page = context.new_page()
    login_ui(page, live, "worker@example.invalid")
    page.goto(live + "/discover")
    return context, page, jobs


def swipe(page, selector, dx, dy, cancel=False):
    # Dispatch the exact pointer contract with controlled timestamps. This is a
    # simulated touch gesture; keyboard and button paths use real browser actions.
    page.locator(selector).evaluate(
        """(el,args)=>{
      const [dx,dy,cancel]=args;
      const send=(type,x,y,time)=>{const e=new PointerEvent(type,{bubbles:true,pointerId:2,pointerType:'touch',isPrimary:true,button:0,clientX:x,clientY:y});Object.defineProperty(e,'timeStamp',{value:time});el.dispatchEvent(e);};
      el.setPointerCapture=()=>{};
      send('pointerdown',180,350,100);send(cancel?'pointercancel':'pointerup',180+dx,350+dy,400);
    }""",
        [dx, dy, cancel],
    )


def test_discovery_gestures_buttons_confirmation_undo_and_status(
    browser, live, journey
):
    context, page, jobs = discovery_page(browser, live, journey)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.locator("#tutorial-skip").click()
    expect(page.locator("#job-title")).to_have_text("Demo welder 1")
    swipe(page, "#swipe-pad", 0, -100)
    expect(page.locator("#job-title")).to_have_text("Demo welder 2")
    swipe(page, "#swipe-pad", 0, 100)
    expect(page.locator("#job-title")).to_have_text("Demo welder 1")
    swipe(page, "#swipe-pad", -100, 0)
    expect(page.locator("#job-title")).to_have_text("Demo welder 2")
    page.locator("#undo-skip").click()
    expect(page.locator("#job-title")).to_have_text("Demo welder 1")
    page.locator("#swipe-pad").press("ArrowUp")
    page.locator("#previous-job").click()
    swipe(page, "#swipe-pad", 100, 90)  # diagonal is ambiguous
    swipe(page, "#swipe-pad", 100, 0, cancel=True)
    expect(page.locator("#apply-dialog")).not_to_be_visible()
    swipe(page, "#swipe-pad", 100, 0)
    expect(page.locator("#apply-dialog")).to_be_visible()
    assert journey[0].get("/api/laborer/my-jobs").json["applications"] == []
    page.locator("#cancel-apply").click()
    page.locator("#apply-job").click()
    page.locator("#confirm-apply").dblclick()
    expect(page.locator("#discovery-status")).to_contain_text("आवेदन भेज दिया")
    assert len(journey[0].get("/api/laborer/my-jobs").json["applications"]) == 1
    page.reload()
    expect(page.locator("#job-title")).to_have_text("Demo welder 2")
    page.locator("#skip-job").click()
    page.reload()
    expect(page.locator("#job-title")).to_have_text("Demo welder 3")
    page.locator("#restore-skips").click()
    expect(page.locator("#job-title")).to_have_text("Demo welder 2")
    layout(page)
    page.screenshot(path=str(RESULTS / "v2-discovery-mobile.png"), full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1100})
    page.screenshot(path=str(RESULTS / "v2-discovery-desktop.png"), full_page=True)
    assert not errors
    context.close()


def test_tutorial_practice_cannot_apply_and_buttons_repeat(browser, live, journey):
    context, page, jobs = discovery_page(
        browser, live, journey, reduced_motion="reduce"
    )
    expect(page.locator("#tutorial")).to_be_visible()
    page.screenshot(path=str(RESULTS / "v2-tutorial-mobile.png"), full_page=True)
    for dx, dy in [(0, -100), (0, 100), (-100, 0), (100, 0)]:
        swipe(page, "#practice-card", dx, dy)
    expect(page.locator("#tutorial-progress")).to_contain_text("5 / 5")
    page.locator("#tutorial-next").click()
    expect(page.locator("#tutorial")).not_to_be_visible()
    assert journey[0].get("/api/laborer/my-jobs").json["applications"] == []
    page.locator("#help-discovery").click()
    for _ in range(5):
        page.locator("#tutorial-next").click()
    assert journey[0].get("/api/laborer/my-jobs").json["applications"] == []
    assert (
        page.evaluate(
            "getComputedStyle(document.querySelector('.practice-arrow')).animationName"
        )
        == "none"
    )
    context.close()


@pytest.mark.parametrize("failure", ["filled", "network", "server", "csrf"])
def test_application_errors_never_show_success(browser, live, journey, app, failure):
    context, page, jobs = discovery_page(browser, live, journey)
    page.locator("#tutorial-skip").click()
    if failure == "filled":
        from app.models import Job, JobStatus, db

        with app.app_context():
            job = db.session.get(Job, jobs[0]["id"])
            job.status = JobStatus.FILLED
            job.workers_hired = 2
            db.session.commit()
    elif failure == "network":
        page.route("**/api/laborer/apply", lambda route: route.abort())
    elif failure == "server":
        page.route(
            "**/api/laborer/apply",
            lambda route: route.fulfill(
                status=500, json={"success": False, "error": "अभी उपलब्ध नहीं।"}
            ),
        )
    else:
        page.evaluate(
            "document.querySelector('meta[name=csrf-token]').content='bad-token'"
        )
    page.locator("#apply-job").click()
    page.locator("#confirm-apply").click()
    expect(page.locator("#apply-error")).not_to_be_empty()
    expect(page.locator("#apply-dialog")).to_be_visible()
    assert journey[0].get("/api/laborer/my-jobs").json["applications"] == []
    expect(page.locator("#job-title")).to_have_text("Demo welder 1")
    context.close()


def test_job_audio_cancel_auto_read_fallback_and_narrow_layouts(browser, live, journey):
    context, page, jobs = discovery_page(browser, live, journey)
    page.locator("#tutorial-skip").click()
    page.locator("#read-job").click()
    expect(page.locator("#discovery-status")).to_contain_text("जानकारी सुनें")
    page.wait_for_function("!speechSynthesis.speaking")
    assert "आठ सौ पचास" in " ".join(
        page.evaluate("window.__speech.spoken.map(x=>x.text)")
    )
    page.evaluate("window.__speech.holdTTS=true")
    page.locator("#read-job").click()
    page.locator("#next-job").click()
    assert page.evaluate("speechSynthesis.speaking") is False
    page.evaluate("window.__speech.endTTS();window.__speech.holdTTS=false")
    page.locator("#voice-discovery").click()
    page.locator("#next-job").click()
    page.wait_for_function("!speechSynthesis.speaking")
    assert "Demo welder 3" in " ".join(
        page.evaluate("window.__speech.spoken.map(x=>x.text)")
    )
    page.evaluate("window.__speech.noVoices=true")
    page.locator("#read-job").click()
    expect(page.locator("#discovery-status")).to_contain_text("हिंदी आवाज़ नहीं चल पाई")
    expect(page.locator("#apply-job")).to_be_enabled()
    for width in [320, 360, 390, 768, 1440]:
        page.set_viewport_size({"width": width, "height": 844})
        layout(page)
    assert page.evaluate("window.__speech.overlaps") == []
    context.close()


def test_synthesis_timeout_and_explicit_repeat_fail_without_auto_loops(
    app, browser, live
):
    context, page = worker_page(app, browser, live, mock=True)
    page.clock.install()
    page.evaluate("window.__speech.holdTTS=true")
    page.locator("#start-voice").click()
    page.clock.fast_forward(25001)
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    page.clock.fast_forward(120000)
    assert page.evaluate("window.__speech.starts") == 0
    assert page.evaluate("window.__speech.spoken.length") == 1
    page.evaluate("window.__speech.holdTTS=false;window.__speech.ttsError=true")
    page.locator("#pause-voice").click()
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    assert page.evaluate("window.__speech.starts") == 0
    context.close()


def test_real_mouse_drag_and_keyboard_scope(browser, live, journey):
    context, page, _ = discovery_page(browser, live, journey)
    page.locator("#tutorial-skip").click()
    pad = page.locator("#swipe-pad")
    pad.scroll_into_view_if_needed()
    box = pad.bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x, y - 100, steps=10)
    page.wait_for_timeout(80)  # An intentional gesture must last at least 40 ms.
    page.mouse.up()
    expect(page.locator("#job-title")).to_have_text("Demo welder 2")
    page.locator("#help-discovery").focus()
    page.keyboard.press("ArrowRight")
    expect(page.locator("#apply-dialog")).not_to_be_visible()
    pad.press("ArrowRight")
    expect(page.locator("#apply-dialog")).to_be_visible()
    assert journey[0].get("/api/laborer/my-jobs").json["applications"] == []
    page.keyboard.press("Escape")
    expect(page.locator("#apply-dialog")).not_to_be_visible()
    context.close()


def test_discovery_without_javascript_requires_checked_confirmation(
    browser, live, journey
):
    context, page, _ = discovery_page(browser, live, journey, java_script_enabled=False)
    expect(page.locator("#job-list-fallback")).to_be_visible()
    form = page.locator("#job-list-fallback form").first
    form.get_by_role("button", name="हाँ, आवेदन भेजें").click()
    assert journey[0].get("/api/laborer/my-jobs").json["applications"] == []
    form.locator("input[type=checkbox]").check()
    form.get_by_role("button", name="हाँ, आवेदन भेजें").click()
    expect(page).to_have_url(live + "/dashboard/laborer#applications")
    assert len(journey[0].get("/api/laborer/my-jobs").json["applications"]) == 1
    context.close()


def test_visible_skip_waits_for_mic_end_and_stop_cancels_pending_restart(
    app, browser, live
):
    context, page = worker_page(app, browser, live, mock=True)
    start_voice(page)
    for answer in ["परीक्षण श्रमिक", "25", "वेल्डिंग", "कारखाना", "6 mahine", "दिल्ली"]:
        say(page, answer)
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    page.locator("#skip").click()
    expect(page.locator("#confirmation")).to_be_visible()
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    assert page.evaluate("window.__speech.overlaps") == []
    # Force a slow microphone stop. A later Stop must win over queued Repeat.
    page.evaluate("window.__speech.holdEnd=true")
    page.locator("#repeat").click()
    page.locator("#stop-voice").click()
    starts = page.evaluate("window.__speech.starts")
    page.evaluate("window.__speech.activeMic=false;window.__speech.last.onend()")
    page.wait_for_timeout(400)
    assert page.evaluate("window.__speech.starts") == starts
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    assert page.request.get(live + "/api/laborer/profile").json()["complete"] is False
    context.close()


def test_spoken_previous_next_required_skip_and_stop(app, browser, live):
    context, page = worker_page(app, browser, live, mock=True)
    start_voice(page)
    say(page, "परीक्षण श्रमिक")
    say(page, "25")
    say(page, "पिछला सवाल")
    expect(page.locator("#age")).to_be_visible()
    say(page, "आगे बढ़ो")
    expect(page.locator("#skills")).to_be_visible()
    say(page, "छोड़ दो")
    expect(page.locator("#skills")).to_be_visible()
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "listening")
    say(page, "बंद करो")
    expect(page.locator("#voice-state")).to_have_attribute("data-state", "paused")
    assert page.evaluate("window.__speech.overlaps") == []
    assert page.request.get(live + "/api/laborer/profile").json()["complete"] is False
    context.close()
