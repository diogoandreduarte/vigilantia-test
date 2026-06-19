from playwright.sync_api import sync_playwright

# Seletores CSS de CMPs conhecidos (OneTrust, Cookiebot, Quantcast, etc.)
_CMP_SELECTORS = [
    "#onetrust-banner-sdk",
    "#onetrust-accept-btn-handler",
    "#CybotCookiebotDialog",
    "#cookiebanner",
    "#cookie-banner",
    "#cookie-notice",
    "#cookie-consent",
    "#gdpr-banner",
    "#gdpr-cookie-notice",
    ".cookie-banner",
    ".cookie-notice",
    ".cookie-consent",
    ".cookiebanner",
    ".cc-window",
    ".cc-banner",
    "[id*='cookie'][id*='banner']",
    "[id*='consent']",
    "[class*='cookie-bar']",
    "[class*='consent-banner']",
    "[aria-label*='cookie']",
    "[aria-label*='consent']",
]

# Palavras-chave específicas de banner (não simples presença no body)
_BANNER_TEXT_KEYWORDS = [
    "aceitar cookies", "accept cookies", "aceitar todos", "accept all",
    "aceitar e fechar", "i accept", "eu aceito",
    "gerir preferências", "manage preferences", "manage cookies",
    "rejeitar cookies", "reject cookies",
]


def fetch_page_with_browser(url: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        # Esconder webdriver para evitar deteção de headless por sites
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page.goto(url, wait_until="networkidle", timeout=30000)

        # Scroll ao fundo para disparar IntersectionObservers (footers lazy)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        html = page.content()
        final_url = page.url
        cookies = context.cookies()

        # 1. Verificar seletores de CMPs conhecidos
        consent_banner_detected = False
        for selector in _CMP_SELECTORS:
            try:
                element = page.query_selector(selector)
                if element and element.is_visible():
                    consent_banner_detected = True
                    break
            except Exception:
                continue

        # 2. Fallback: texto específico de botões de consentimento
        if not consent_banner_detected:
            page_text = page.inner_text("body").lower()
            consent_banner_detected = any(kw in page_text for kw in _BANNER_TEXT_KEYWORDS)

        browser.close()

        return {
            "html": html,
            "final_url": final_url,
            "cookies": cookies,
            "consent_banner_detected": consent_banner_detected,
        }
