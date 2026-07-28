import json
import re
import subprocess
import sys
import tempfile
import os
from pathlib import Path
from typing import Optional

import typer

from src.scraper.collector import collect_site_data
from src.analyzer.rule_engine import run_analysis
from src.analyzer.reporter import generate_html_report, generate_pdf_report, generate_json_report

app = typer.Typer(help="Vigilantia — análise automática de conformidade RGPD")


def _history_path(url: str) -> Optional[Path]:
    """Deriva o caminho do ficheiro de histórico a partir do URL, se docs/data/ existir."""
    data_dir = Path("docs/data")
    if not data_dir.exists():
        return None
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or ""
        hostname = hostname.replace("www.", "")
        label = re.sub(r"[^a-z0-9]", "_", hostname.lower()).strip("_")
        return data_dir / f"{label}.json"
    except Exception:
        return None


def _append_to_history(url: str, result_json_path: str, pdf_path: Optional[str] = None, html_path: Optional[str] = None) -> Optional[Path]:
    """Appenda o resultado ao histórico do dashboard."""
    hist_path = _history_path(url)
    if not hist_path:
        return None
    try:
        from datetime import date
        script = Path(__file__).parent.parent / "scripts" / "append_scan.py"
        label = hist_path.stem
        today = date.today().isoformat()
        cmd = [sys.executable, str(script), label, url, today, result_json_path, str(hist_path)]
        cmd.append(pdf_path or "")
        if html_path:
            cmd.append(html_path)
        subprocess.run(cmd, check=True, capture_output=True)
        return hist_path
    except Exception:
        return None


@app.command()
def analyze(
    url: str = typer.Argument(..., help="URL do site a analisar"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Guardar resultado JSON neste ficheiro"),
    html: Optional[Path] = typer.Option(None, "--html", help="Gerar relatório HTML neste ficheiro"),
    pdf: Optional[Path] = typer.Option(None, "--pdf", help="Gerar relatório PDF neste ficheiro"),
    rules: Path = typer.Option("rules/gdpr_rules.yaml", "--rules", "-r", help="Ficheiro de regras YAML"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Mostrar apenas não-conformidades"),
    no_history: bool = typer.Option(False, "--no-history", help="Não atualizar o histórico do dashboard"),
):
    """Analisa um website e verifica conformidade com o RGPD."""

    typer.echo(f"Analisando: {url}")

    # 1. Scraping
    try:
        site_data = collect_site_data(url)
    except Exception as e:
        typer.echo(f"[ERRO] Falha ao recolher dados do site: {e}", err=True)
        raise typer.Exit(code=2)

    # 2. Análise RGPD
    try:
        findings = run_analysis(site_data, rules_path=str(rules))
    except Exception as e:
        typer.echo(f"[ERRO] Falha ao analisar regras: {e}", err=True)
        raise typer.Exit(code=3)

    # 3. Output no terminal
    failed = [f for f in findings if not f.passed]
    passed_list = [f for f in findings if f.passed]

    typer.echo(f"\nResultado: {len(passed_list)}/{len(findings)} regras OK  |  {len(failed)} não-conformidades\n")

    if failed:
        typer.echo("NAO CONFORMIDADES:")
        for f in failed:
            badge = {"high": "[HIGH]", "medium": "[MED]", "low": "[LOW]", "info": "[INFO]"}.get(f.severity.value, "[-]")
            typer.echo(f"  {badge} [{f.rule_id}] {f.title}")
            if f.evidence:
                typer.echo(f"     Evidencia: {f.evidence}")
            typer.echo(f"     Recomendacao: {f.recommendation}")
            if f.article:
                typer.echo(f"     Artigo: {f.article}")
            typer.echo()

    if not quiet and passed_list:
        typer.echo("CONFORMIDADES:")
        for f in passed_list:
            typer.echo(f"  [OK] [{f.rule_id}] {f.title}")
        typer.echo()

    # 4. Relatório HTML
    if html:
        try:
            generate_html_report(findings, str(html), site_data=site_data)
            typer.echo(f"Relatorio HTML: {html}")
        except Exception as e:
            typer.echo(f"[ERRO] HTML: {e}", err=True)

    # 5. Relatório PDF
    if pdf:
        try:
            generate_pdf_report(findings, str(pdf), site_data=site_data)
            typer.echo(f"Relatorio PDF: {pdf}")
        except Exception as e:
            typer.echo(f"[ERRO] PDF: {e}", err=True)

    # 6. JSON — sempre guardado num temp para o histórico; opcionalmente no path pedido
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        tmp_path = tmp.name
    try:
        generate_json_report(findings, tmp_path, site_data=site_data)

        if output:
            import shutil
            shutil.copy(tmp_path, str(output))
            typer.echo(f"JSON guardado em: {output}")
        else:
            typer.echo(open(tmp_path, encoding="utf-8").read())

        # 7. Histórico do dashboard (automático se docs/data/ existir)
        if not no_history:
            pdf_for_history: Optional[str] = None
            html_for_history: Optional[str] = None
            hist_path = _history_path(url)
            if hist_path:
                from datetime import date
                today_str = date.today().isoformat()
                try:
                    pdf_for_history = str(hist_path.parent / f"{hist_path.stem}_{today_str}.pdf")
                    generate_pdf_report(findings, pdf_for_history, site_data=site_data)
                except Exception as e:
                    typer.echo(f"[AVISO] PDF do historico falhou: {e}", err=True)
                    pdf_for_history = None
                try:
                    html_for_history = str(hist_path.parent / f"{hist_path.stem}_{today_str}.html")
                    generate_html_report(findings, html_for_history, site_data=site_data)
                except Exception:
                    html_for_history = None

            hist = _append_to_history(url, tmp_path, pdf_path=pdf_for_history, html_path=html_for_history)
            if hist:
                typer.echo(f"Historico atualizado: {hist}")
                if pdf_for_history and os.path.exists(pdf_for_history):
                    typer.echo(f"PDF guardado: {pdf_for_history}")
                if html_for_history and os.path.exists(html_for_history):
                    typer.echo(f"HTML guardado: {html_for_history}")
    finally:
        os.remove(tmp_path)


@app.command()
def serve(
    port: int = typer.Option(8080, "--port", "-p", help="Porta do servidor local"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Não abrir o browser automaticamente"),
):
    """Abre o dashboard localmente num servidor HTTP."""
    import http.server
    import threading
    import webbrowser

    docs_dir = Path("docs")
    if not docs_dir.exists():
        typer.echo("[ERRO] Pasta docs/ não encontrada. Corre o comando a partir da raiz do projeto.", err=True)
        raise typer.Exit(code=1)

    os.chdir(docs_dir)

    class _Handler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Connection", "close")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            super().end_headers()
        def log_message(self, *args):
            pass

    with http.server.ThreadingHTTPServer(("", port), _Handler) as httpd:
        url = f"http://localhost:{port}"
        typer.echo(f"Dashboard disponível em: {url}")
        typer.echo("Ctrl+C para parar.")
        if not no_browser:
            threading.Timer(0.5, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            typer.echo("\nServidor parado.")


if __name__ == "__main__":
    app()
