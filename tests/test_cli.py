import json
import subprocess
import sys


def test_cli_analyze_returns_json(tmp_path):
    output_json = tmp_path / "resultado.json"
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "analyze", "https://example.com",
         "--output", str(output_json), "--quiet", "--no-history"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output_json.exists()
    data = json.loads(output_json.read_text(encoding="utf-8"))
    assert "url" in data
    assert "findings" in data
    assert "summary" in data
    assert data["summary"]["total"] == 19


def test_cli_analyze_generates_html(tmp_path):
    html_path = tmp_path / "relatorio.html"
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "analyze", "https://example.com",
         "--html", str(html_path), "--quiet", "--no-history"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")
    assert "Relatório de Conformidade RGPD" in content


def test_cli_analyze_invalid_url_exits_nonzero():
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "analyze", "nao-e-um-url", "--no-history"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0


def test_cli_serve_help():
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "serve", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "8080" in result.stdout
