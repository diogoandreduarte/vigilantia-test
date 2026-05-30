import re
from src.scraper.playwright_fetcher import fetch_page_with_browser
from src.scraper.extractor import (
    extract_scripts,
    extract_forms,
    find_privacy_policy_link,
    extract_page_language,
)
from src.models.site_data import SiteData, ThirdPartyScript, Form, Cookie

_ANALYTICS_PATTERNS = re.compile(
    r"google-analytics|googletagmanager|gtag|hotjar|mixpanel|matomo|"
    r"clarity\.ms|segment\.com|amplitude|heap\.io|fullstory|newrelic|"
    r"datadog|optimizely|vwo\.com|crazyegg|mouseflow",
    re.IGNORECASE,
)

_ADVERTISING_PATTERNS = re.compile(
    r"doubleclick|googlesyndication|adservice|adnxs|facebook\.net/signals|"
    r"connect\.facebook|bat\.bing|ads\.linkedin|taboola|outbrain|"
    r"criteo|tradedoubler|zanox|awin\.com|shareasale",
    re.IGNORECASE,
)

_SOCIAL_PATTERNS = re.compile(
    r"facebook\.com/plugins|twitter\.com/widgets|platform\.twitter|"
    r"linkedin\.com/embed|instagram\.com/embed|tiktok\.com|"
    r"youtube\.com/embed|ytimg\.com|disqus\.com|addthis\.com|"
    r"shareaholic\.com|addtoany\.com",
    re.IGNORECASE,
)


def _classify_script(src: str) -> str:
    if _ANALYTICS_PATTERNS.search(src):
        return "analytics"
    if _ADVERTISING_PATTERNS.search(src):
        return "advertising"
    if _SOCIAL_PATTERNS.search(src):
        return "social"
    return "unknown"


def _detect_language(html: str, page_text: str) -> str:
    # 1. Atributo lang da tag <html>
    lang = extract_page_language(html)
    if lang != "unknown":
        return lang
    # 2. langdetect sobre o texto da página
    try:
        from langdetect import detect
        lang = detect(page_text[:3000])
        return lang
    except Exception:
        return "unknown"


def collect_site_data(url: str) -> SiteData:
    page_data = fetch_page_with_browser(url)
    html = page_data["html"]

    # Scripts com categoria detetada na origem
    scripts = [
        ThirdPartyScript(src=src, category=_classify_script(src))
        for src in extract_scripts(html)
    ]

    # Formulários com deteção de aviso de privacidade
    forms = [
        Form(
            action=f["action"],
            method=f["method"],
            fields=f["fields"],
            has_privacy_notice=f["has_privacy_notice"],
            password_autocomplete_ok=f["password_autocomplete_ok"],
        )
        for f in extract_forms(html)
    ]

    cookies = [
        Cookie(
            name=c["name"],
            domain=c["domain"],
            path=c["path"],
            secure=c["secure"],
            httpOnly=c.get("httpOnly", False),
            sameSite=c.get("sameSite"),
        )
        for c in page_data["cookies"]
    ]

    # Deteção de idioma: HTML lang attr → langdetect
    try:
        page_text = html[:5000]
    except Exception:
        page_text = ""
    language = _detect_language(html, page_text)

    return SiteData(
        url=url,
        final_url=page_data["final_url"],
        language=language,
        cookies=cookies,
        third_party_scripts=scripts,
        forms=forms,
        privacy_policy_url=find_privacy_policy_link(html),
        privacy_policy_text=None,
        consent_banner_detected=page_data["consent_banner_detected"],
        screenshot_path=None,
    )
