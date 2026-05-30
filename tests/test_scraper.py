from src.scraper.extractor import (
    extract_scripts,
    extract_forms,
    find_privacy_policy_link,
    extract_page_language,
)
from src.scraper.collector import _classify_script


# ── extract_scripts ────────────────────────────────────────────────────────

def test_extract_scripts_finds_external():
    html = '<html><body><script src="https://cdn.example.com/lib.js"></script></body></html>'
    assert "https://cdn.example.com/lib.js" in extract_scripts(html)


def test_extract_scripts_ignores_inline():
    html = "<html><body><script>var x = 1;</script></body></html>"
    assert extract_scripts(html) == []


# ── extract_forms ──────────────────────────────────────────────────────────

def test_extract_forms_method_default_get():
    html = '<html><body><form action="/send"><input name="email"></form></body></html>'
    forms = extract_forms(html)
    assert len(forms) == 1
    assert forms[0]["method"] == "GET"
    assert "email" in forms[0]["fields"]


def test_extract_forms_has_privacy_notice_false():
    html = '<html><body><form><input name="name"></form></body></html>'
    forms = extract_forms(html)
    assert forms[0]["has_privacy_notice"] is False


def test_extract_forms_has_privacy_notice_true():
    html = '''<html><body>
        <form><input name="email">
        <a href="/privacidade">Política de privacidade</a>
        </form></body></html>'''
    forms = extract_forms(html)
    assert forms[0]["has_privacy_notice"] is True


def test_extract_forms_password_autocomplete_ok():
    html = '<html><body><form><input type="password" name="pwd" autocomplete="new-password"></form></body></html>'
    forms = extract_forms(html)
    assert forms[0]["password_autocomplete_ok"] is True


def test_extract_forms_password_autocomplete_missing():
    html = '<html><body><form><input type="password" name="pwd"></form></body></html>'
    forms = extract_forms(html)
    assert forms[0]["password_autocomplete_ok"] is False


# ── find_privacy_policy_link ───────────────────────────────────────────────

def test_find_privacy_policy_link_found():
    html = '<html><body><a href="/politica-de-privacidade">Política de privacidade</a></body></html>'
    assert find_privacy_policy_link(html) == "/politica-de-privacidade"


def test_find_privacy_policy_link_not_found():
    html = "<html><body><a href='/sobre'>Sobre nós</a></body></html>"
    assert find_privacy_policy_link(html) is None


# ── extract_page_language ──────────────────────────────────────────────────

def test_extract_page_language_pt():
    html = '<html lang="pt-PT"><body></body></html>'
    assert extract_page_language(html) == "pt"


def test_extract_page_language_en():
    html = '<html lang="en"><body></body></html>'
    assert extract_page_language(html) == "en"


def test_extract_page_language_unknown():
    html = "<html><body></body></html>"
    assert extract_page_language(html) == "unknown"


# ── _classify_script ───────────────────────────────────────────────────────

def test_classify_script_analytics():
    assert _classify_script("https://www.googletagmanager.com/gtm.js") == "analytics"
    assert _classify_script("https://www.google-analytics.com/analytics.js") == "analytics"


def test_classify_script_advertising():
    assert _classify_script("https://securepubads.g.doubleclick.net/gpt.js") == "advertising"


def test_classify_script_social():
    assert _classify_script("https://platform.twitter.com/widgets.js") == "social"
    assert _classify_script("https://www.youtube.com/embed/abc123") == "social"


def test_classify_script_unknown():
    assert _classify_script("https://cdn.exemplo.com/app.js") == "unknown"
