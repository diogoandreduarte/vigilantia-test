import re
import yaml
import requests
from pathlib import Path
from typing import List, Optional, Tuple
from src.models.site_data import SiteData, ThirdPartyScript
from src.models.finding import Finding, FindingCategory, Severity
from src.analyzer.privacy_text import analyze_policy, PolicyFeatures


_CATEGORY_MAP = {
    "consentimento": FindingCategory.CONSENT,
    "cookies": FindingCategory.COOKIES,
    "terceiros": FindingCategory.THIRD_PARTY,
    "formularios": FindingCategory.FORMS,
    "politica": FindingCategory.POLICY,
}

_SEVERITY_MAP = {
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
    "info": Severity.INFO,
}

# ── Classificação de scripts de terceiros por URL ─────────────────────────

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


def _enrich_scripts(scripts: List[ThirdPartyScript]) -> List[ThirdPartyScript]:
    """Reclassifica scripts com category='unknown' usando URL matching."""
    result = []
    for s in scripts:
        if s.category == "unknown":
            cat = _classify_script(s.src)
            result.append(ThirdPartyScript(src=s.src, category=cat))
        else:
            result.append(s)
    return result


# ── Fetch automático do texto da política de privacidade ──────────────────

def _fetch_policy_text(url: str) -> Optional[str]:
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:20000]
    except Exception:
        return None


class RuleDefinition:
    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.category: str = data["category"]
        self.name: str = data["name"]
        self.description: str = data["description"]
        self.severity: str = data["severity"]
        self.article: Optional[str] = data.get("article")
        self.recommendation: str = data["recommendation"]
        self.keywords: List[str] = data.get("keywords", [])


def load_rules(yaml_path: str) -> List[RuleDefinition]:
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [RuleDefinition(r) for r in data.get("rules", [])]


# ── Avaliadores estruturais ────────────────────────────────────────────────

def _eval_rgpd01(site: SiteData, rule: RuleDefinition) -> Tuple[bool, Optional[str]]:
    passed = site.consent_banner_detected
    return passed, None if passed else "consent_banner_detected = False"


def _eval_rgpd02(site: SiteData, rule: RuleDefinition) -> Tuple[bool, Optional[str]]:
    from urllib.parse import urlparse
    site_host = urlparse(site.final_url).hostname or ""
    third_party = [
        c for c in site.cookies
        if c.domain and not site_host.endswith(c.domain.lstrip("."))
    ]
    passed = len(third_party) == 0
    return passed, f"Cookies de terceiros: {[c.name for c in third_party]}" if not passed else None


def _eval_rgpd03(site: SiteData, rule: RuleDefinition) -> Tuple[bool, Optional[str]]:
    tracking = [c for c in site.cookies if not c.secure and c.domain != ""]
    passed = len(tracking) == 0
    return passed, f"Cookies sem Secure: {[c.name for c in tracking]}" if not passed else None


def _eval_rgpd04(site: SiteData, rule: RuleDefinition) -> Tuple[bool, Optional[str]]:
    insecure = [c for c in site.cookies if not c.httpOnly]
    passed = len(insecure) == 0
    return passed, f"Cookies sem HttpOnly: {[c.name for c in insecure]}" if not passed else None


def _eval_rgpd05(site: SiteData, rule: RuleDefinition) -> Tuple[bool, Optional[str]]:
    analytics = [s for s in site.third_party_scripts if s.category == "analytics"]
    passed = len(analytics) == 0 or site.consent_banner_detected
    return passed, f"Scripts de analytics sem consentimento: {[s.src for s in analytics]}" if not passed else None


def _eval_rgpd06(site: SiteData, rule: RuleDefinition) -> Tuple[bool, Optional[str]]:
    ads = [s for s in site.third_party_scripts if s.category == "advertising"]
    passed = len(ads) == 0 or site.consent_banner_detected
    return passed, f"Scripts de publicidade sem consentimento: {[s.src for s in ads]}" if not passed else None


def _eval_rgpd07(site: SiteData, rule: RuleDefinition) -> Tuple[bool, Optional[str]]:
    without_notice = [f for f in site.forms if not f.has_privacy_notice]
    passed = len(without_notice) == 0
    return passed, f"{len(without_notice)} formulário(s) sem aviso de privacidade" if not passed else None


def _eval_rgpd08(site: SiteData, rule: RuleDefinition) -> Tuple[bool, Optional[str]]:
    personal_fields = {"email", "name", "nome", "password", "senha", "phone", "telefone", "nif", "address", "morada"}
    bad_forms = [
        f for f in site.forms
        if f.method.upper() == "GET" and any(field.lower() in personal_fields for field in f.fields)
    ]
    passed = len(bad_forms) == 0
    return passed, f"{len(bad_forms)} formulário(s) com dados pessoais em GET" if not passed else None


def _eval_rgpd09(site: SiteData, rule: RuleDefinition) -> Tuple[bool, Optional[str]]:
    passed = site.privacy_policy_url is not None
    return passed, None if passed else "privacy_policy_url = None"


# ── Avaliadores de texto de política ──────────────────────────────────────

_POLICY_FEATURE_MAP = {
    "RGPD-10": "has_consent_terms",
    "RGPD-11": "has_erasure_terms",
    "RGPD-12": "has_controller_terms",
    "RGPD-13": "has_dpo_terms",
    "RGPD-15": "has_access_right_terms",
    "RGPD-16": "has_international_transfer_terms",
    "RGPD-17": "has_retention_terms",
}


def _eval_policy_feature(rule_id: str, pf: PolicyFeatures) -> Tuple[bool, Optional[str]]:
    if not pf.language_detected and not any([
        pf.has_consent_terms, pf.has_erasure_terms,
        pf.has_controller_terms, pf.has_dpo_terms,
    ]):
        return False, "Texto da política de privacidade não encontrado"
    passed = getattr(pf, _POLICY_FEATURE_MAP[rule_id])
    return passed, f"Termos ausentes na política: {pf.missing_terms}" if not passed else None


def _eval_rgpd14(pf: PolicyFeatures, site_language: str) -> Tuple[bool, Optional[str]]:
    if not pf.language_detected or site_language == "unknown":
        return True, None
    passed = pf.language_detected == site_language
    return passed, f"Site: {site_language}, Política: {pf.language_detected}" if not passed else None


def _eval_rgpd18(site: SiteData, rule: RuleDefinition) -> Tuple[bool, Optional[str]]:
    bad = [f for f in site.forms if not f.password_autocomplete_ok]
    passed = len(bad) == 0
    return passed, f"{len(bad)} formulário(s) com campos de password sem autocomplete adequado" if not passed else None


_UA_PATTERN = re.compile(r"\banalytics\.js\b|\bga\.js\b", re.IGNORECASE)


def _eval_rgpd19(site: SiteData, rule: RuleDefinition) -> Tuple[bool, Optional[str]]:
    ua_scripts = [s for s in site.third_party_scripts if _UA_PATTERN.search(s.src)]
    if not ua_scripts:
        return True, None
    return False, f"Universal Analytics detetado: {[s.src for s in ua_scripts]} — verificar anonymize_ip"


_STRUCT_EVALUATORS = {
    "RGPD-01": _eval_rgpd01,
    "RGPD-02": _eval_rgpd02,
    "RGPD-03": _eval_rgpd03,
    "RGPD-04": _eval_rgpd04,
    "RGPD-05": _eval_rgpd05,
    "RGPD-06": _eval_rgpd06,
    "RGPD-07": _eval_rgpd07,
    "RGPD-08": _eval_rgpd08,
    "RGPD-09": _eval_rgpd09,
    "RGPD-18": _eval_rgpd18,
    "RGPD-19": _eval_rgpd19,
}


def evaluate_rules(site: SiteData, rules: List[RuleDefinition]) -> List[Finding]:
    policy_features = analyze_policy(
        site.privacy_policy_text or "", site_language=site.language
    )

    findings = []
    for rule in rules:
        try:
            if rule.id in _STRUCT_EVALUATORS:
                passed, evidence = _STRUCT_EVALUATORS[rule.id](site, rule)
            elif rule.id in _POLICY_FEATURE_MAP:
                passed, evidence = _eval_policy_feature(rule.id, policy_features)
            elif rule.id == "RGPD-14":
                passed, evidence = _eval_rgpd14(policy_features, site.language)
            else:
                continue
        except Exception:
            passed, evidence = False, "Erro ao avaliar a regra"

        findings.append(Finding(
            rule_id=rule.id,
            category=_CATEGORY_MAP.get(rule.category, FindingCategory.POLICY),
            severity=_SEVERITY_MAP.get(rule.severity, Severity.MEDIUM),
            title=rule.name,
            description=rule.description,
            evidence=evidence,
            recommendation=rule.recommendation,
            article=rule.article,
            passed=passed,
        ))
    return findings


def run_analysis(site: SiteData, rules_path: Optional[str] = None) -> List[Finding]:
    if rules_path is None:
        rules_path = str(Path(__file__).parent.parent.parent / "rules" / "gdpr_rules.yaml")

    # 1. Enriquecer categorias de scripts "unknown"
    enriched_scripts = _enrich_scripts(site.third_party_scripts)
    site = site.model_copy(update={"third_party_scripts": enriched_scripts})

    # 2. Buscar texto da política se URL existe mas texto está em falta
    if site.privacy_policy_url and not site.privacy_policy_text:
        text = _fetch_policy_text(site.privacy_policy_url)
        if text:
            site = site.model_copy(update={"privacy_policy_text": text})

    rules = load_rules(rules_path)
    return evaluate_rules(site, rules)
