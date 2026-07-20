"""
VentureMiner AI — Master PDF Generator
======================================
Converts every .md file under docs/ into a professionally formatted PDF.

Usage:
    python generate_pdfs.py                 # build all
    python generate_pdfs.py --only 00-Governance/00_*.md
    python generate_pdfs.py --skip-existing

The output goes to docs/pdfs/ with the same filename + .pdf.

Design choices (kept simple, deterministic, dependency-light):
- reportlab Platypus (paragraphs, tables, page breaks)
- python-markdown for inline markdown→XHTML, then parsed for body
- Cover page (title, version, date, author)
- Revision history table sourced from front-matter
- Page footer with page x of y
- Heading styles, monospace, tables, blockquotes, code, lists
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import markdown as md_lib
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "pdfs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_TITLE = "VentureMiner AI"
PROJECT_SUBTITLE = "AI Venture Intelligence Platform"
COMPANY = "ProjectSAAS"
DEFAULT_AUTHOR = "VentureMiner AI Documentation Team"
DEFAULT_VERSION = "v1.0"
DEFAULT_DATE = dt.date.today().isoformat()

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
COL_PRIMARY = colors.HexColor("#0F172A")     # slate-900
COL_ACCENT = colors.HexColor("#2563EB")      # blue-600
COL_MUTED = colors.HexColor("#64748B")        # slate-500
COL_TABLE_HDR = colors.HexColor("#1E293B")    # slate-800
COL_TABLE_ROW = colors.HexColor("#F8FAFC")    # slate-50
COL_CODE_BG = colors.HexColor("#F1F5F9")      # slate-100


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}
    styles["CoverTitle"] = ParagraphStyle(
        "CoverTitle", parent=base["Title"], fontName="Helvetica-Bold",
        fontSize=28, leading=34, textColor=COL_PRIMARY, spaceAfter=12,
        alignment=TA_LEFT,
    )
    styles["CoverSubtitle"] = ParagraphStyle(
        "CoverSubtitle", parent=base["Heading2"], fontName="Helvetica",
        fontSize=14, leading=18, textColor=COL_ACCENT, spaceAfter=24,
    )
    styles["CoverMeta"] = ParagraphStyle(
        "CoverMeta", parent=base["Normal"], fontName="Helvetica",
        fontSize=10.5, leading=14, textColor=COL_MUTED, spaceAfter=4,
    )
    styles["H1"] = ParagraphStyle(
        "H1", parent=base["Heading1"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, textColor=COL_PRIMARY, spaceBefore=14, spaceAfter=8,
    )
    styles["H2"] = ParagraphStyle(
        "H2", parent=base["Heading2"], fontName="Helvetica-Bold",
        fontSize=14, leading=18, textColor=COL_PRIMARY, spaceBefore=10, spaceAfter=6,
    )
    styles["H3"] = ParagraphStyle(
        "H3", parent=base["Heading3"], fontName="Helvetica-Bold",
        fontSize=12, leading=16, textColor=COL_ACCENT, spaceBefore=8, spaceAfter=4,
    )
    styles["H4"] = ParagraphStyle(
        "H4", parent=base["Heading4"], fontName="Helvetica-BoldOblique",
        fontSize=11, leading=15, textColor=COL_PRIMARY, spaceBefore=6, spaceAfter=3,
    )
    styles["Body"] = ParagraphStyle(
        "Body", parent=base["Normal"], fontName="Helvetica",
        fontSize=10, leading=14, textColor=COL_PRIMARY, spaceAfter=6, alignment=TA_LEFT,
    )
    styles["Bullet"] = ParagraphStyle(
        "Bullet", parent=styles["Body"], leftIndent=14, bulletIndent=2,
    )
    styles["Code"] = ParagraphStyle(
        "Code", parent=base["Code"], fontName="Courier",
        fontSize=9, leading=12, textColor=COL_PRIMARY, backColor=COL_CODE_BG,
        leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=4,
    )
    styles["Blockquote"] = ParagraphStyle(
        "Blockquote", parent=styles["Body"], leftIndent=18, rightIndent=8,
        fontName="Helvetica-Oblique", textColor=COL_MUTED, borderColor=COL_ACCENT,
        borderWidth=0, borderPadding=4, spaceBefore=4, spaceAfter=8,
    )
    styles["TOCEntry"] = ParagraphStyle(
        "TOCEntry", parent=styles["Body"], fontSize=10, leading=14,
    )
    return styles


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    return meta, text[m.end():]


def extract_title(text: str) -> str:
    m = H1_RE.search(text)
    return m.group(1).strip() if m else "Untitled Document"


def collect_headings(md_text: str) -> list[tuple[int, str, str]]:
    """Return (level, plain text, anchor) for every H1/H2/H3."""
    out: list[tuple[int, str, str]] = []
    in_fm = False
    for line in md_text.splitlines():
        if line.strip() == "---":
            in_fm = not in_fm
            continue
        if in_fm:
            continue
        m = re.match(r"^(#{1,3})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            out.append((level, text, anchor))
    return out


# ---------------------------------------------------------------------------
# XHTML → reportlab flowables
# ---------------------------------------------------------------------------
INLINE_TAGS = {
    "strong": ("<b>", "</b>"),
    "b": ("<b>", "</b>"),
    "em": ("<i>", "</i>"),
    "i": ("<i>", "</i>"),
    "code": ("<font face='Courier' size='9'>", "</font>"),
}


def inline_to_rl(html: str) -> str:
    """Convert a small set of inline tags to reportlab paragraph markup."""
    s = html
    for tag, (open_, close_) in INLINE_TAGS.items():
        s = re.sub(rf"<{tag}(?:\s[^>]*)?>", open_, s, flags=re.IGNORECASE)
        s = re.sub(rf"</{tag}>", close_, s, flags=re.IGNORECASE)
    # Strip any other tags but keep their text
    s = re.sub(r"<[^>]+>", "", s)
    # Escape stray reportlab-sensitive chars
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return s


def md_to_flowables(md_text: str, styles: dict[str, ParagraphStyle]) -> list:
    flow: list = []
    html = md_lib.markdown(
        md_text,
        extensions=["extra", "tables", "fenced_code", "sane_lists", "toc"],
        output_format="xhtml",
    )

    # Walk top-level children of the markdown root
    root = ET.fromstring(f"<root>{html}</root>")

    for child in list(root):
        tag = child.tag.lower()
        if tag in ("h1", "h2", "h3", "h4"):
            level = int(tag[1])
            text = "".join(child.itertext()).strip()
            style = styles[f"H{min(level, 4)}"]
            flow.append(Paragraph(inline_to_rl(text), style))
        elif tag == "p":
            text = ET.tostring(child, encoding="unicode")
            text = re.sub(r"^<p[^>]*>", "", text)
            text = re.sub(r"</p>\s*$", "", text)
            if not text.strip():
                continue
            flow.append(Paragraph(inline_to_rl(text), styles["Body"]))
        elif tag == "blockquote":
            inner_html = ET.tostring(child, encoding="unicode")
            inner_html = re.sub(r"^<blockquote[^>]*>", "", inner_html)
            inner_html = re.sub(r"</blockquote>\s*$", "", inner_html)
            flow.append(Paragraph(inline_to_rl(inner_html), styles["Blockquote"]))
        elif tag == "ul":
            for li in child.findall("li"):
                li_html = ET.tostring(li, encoding="unicode")
                li_html = re.sub(r"^<li[^>]*>", "", li_html)
                li_html = re.sub(r"</li>\s*$", "", li_html)
                # Strip nested <ul>/<ol> for simplicity in this MVP renderer
                li_html = re.sub(r"<\/?(ul|ol)[^>]*>", "", li_html)
                li_html = re.sub(r"<li[^>]*>", " — ", li_html)
                flow.append(Paragraph("• " + inline_to_rl(li_html), styles["Bullet"]))
            flow.append(Spacer(1, 4))
        elif tag == "ol":
            for i, li in enumerate(child.findall("li"), start=1):
                li_html = ET.tostring(li, encoding="unicode")
                li_html = re.sub(r"^<li[^>]*>", "", li_html)
                li_html = re.sub(r"</li>\s*$", "", li_html)
                li_html = re.sub(r"<\/?(ul|ol)[^>]*>", "", li_html)
                li_html = re.sub(r"<li[^>]*>", " — ", li_html)
                flow.append(Paragraph(f"{i}. " + inline_to_rl(li_html), styles["Bullet"]))
            flow.append(Spacer(1, 4))
        elif tag == "pre":
            code_text = ET.tostring(child, encoding="unicode")
            code_text = re.sub(r"^<pre[^>]*>", "", code_text)
            code_text = re.sub(r"</pre>\s*$", "", code_text)
            code_text = re.sub(r"<code[^>]*>", "", code_text)
            code_text = re.sub(r"</code>", "", code_text)
            # Preserve indentation
            for line in code_text.splitlines() or [""]:
                flow.append(Paragraph(inline_to_rl(line) or "&nbsp;", styles["Code"]))
            flow.append(Spacer(1, 4))
        elif tag == "table":
            data: list[list] = []
            for tr in child.findall("tbody/tr") or child.findall("tr"):
                row: list = []
                for cell in tr.findall("th") + tr.findall("td"):
                    c_html = ET.tostring(cell, encoding="unicode")
                    c_html = re.sub(r"<\/?(th|td)[^>]*>", "", c_html)
                    row.append(Paragraph(inline_to_rl(c_html), styles["Body"]))
                if row:
                    data.append(row)
            if data:
                # First row is header if any <th> present in thead
                tbl = Table(data, repeatRows=1)
                tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COL_TABLE_HDR),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COL_TABLE_ROW]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                flow.append(tbl)
                flow.append(Spacer(1, 6))
        elif tag == "hr":
            flow.append(Spacer(1, 8))
        else:
            # Fallback: dump the text content
            text = "".join(child.itertext()).strip()
            if text:
                flow.append(Paragraph(inline_to_rl(text), styles["Body"]))
    return flow


# ---------------------------------------------------------------------------
# Page templates (cover, TOC, body) with running footer
# ---------------------------------------------------------------------------
class Doc(BaseDocTemplate):
    def __init__(self, filename: str, title: str, **kw):
        super().__init__(filename, pagesize=A4,
                         leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                         topMargin=2.0 * cm, bottomMargin=2.0 * cm, **kw)
        self.title = title
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="body")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[frame], onPage=self._cover_decor),
            PageTemplate(id="body", frames=[frame], onPage=self._body_decor),
        ])

    # -- running decorations
    def _cover_decor(self, canv, doc):
        canv.saveState()
        canv.setFillColor(COL_PRIMARY)
        canv.rect(0, 0, A4[0], 4 * cm, fill=1, stroke=0)
        canv.setFillColor(COL_ACCENT)
        canv.rect(0, 4 * cm, A4[0], 0.15 * cm, fill=1, stroke=0)
        canv.setFillColor(COL_MUTED)
        canv.setFont("Helvetica", 9)
        canv.drawString(2.2 * cm, 1.2 * cm, f"{COMPANY} • {PROJECT_TITLE}")
        canv.drawRightString(A4[0] - 2.2 * cm, 1.2 * cm, DEFAULT_DATE)
        canv.restoreState()

    def _body_decor(self, canv, doc):
        canv.saveState()
        canv.setStrokeColor(COL_MUTED)
        canv.setLineWidth(0.4)
        canv.line(2.2 * cm, 1.6 * cm, A4[0] - 2.2 * cm, 1.6 * cm)
        canv.setFont("Helvetica", 8.5)
        canv.setFillColor(COL_MUTED)
        canv.drawString(2.2 * cm, 1.0 * cm, f"{PROJECT_TITLE} — {self.title}")
        canv.drawRightString(A4[0] - 2.2 * cm, 1.0 * cm, f"Page {doc.page}")
        canv.restoreState()


# ---------------------------------------------------------------------------
# Per-document builder
# ---------------------------------------------------------------------------
def build_pdf(md_path: Path, pdf_path: Path) -> None:
    raw = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    title = meta.get("title") or extract_title(body)
    version = meta.get("version", DEFAULT_VERSION)
    author = meta.get("author", DEFAULT_AUTHOR)
    date = meta.get("date", DEFAULT_DATE)
    rev_rows = []

    # Parse revision history if present (under "## Revision History")
    rev_match = re.search(
        r"##\s*Revision History\s*\n+(.*?)(?=\n##\s|\Z)", body, flags=re.DOTALL | re.IGNORECASE,
    )
    if rev_match:
        rev_block = rev_match.group(1)
        for line in rev_block.splitlines():
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 3 or set(cells[0]) <= {"-"}:
                continue
            if cells[0].lower() in {"version", "date"}:
                continue
            rev_rows.append(cells[:4] if len(cells) >= 4 else cells + [""] * (4 - len(cells)))

    styles = build_styles()
    doc = Doc(str(pdf_path), title=title)
    story: list = []

    # ---- Cover
    story.append(Spacer(1, 4.5 * cm))
    story.append(Paragraph(inline_to_rl(PROJECT_TITLE), styles["CoverTitle"]))
    story.append(Paragraph(inline_to_rl(title), styles["CoverSubtitle"]))
    story.append(Spacer(1, 1.0 * cm))
    for label, value in [
        ("Document", f"{md_path.parent.name} / {md_path.stem}"),
        ("Version", version),
        ("Date", date),
        ("Author", author),
        ("Status", meta.get("status", "Draft")),
        ("Project", f"{PROJECT_TITLE} — {PROJECT_SUBTITLE}"),
    ]:
        story.append(Paragraph(f"<b>{label}:</b> {inline_to_rl(value)}", styles["CoverMeta"]))

    story.append(Spacer(1, 1.0 * cm))

    # Revision history on cover
    if rev_rows:
        story.append(Paragraph("Revision History", styles["H3"]))
        header = ["Version", "Date", "Author", "Summary"]
        data = [header] + rev_rows[:12]
        tbl = Table(data, colWidths=[2.2 * cm, 2.6 * cm, 3.4 * cm, 8.0 * cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COL_TABLE_HDR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COL_TABLE_ROW]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl)

    story.append(PageBreak())

    # ---- TOC
    story.append(Paragraph("Table of Contents", styles["H1"]))
    headings = collect_headings(body)
    for level, text, _anchor in headings:
        indent = (level - 1) * 18
        story.append(Paragraph(
            f'<font color="#64748B">{"&nbsp;" * (indent // 6)}</font>'
            f'{inline_to_rl(text)}', styles["TOCEntry"]))
    if not headings:
        story.append(Paragraph("(No headings found.)", styles["Body"]))
    story.append(PageBreak())

    # ---- Body
    story.extend(md_to_flowables(body, styles))

    doc.build(story)
    print(f"  [OK]  {pdf_path.name}  ({pdf_path.stat().st_size:,} bytes)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="Substring match to limit which .md are built")
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()

    md_files = sorted(ROOT.rglob("*.md"))
    md_files = [p for p in md_files if p.name != "README.md"]
    if args.only:
        needle = args.only.replace("\\", "/")
        md_files = [p for p in md_files if needle in str(p).replace("\\", "/")]

    if not md_files:
        print("No markdown files found.")
        return 1

    for md_path in md_files:
        rel = md_path.relative_to(ROOT)
        pdf_path = OUT_DIR / (rel.parent.as_posix().replace("/", "__") + "__" + md_path.stem + ".pdf")
        # Cleaner: keep subfolder prefix for traceability
        pdf_path = OUT_DIR / f"{rel.parent.name}__{md_path.stem}.pdf"
        if args.skip_existing and pdf_path.exists():
            print(f"  [SKIP]  {pdf_path.name}  (already exists)")
            continue
        try:
            build_pdf(md_path, pdf_path)
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {md_path.name}: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
