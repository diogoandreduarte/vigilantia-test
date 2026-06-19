"""
Acrescenta o resultado de um scan ao histórico JSON do site.
Uso: python scripts/append_scan.py <label> <url> <date> <json_file> <docs_file> [pdf_src]
"""
import json
import os
import shutil
import sys


def main():
    args = sys.argv[1:]
    label, site_url, date, json_file, docs_file = args[:5]
    pdf_src = args[5] if len(args) > 5 and args[5] else None
    html_src = args[6] if len(args) > 6 else None

    with open(json_file, encoding="utf-8") as f:
        result = json.load(f)

    scan_entry = {
        "date": date,
        "passed": result["summary"]["passed"],
        "failed": result["summary"]["failed"],
        "total":  result["summary"]["total"],
        "findings": result["findings"],
    }

    # Copiar PDF para docs/data/ e registar no histórico
    if pdf_src and os.path.exists(pdf_src):
        pdf_dest_name = f"{label}_{date}.pdf"
        pdf_dest = os.path.join(os.path.dirname(docs_file), pdf_dest_name)
        if os.path.abspath(pdf_src) != os.path.abspath(pdf_dest):
            shutil.copy2(pdf_src, pdf_dest)
        scan_entry["pdf"] = pdf_dest_name
        print(f"PDF guardado: {pdf_dest}")

    # Copiar HTML para docs/data/ e registar no histórico
    if html_src and os.path.exists(html_src):
        html_dest_name = f"{label}_{date}.html"
        html_dest = os.path.join(os.path.dirname(docs_file), html_dest_name)
        if os.path.abspath(html_src) != os.path.abspath(html_dest):
            shutil.copy2(html_src, html_dest)
        scan_entry["html"] = html_dest_name
        print(f"HTML guardado: {html_dest}")

    if os.path.exists(docs_file):
        with open(docs_file, encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {"site": label, "url": site_url, "scans": []}

    history["scans"].append(scan_entry)

    with open(docs_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    print(f"Updated {docs_file}: {len(history['scans'])} scans total")

    # Atualizar manifest.json automaticamente
    manifest_file = os.path.join(os.path.dirname(docs_file), "manifest.json")
    docs_filename = os.path.basename(docs_file)

    if os.path.exists(manifest_file):
        with open(manifest_file, encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = []

    if docs_filename not in manifest:
        manifest.append(docs_filename)
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"Added {docs_filename} to manifest.json")


if __name__ == "__main__":
    main()
