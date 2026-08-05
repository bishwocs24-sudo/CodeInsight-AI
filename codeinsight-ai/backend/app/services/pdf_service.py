"""
Renders a stored Review as a downloadable PDF report.
"""
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.review import Review


def _bullets(items: list[str], style) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(item, style)) for item in items],
        bulletType="bullet",
    )


def build_review_pdf(review: Review) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["Normal"], spaceAfter=6)
    heading = ParagraphStyle("heading", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)

    story = [
        Paragraph("CodeInsight AI — Review Report", styles["Title"]),
        Paragraph(
            f"Language: {review.language} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Type: {review.review_type} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Generated: {review.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
            body,
        ),
        Spacer(1, 12),
    ]

    results = review.results or {}

    scores = results.get("scores")
    if scores:
        story.append(Paragraph("Scores", heading))
        rows = [["Metric", "Score"]] + [[k.replace("_", " ").title(), f"{v}/100"] for k, v in scores.items()]
        table = Table(rows, colWidths=[3 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e1b2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)

    if results.get("summary"):
        story.append(Paragraph("Summary", heading))
        story.append(Paragraph(results["summary"], body))

    for key, title in [
        ("strengths", "Strengths"),
        ("weaknesses", "Weaknesses"),
        ("code_smells", "Code Smells"),
        ("best_practices", "Best Practice Suggestions"),
        ("edge_cases", "Edge Cases to Consider"),
    ]:
        items = results.get(key)
        if items:
            story.append(Paragraph(title, heading))
            story.append(_bullets(items, body))

    bugs = results.get("bugs")
    if bugs:
        story.append(Paragraph("Bugs Found", heading))
        story.append(_bullets([f"[{b.get('severity', 'n/a').upper()}] {b.get('description', '')}" for b in bugs], body))

    security_issues = results.get("security_issues")
    if security_issues:
        story.append(Paragraph("Security Issues", heading))
        story.append(_bullets(
            [f"[{s.get('severity', 'n/a').upper()}] {s.get('title', '')} — {s.get('description', '')}" for s in security_issues],
            body,
        ))

    if results.get("explanation"):
        story.append(Paragraph("Explanation", heading))
        story.append(Paragraph(results["explanation"], body))

    if results.get("refactored_code"):
        story.append(Paragraph("Refactored Code", heading))
        story.append(Paragraph(
            f"<font face='Courier' size=8>{results['refactored_code'].replace(chr(10), '<br/>')}</font>",
            body,
        ))

    if results.get("unit_tests"):
        story.append(Paragraph("Generated Tests", heading))
        story.append(Paragraph(
            f"<font face='Courier' size=8>{results['unit_tests'].replace(chr(10), '<br/>')}</font>",
            body,
        ))

    doc.build(story)
    return buffer.getvalue()
