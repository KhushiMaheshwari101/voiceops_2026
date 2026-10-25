import os
import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

BASE_DIR = Path(__file__).resolve().parent
REPORT_MD = BASE_DIR / "report.md"
REPORT_PDF = BASE_DIR / "report.pdf"


def md_to_xml(text: str) -> str:
    """Safely convert markdown inline formatting to reportlab XML tags."""
    # Escape XML entities first
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold **text** -> <b>text</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # Italics *text* -> <i>text</i>
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    # Inline code `code` -> <font face="Courier">code</font>
    text = re.sub(r"`(.*?)`", r'<font face="Courier">\1</font>', text)
    return text


def build_pdf():
    doc = SimpleDocTemplate(
        str(REPORT_PDF),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
    )
    h1_style = ParagraphStyle(
        "ReportH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=8,
        spaceAfter=3,
    )
    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=5,
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "ReportBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#2D3748"),
        leftIndent=12,
        spaceAfter=2,
    )

    story = []

    # Title & Header
    story.append(Paragraph("VoiceOps 2026: ZentroMart AI Customer Support Voice Agent", title_style))
    story.append(Spacer(1, 3))
    story.append(
        Paragraph(
            "<b>LLM &amp; Generative AI Capstone Technical Report</b> · Consulting &amp; Analytics Club, IIT Guwahati &times; Gnani.ai<br/>"
            "<b>Simulation Reference Date:</b> 20 October 2026 | <b>Public GitHub:</b> <font color='#2B6CB0'>https://github.com/KhushiMaheshwari101/voiceops_2026</font>",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=8))

    with open(REPORT_MD, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_table = False
    table_data = []

    for line in lines:
        line_str = line.strip()
        if not line_str:
            if not in_table:
                story.append(Spacer(1, 2))
            continue

        # Skip main header lines already rendered
        if line_str.startswith("# VoiceOps 2026") or line_str.startswith("## Capstone"):
            continue
        if line_str.startswith("**Course**") or line_str.startswith("**Simulation"):
            continue
        if line_str == "---":
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceBefore=4, spaceAfter=4))
            continue

        # Table parsing
        if line_str.startswith("|"):
            parts = [p.strip() for p in line_str.split("|")[1:-1]]
            if all(set(p) <= {"-", ":", " "} for p in parts):
                continue  # separator
            in_table = True
            is_header = len(table_data) == 0
            row_cells = []
            for p in parts:
                formatted = md_to_xml(p)
                if is_header:
                    formatted = f"<b>{formatted}</b>"
                row_cells.append(Paragraph(formatted, body_style))
            table_data.append(row_cells)
            continue
        elif in_table:
            # End of table
            t = Table(table_data, colWidths=[150, 110, 140, 100])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EBF8FF")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(t)
            story.append(Spacer(1, 4))
            table_data = []
            in_table = False

        if line_str.startswith("### "):
            story.append(Paragraph(md_to_xml(line_str.replace("### ", "")), h1_style))
        elif line_str.startswith("#### "):
            story.append(Paragraph(md_to_xml(line_str.replace("#### ", "")), h2_style))
        elif line_str.startswith("- ") or line_str.startswith("* "):
            content = md_to_xml(line_str[2:])
            story.append(Paragraph(f"&bull; {content}", bullet_style))
        elif line_str.startswith("> "):
            quote_text = md_to_xml(line_str[2:])
            quote_style = ParagraphStyle(
                "Quote",
                parent=body_style,
                fontName="Helvetica-Oblique",
                leftIndent=12,
                textColor=colors.HexColor("#4A5568"),
            )
            story.append(Paragraph(quote_text, quote_style))
        else:
            p_text = md_to_xml(line_str)
            story.append(Paragraph(p_text, body_style))

    doc.build(story)
    print(f"Report PDF generated successfully at: {REPORT_PDF}")


if __name__ == "__main__":
    build_pdf()
