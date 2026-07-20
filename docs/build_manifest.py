"""Generate a machine-readable manifest of the docs suite.

Outputs docs/manifest.json with one entry per document (front-matter, file
size, link to PDF, link to source Markdown, related requirements).

Idempotent: run as needed.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PDF_DIR = ROOT / "pdfs"
OUT = ROOT / "manifest.json"

FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def parse_fm(text: str) -> dict:
    m = FRONT_RE.match(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def main() -> None:
    manifest = {
        "project": "VentureMiner AI",
        "subtitle": "AI Venture Intelligence Platform",
        "version": "v1.0",
        "generated": __import__("datetime").date.today().isoformat(),
        "total_documents": 0,
        "total_size_bytes": 0,
        "documents": [],
    }

    md_files = sorted([p for p in ROOT.rglob("*.md") if p.name != "README.md"])
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        fm = parse_fm(text)
        h1 = H1_RE.search(text)
        title = fm.get("title") or (h1.group(1).strip() if h1 else md.stem)

        pdf_name = f"{md.parent.name}__{md.stem}.pdf"
        pdf_path = PDF_DIR / pdf_name
        rel_pdf = pdf_path.relative_to(ROOT).as_posix() if pdf_path.exists() else None
        rel_md = md.relative_to(ROOT).as_posix()

        entry = {
            "id": md.stem.split("_", 1)[0],
            "title": title,
            "version": fm.get("version", "v1.0"),
            "date": fm.get("date"),
            "author": fm.get("author"),
            "status": fm.get("status", "Draft"),
            "source_md": rel_md,
            "pdf": rel_pdf,
            "source_bytes": len(text.encode("utf-8")),
            "pdf_bytes": pdf_path.stat().st_size if pdf_path.exists() else 0,
            "folder": md.parent.name,
        }
        manifest["documents"].append(entry)
        manifest["total_size_bytes"] += entry["source_bytes"] + entry["pdf_bytes"]

    manifest["total_documents"] = len(manifest["documents"])
    manifest["total_documents_with_pdf"] = sum(1 for d in manifest["documents"] if d["pdf"])

    OUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} — {manifest['total_documents']} documents, "
          f"{manifest['total_size_bytes']:,} bytes total.")


if __name__ == "__main__":
    main()
