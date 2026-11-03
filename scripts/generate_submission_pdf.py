from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "SUBMISSION_DOCUMENT.md"
OUTPUT = ROOT / "submission" / "Artefact_AI_Engineer_Case.pdf"

def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    font = Path("C:/Windows/Fonts/arial.ttf")
    bold = Path("C:/Windows/Fonts/arialbd.ttf")
    if font.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("Arial", str(font)))
        pdfmetrics.registerFont(TTFont("Arial-Bold", str(bold)))
        body_font, bold_font = "Arial", "Arial-Bold"
    else:
        body_font, bold_font = "Helvetica", "Helvetica-Bold"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodyCase", parent=styles["BodyText"], fontName=body_font, fontSize=9.2, leading=12, spaceAfter=5))
    styles.add(ParagraphStyle(name="H1Case", parent=styles["Heading1"], fontName=bold_font, fontSize=17, leading=21, spaceAfter=10))
    styles.add(ParagraphStyle(name="H2Case", parent=styles["Heading2"], fontName=bold_font, fontSize=12, leading=15, spaceBefore=8, spaceAfter=5))
    styles.add(ParagraphStyle(name="CodeCase", parent=styles["Code"], fontName="Courier", fontSize=7.5, leading=9, leftIndent=8, spaceAfter=5))
    story = []
    in_code = False
    for raw in SOURCE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if not line:
            story.append(Spacer(1, 3)); continue
        if in_code:
            story.append(Paragraph(escape(raw), styles["CodeCase"])); continue
        if line.startswith("# "): story.append(Paragraph(escape(line[2:]), styles["H1Case"])); continue
        if line.startswith("## "): story.append(Paragraph(escape(line[3:]), styles["H2Case"])); continue
        if line.startswith("### "): story.append(Paragraph(escape(line[4:]), styles["H2Case"])); continue
        if line.startswith("- "): line = "• " + line[2:]
        line = escape(line).replace("`", "")
        story.append(Paragraph(line, styles["BodyCase"]))
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm, title="Artefact AI Engineer Case")
    doc.build(story)
    print(OUTPUT)

if __name__ == "__main__": main()
