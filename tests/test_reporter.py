import os
import tempfile
from src.analyzer.reporter import generate_html_report, generate_pdf_report
from src.models.finding import Finding, Severity, FindingCategory


def make_finding(passed: bool = False) -> Finding:
    return Finding(
        rule_id="RGPD-01",
        category=FindingCategory.CONSENT,
        severity=Severity.HIGH,
        title="Banner de consentimento ausente",
        description="O site não apresenta banner de cookies.",
        evidence="consent_banner_detected = False",
        recommendation="Implementar CMP.",
        article="Art. 6.º RGPD",
        passed=passed,
    )


def test_generate_html_report_contains_title():
    finding = make_finding(passed=False)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as tmp:
        tmp_name = tmp.name
    generate_html_report([finding], tmp_name)
    with open(tmp_name, encoding="utf-8") as f:
        content = f.read()
    os.remove(tmp_name)
    assert "Banner de consentimento ausente" in content


def test_generate_html_report_shows_passed_section():
    f1 = make_finding(passed=False)
    f2 = make_finding(passed=True)
    f2.rule_id = "RGPD-09"
    f2.title = "Política de privacidade ausente"
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as tmp:
        tmp_name = tmp.name
    generate_html_report([f1, f2], tmp_name)
    with open(tmp_name, encoding="utf-8") as f:
        content = f.read()
    os.remove(tmp_name)
    assert "Não-Conformidades" in content
    assert "Regras Cumpridas" in content


def test_generate_html_report_with_site_url():
    from src.models.site_data import SiteData
    site = SiteData(url="https://test.com", final_url="https://test.com")
    finding = make_finding()
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as tmp:
        tmp_name = tmp.name
    generate_html_report([finding], tmp_name, site_data=site)
    with open(tmp_name, encoding="utf-8") as f:
        content = f.read()
    os.remove(tmp_name)
    assert "test.com" in content


def test_generate_pdf_report_creates_file():
    finding = make_finding()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_name = tmp.name
    generate_pdf_report([finding], tmp_name)
    size = os.path.getsize(tmp_name)
    os.remove(tmp_name)
    assert size > 0
