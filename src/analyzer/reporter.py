import json
from pathlib import Path
from typing import List, Optional
from src.models.finding import Finding, Severity
from src.models.site_data import SiteData
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


def _build_context(findings: List[Finding], site_data: Optional[SiteData] = None) -> dict:
    summary = {s: 0 for s in Severity}
    for f in findings:
        if not f.passed:
            summary[f.severity] += 1

    return {
        "findings": findings,
        "failed": [f for f in findings if not f.passed],
        "passed": [f for f in findings if f.passed],
        "summary": summary,
        "site_url": site_data.url if site_data else None,
        "scraped_at": site_data.scraped_at.strftime("%Y-%m-%d %H:%M") if site_data else None,
        "legal_disclaimer": (
            "Este relatório é gerado automaticamente e não substitui uma auditoria jurídica profissional."
        ),
    }


def generate_html_report(
    findings: List[Finding],
    output_path: str,
    template_dir: str = "templates",
    site_data: Optional[SiteData] = None,
) -> None:
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report.html.j2")
    rendered = template.render(**_build_context(findings, site_data))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)


def generate_pdf_report(
    findings: List[Finding],
    output_path: str,
    template_dir: str = "templates",
    site_data: Optional[SiteData] = None,
) -> None:
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report.html.j2")
    rendered = template.render(**_build_context(findings, site_data))
    HTML(string=rendered).write_pdf(output_path)


def generate_json_report(
    findings: List[Finding],
    output_path: str,
    site_data: Optional[SiteData] = None,
) -> None:
    failed = [f for f in findings if not f.passed]
    result = {
        "url": site_data.url if site_data else None,
        "site_data": site_data.model_dump(mode="json") if site_data else None,
        "summary": {
            "total": len(findings),
            "passed": len(findings) - len(failed),
            "failed": len(failed),
        },
        "findings": [f.model_dump(mode="json") for f in findings],
    }
    Path(output_path).write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
