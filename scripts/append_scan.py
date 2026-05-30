"""
Acrescenta o resultado de um scan ao histórico JSON do site.
Uso: python scripts/append_scan.py <label> <url> <date> <json_file> <docs_file>
"""
import json
import os
import sys


def main():
    label, site_url, date, json_file, docs_file = sys.argv[1:6]

    with open(json_file, encoding="utf-8") as f:
        result = json.load(f)

    scan_entry = {
        "date": date,
        "passed": result["summary"]["passed"],
        "failed": result["summary"]["failed"],
        "total":  result["summary"]["total"],
        "findings": result["findings"],
    }

    if os.path.exists(docs_file):
        with open(docs_file, encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {"site": label, "url": site_url, "scans": []}

    history["scans"].append(scan_entry)

    with open(docs_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    print(f"Updated {docs_file}: {len(history['scans'])} scans total")


if __name__ == "__main__":
    main()
