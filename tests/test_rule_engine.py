import pytest
from src.analyzer.rule_engine import run_analysis, load_rules, evaluate_rules
from src.models.site_data import SiteData, ThirdPartyScript, Form, Cookie
from src.models.finding import Severity


def make_site(**kwargs) -> SiteData:
    base = dict(
        url="https://exemplo.com",
        final_url="https://exemplo.com",
        language="pt",
        cookies=[],
        third_party_scripts=[],
        forms=[],
        privacy_policy_url=None,
        privacy_policy_text=None,
        consent_banner_detected=False,
        screenshot_path=None,
    )
    base.update(kwargs)
    return SiteData(**base)


RULES_PATH = "rules/gdpr_rules.yaml"


def findings_by_id(site: SiteData) -> dict:
    return {f.rule_id: f for f in run_analysis(site, RULES_PATH)}


# ── RGPD-01: banner de consentimento ──────────────────────────────────────

def test_rgpd01_fail_without_banner():
    f = findings_by_id(make_site(consent_banner_detected=False))
    assert f["RGPD-01"].passed is False
    assert f["RGPD-01"].severity == Severity.HIGH


def test_rgpd01_pass_with_banner():
    f = findings_by_id(make_site(consent_banner_detected=True))
    assert f["RGPD-01"].passed is True


# ── RGPD-02: cookies de terceiros ─────────────────────────────────────────

def test_rgpd02_fail_with_third_party_cookie():
    cookies = [Cookie(name="_ga", domain=".google.com", secure=True, httpOnly=True)]
    f = findings_by_id(make_site(cookies=cookies))
    assert f["RGPD-02"].passed is False


def test_rgpd02_pass_no_cookies():
    f = findings_by_id(make_site(cookies=[]))
    assert f["RGPD-02"].passed is True


# ── RGPD-03: cookie sem Secure ────────────────────────────────────────────

def test_rgpd03_fail_without_secure():
    cookies = [Cookie(name="track", domain=".ads.com", secure=False)]
    f = findings_by_id(make_site(cookies=cookies))
    assert f["RGPD-03"].passed is False


def test_rgpd03_pass_all_secure():
    cookies = [Cookie(name="track", domain=".ads.com", secure=True)]
    f = findings_by_id(make_site(cookies=cookies))
    assert f["RGPD-03"].passed is True


# ── RGPD-04: cookie sem HttpOnly ──────────────────────────────────────────

def test_rgpd04_fail_without_httponly():
    cookies = [Cookie(name="session", domain="exemplo.com", httpOnly=False)]
    f = findings_by_id(make_site(cookies=cookies))
    assert f["RGPD-04"].passed is False


# ── RGPD-05: analytics sem consentimento ──────────────────────────────────

def test_rgpd05_fail_analytics_no_consent():
    scripts = [ThirdPartyScript(src="https://www.google-analytics.com/analytics.js", category="analytics")]
    f = findings_by_id(make_site(third_party_scripts=scripts, consent_banner_detected=False))
    assert f["RGPD-05"].passed is False


def test_rgpd05_pass_analytics_with_consent():
    scripts = [ThirdPartyScript(src="https://www.google-analytics.com/analytics.js", category="analytics")]
    f = findings_by_id(make_site(third_party_scripts=scripts, consent_banner_detected=True))
    assert f["RGPD-05"].passed is True


# ── RGPD-07: formulário sem aviso de privacidade ──────────────────────────

def test_rgpd07_fail_form_without_notice():
    forms = [Form(action="/send", method="POST", fields=["email"], has_privacy_notice=False)]
    f = findings_by_id(make_site(forms=forms))
    assert f["RGPD-07"].passed is False


def test_rgpd07_pass_form_with_notice():
    forms = [Form(action="/send", method="POST", fields=["email"], has_privacy_notice=True)]
    f = findings_by_id(make_site(forms=forms))
    assert f["RGPD-07"].passed is True


# ── RGPD-08: formulário com GET e dados pessoais ──────────────────────────

def test_rgpd08_fail_personal_data_in_get():
    forms = [Form(action="/search", method="GET", fields=["email", "name"])]
    f = findings_by_id(make_site(forms=forms))
    assert f["RGPD-08"].passed is False


def test_rgpd08_pass_get_without_personal_fields():
    forms = [Form(action="/search", method="GET", fields=["query"])]
    f = findings_by_id(make_site(forms=forms))
    assert f["RGPD-08"].passed is True


# ── RGPD-09: política de privacidade ausente ──────────────────────────────

def test_rgpd09_fail_no_policy_url():
    f = findings_by_id(make_site(privacy_policy_url=None))
    assert f["RGPD-09"].passed is False
    assert f["RGPD-09"].severity == Severity.HIGH


def test_rgpd09_pass_with_policy_url():
    f = findings_by_id(make_site(privacy_policy_url="https://exemplo.com/privacidade"))
    assert f["RGPD-09"].passed is True


# ── RGPD-10: política menciona consentimento ──────────────────────────────

def test_rgpd10_fail_no_consent_term():
    f = findings_by_id(make_site(privacy_policy_text="Politica de privacidade do site."))
    assert f["RGPD-10"].passed is False


def test_rgpd10_pass_with_consent_term():
    f = findings_by_id(make_site(privacy_policy_text="O tratamento baseia-se em consentimento do utilizador."))
    assert f["RGPD-10"].passed is True


# ── RGPD-11: direito ao apagamento ────────────────────────────────────────

def test_rgpd11_fail_no_erasure_term():
    f = findings_by_id(make_site(privacy_policy_text="Os seus dados são tratados com segurança."))
    assert f["RGPD-11"].passed is False


def test_rgpd11_pass_with_erasure_term():
    f = findings_by_id(make_site(privacy_policy_text="Tem direito ao apagamento dos seus dados pessoais."))
    assert f["RGPD-11"].passed is True


# ── Todos os findings têm rule_id, category, severity, passed ─────────────

def test_all_findings_have_required_fields():
    findings = run_analysis(make_site(), RULES_PATH)
    assert len(findings) == 19
    for f in findings:
        assert f.rule_id
        assert f.category is not None
        assert f.severity is not None
        assert isinstance(f.passed, bool)
