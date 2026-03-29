"""Generate a PDF version of the technical report.

This script converts TECHNICAL_REPORT.md into a clean PDF using reportlab.
It supports the markdown patterns used in this project:

- headings starting with #
- bullet points starting with -
- numbered lines like 1.
- regular paragraphs
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_MARKDOWN = PROJECT_ROOT / "TECHNICAL_REPORT.md"
OUTPUT_PDF = PROJECT_ROOT / "reports" / "technical_report.pdf"


def build_styles():
    """Create PDF styles for headings, body text, and lists."""

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        leading=28,
        spaceAfter=16,
        textColor=colors.HexColor("#1F3B5B"),
    )

    heading_1 = ParagraphStyle(
        "Heading1Custom",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        spaceBefore=14,
        spaceAfter=10,
        textColor=colors.HexColor("#1F3B5B"),
    )

    heading_2 = ParagraphStyle(
        "Heading2Custom",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        spaceBefore=10,
        spaceAfter=8,
        textColor=colors.HexColor("#244E7A"),
    )

    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=14,
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "BulletCustom",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=14,
        leftIndent=14,
        firstLineIndent=-8,
        spaceAfter=4,
    )

    return title_style, heading_1, heading_2, body_style, bullet_style


def escape_text(text: str) -> str:
    """Escape a few HTML-sensitive characters for reportlab Paragraph."""

    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def markdown_to_story(markdown_text: str):
    """Convert simple markdown lines into reportlab flowables."""

    title_style, heading_1, heading_2, body_style, bullet_style = build_styles()
    story = []

    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return

        combined_text = " ".join(line.strip() for line in paragraph_lines).strip()
        if combined_text:
            story.append(Paragraph(escape_text(combined_text), body_style))
        paragraph_lines.clear()

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            story.append(Spacer(1, 0.12 * cm))
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(escape_text(stripped[2:]), title_style))
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(escape_text(stripped[3:]), heading_1))
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(escape_text(stripped[4:]), heading_2))
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(f"• {escape_text(stripped[2:])}", bullet_style))
            continue

        if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == ".":
            flush_paragraph()
            story.append(Paragraph(escape_text(stripped), bullet_style))
            continue

        if stripped.startswith("```"):
            # Skip code fence markers to keep the PDF clean.
            flush_paragraph()
            continue

        paragraph_lines.append(stripped)

    flush_paragraph()
    return story


def main() -> None:
    """Generate the PDF file from the markdown source."""

    markdown_text = INPUT_MARKDOWN.read_text(encoding="utf-8")
    story = markdown_to_story(markdown_text)

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="Technical Report - LLM Monitoring System",
        author="OpenAI Codex",
    )
    document.build(story)

    print("PDF technical report generated successfully.")
    print(f"Saved to: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
