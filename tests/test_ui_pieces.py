"""The small HTML building blocks in app/ui.py. Needs no database."""

import pytest

from app import ui

pytestmark = pytest.mark.no_database


def test_names_are_escaped_in_person_cards():
    markup = ui.person_html('<script>alert(1)</script> Home', ["<b>city</b>"])
    assert "<script>" not in markup and "<b>city</b>" not in markup
    assert "&lt;script&gt;" in markup


def test_initials():
    assert ui.initials("Hope Shelter") == "HS"
    assert ui.initials("St. Mark's Church Canteen") == "SM"
    assert ui.initials("Grace <Home>") == "GH"
    assert ui.initials("") == "?"


def test_avatar_colour_is_stable_and_from_the_checked_palette():
    assert ui.avatar_colours("Hope Shelter") == ui.avatar_colours("hope shelter")
    assert ui.avatar_colours("Hope Shelter") in ui.AVATAR_COLOURS


@pytest.mark.parametrize("status, done, current", [
    ("REQUESTED", 0, "Requested"),
    ("ACCEPTED", 1, "Accepted"),
    ("PICKED_UP", 2, "Picked up"),
    ("DELIVERED", 4, None),
])
def test_tracker_steps(status, done, current):
    markup = ui.tracker_html(status)
    assert markup.count('class="fr-step done"') == done
    for words in ("Requested", "Accepted", "Picked up", "Delivered"):
        assert words in markup          # words always shown, not colour only
    if current:
        assert f'current"><span class="fr-dot">' in markup
        assert f"Step {done + 1} of 4: {current}" in markup
    else:
        assert "all 4 steps done" in markup


def test_tracker_ignores_unknown_status():
    assert ui.tracker_html("REJECTED") == ""


def test_impact_strip_numbers_and_line():
    markup = ui.impact_html({"kg_this_month": 120, "donations_this_month": 9,
                             "deliveries": 52, "kitchens": 3,
                             "volunteers": 5})
    assert "Together we shared 120 kg of food this month." in markup
    for number in ("120", "52", "3", "5"):
        assert f'<div class="fr-num">{number}</div>' in markup


def test_impact_strip_is_friendly_when_nothing_has_happened_yet():
    markup = ui.impact_html({})
    assert "Your first delivery will appear here." in markup
    assert "fr-num\"" not in markup     # no row of zeros


def test_every_illustration_has_a_description():
    for picture in ui.ASSETS.glob("*.svg"):
        _source, description = ui._picture(picture.stem)
        assert description, picture.name


# ---------------------------------------------------------------- Home polish

def test_greeting_icon_is_sun_before_5pm_and_moon_after():
    from datetime import datetime

    from app.home_pages import greeting_icon
    assert greeting_icon(datetime(2026, 11, 19, 9, 0)) == ":material/wb_sunny:"
    assert greeting_icon(datetime(2026, 11, 19, 16, 59)) == ":material/wb_sunny:"
    assert greeting_icon(datetime(2026, 11, 19, 17, 0)) == ":material/bedtime:"
    assert greeting_icon(datetime(2026, 11, 19, 22, 30)) == ":material/bedtime:"


def test_getting_started_ticks_from_real_numbers():
    from app.home_pages import getting_started_steps
    pages = {name: name for name in
             ("restaurants", "organizations", "user-access", "pickups")}
    nothing = getting_started_steps({}, pages)
    assert [done for _, done, _ in nothing] == [False] * 4
    some = getting_started_steps({"kitchens": 2, "organizations": 1,
                                  "volunteers": 0, "deliveries": 0}, pages)
    assert [done for _, done, _ in some] == [True, True, False, False]
    assert [page for _, _, page in some] == [
        "restaurants", "organizations", "user-access", "pickups"]


def test_progress_bar_says_the_same_in_words():
    assert 'aria-label="2 of 4 done"' in ui.progress_html(2, 4)
    assert "width:50%" in ui.progress_html(2, 4)
    assert "width:0%" in ui.progress_html(0, 0)


def test_a_quick_action_form_request_only_lasts_on_its_page(monkeypatch):
    state = {}
    monkeypatch.setattr(ui.st, "session_state", state)
    state[ui._FORM_REQUEST] = {"form": "volunteer", "page": "volunteers"}
    assert ui.form_requested("volunteer")
    assert not ui.form_requested("restaurant")
    ui.forget_form_request("volunteers")       # still on that page
    assert ui.form_requested("volunteer")
    ui.forget_form_request("home")             # went somewhere else
    assert not ui.form_requested("volunteer")


# ---------------------------------------------------------------- sign-in page

def test_landing_headline_is_escaped_and_highlighted():
    markup = ui.hero_text_html("Grace <Ministry>", "Share food with neighbours",
                               "One line.", highlight="neighbours")
    assert "<h1>Share food with <em>neighbours</em></h1>" in markup
    assert "Grace &lt;Ministry&gt;" in markup


def test_landing_footer_has_privacy_link_and_contact():
    from app.privacy import CONTACT_EMAIL, PRIVACY_LINK
    markup = ui.footer_html("Ministry", PRIVACY_LINK, CONTACT_EMAIL)
    assert f'href="{PRIVACY_LINK}"' in markup
    assert f"mailto:{CONTACT_EMAIL}" in markup
    assert "Made with love by volunteers" in markup


def test_sign_in_text_matches_published_google_sign_in():
    import inspect

    from app import auth
    from app.screens import people
    words = inspect.getsource(auth) + inspect.getsource(people)
    assert "Anyone can sign in with Google. New people are approved" in words
    assert "invited" not in words.lower()
    assert "test user" not in words.lower()
