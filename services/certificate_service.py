import io
import qrcode
from PIL import Image
from reportlab.lib import pagesizes, colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def generate_qr_image(data_text, size_px=150):
    """Generate in-memory QR code PIL image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(data_text)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")

def get_theme_colors(theme_name):
    """Map theme name to ReportLab color palette"""
    theme = (theme_name or "classic").lower()
    if theme == "academic":
        return {
            "primary": colors.HexColor("#064e3b"),     # Emerald 900
            "secondary": colors.HexColor("#047857"),   # Emerald 700
            "accent": colors.HexColor("#d97706"),      # Amber Gold
            "border": colors.HexColor("#064e3b"),
            "inner_border": colors.HexColor("#059669"),
            "bg_tint": colors.HexColor("#f0fdf4"),
            "text_dark": colors.HexColor("#064e3b"),
            "seal": colors.HexColor("#047857"),
        }
    elif theme == "modern":
        return {
            "primary": colors.HexColor("#0f172a"),     # Slate 900
            "secondary": colors.HexColor("#4338ca"),   # Indigo 700
            "accent": colors.HexColor("#6366f1"),      # Indigo 500
            "border": colors.HexColor("#1e293b"),
            "inner_border": colors.HexColor("#4f46e5"),
            "bg_tint": colors.HexColor("#f8fafc"),
            "text_dark": colors.HexColor("#0f172a"),
            "seal": colors.HexColor("#4338ca"),
        }
    elif theme == "gold":
        return {
            "primary": colors.HexColor("#78350f"),     # Amber 900
            "secondary": colors.HexColor("#b45309"),   # Amber 700
            "accent": colors.HexColor("#d97706"),      # Gold 600
            "border": colors.HexColor("#92400e"),
            "inner_border": colors.HexColor("#d97706"),
            "bg_tint": colors.HexColor("#fffbeb"),
            "text_dark": colors.HexColor("#451a03"),
            "seal": colors.HexColor("#d97706"),
        }
    else:  # classic
        return {
            "primary": colors.HexColor("#1e1b4b"),     # Indigo 950
            "secondary": colors.HexColor("#3730a3"),   # Indigo 800
            "accent": colors.HexColor("#d97706"),      # Amber 600
            "border": colors.HexColor("#1e1b4b"),
            "inner_border": colors.HexColor("#b45309"),
            "bg_tint": colors.HexColor("#f8fafc"),
            "text_dark": colors.HexColor("#1e1b4b"),
            "seal": colors.HexColor("#d97706"),
        }

def generate_certificate_pdf(cert_data, verify_url=""):
    """
    Generate a high-resolution A4 landscape certificate PDF using ReportLab.
    
    :param cert_data: Dict or Certificate model object containing certificate attributes
    :param verify_url: Fully qualified URL for the public verification QR code
    :return: bytes of PDF file
    """
    buffer = io.BytesIO()
    page_width, page_height = pagesizes.landscape(pagesizes.A4)
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    c.setTitle(f"Certificate - {cert_data.get('studentName', 'Student')}")
    c.setAuthor(cert_data.get("instituteName", "GVT"))

    theme_colors = get_theme_colors(cert_data.get("certificateTemplate", "classic"))

    # 1. Background Fill
    c.setFillColor(theme_colors["bg_tint"])
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # 2. Outer Heavy Ornate Border
    margin = 24
    c.setStrokeColor(theme_colors["border"])
    c.setLineWidth(4)
    c.rect(margin, margin, page_width - (2 * margin), page_height - (2 * margin), fill=0, stroke=1)

    # 3. Inner Fine Border
    inner_margin = 32
    c.setStrokeColor(theme_colors["inner_border"])
    c.setLineWidth(1.5)
    c.rect(inner_margin, inner_margin, page_width - (2 * inner_margin), page_height - (2 * inner_margin), fill=0, stroke=1)

    # 4. Corner Decorative Accents
    corner_size = 14
    for cx, cy, sx, sy in [
        (inner_margin + 4, page_height - inner_margin - 4, 1, -1),
        (page_width - inner_margin - 4, page_height - inner_margin - 4, -1, -1),
        (inner_margin + 4, inner_margin + 4, 1, 1),
        (page_width - inner_margin - 4, inner_margin + 4, -1, 1),
    ]:
        c.setStrokeColor(theme_colors["accent"])
        c.setLineWidth(2)
        c.line(cx, cy, cx + (sx * corner_size), cy)
        c.line(cx, cy, cx, cy + (sy * corner_size))

    # 5. Header: Institute Name
    inst_name = (cert_data.get("instituteName") or "GVT").upper()
    c.setFillColor(theme_colors["secondary"])
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(page_width / 2.0, page_height - 68, inst_name)

    # 6. Main Title: Certificate Title
    cert_title = (cert_data.get("certificateTitle") or "CERTIFICATE OF ACHIEVEMENT").upper()
    c.setFillColor(theme_colors["primary"])
    c.setFont("Times-Bold", 26)
    c.drawCentredString(page_width / 2.0, page_height - 105, cert_title)

    # Small gold accent line under title
    c.setStrokeColor(theme_colors["accent"])
    c.setLineWidth(1.5)
    c.line((page_width / 2.0) - 120, page_height - 114, (page_width / 2.0) + 120, page_height - 114)

    # 7. Presentation Subtitle
    c.setFillColor(colors.HexColor("#4b5563"))
    c.setFont("Times-Italic", 13)
    c.drawCentredString(page_width / 2.0, page_height - 146, "This is proudly presented to")

    # 8. Student Name (Large & Elegant)
    student_name = cert_data.get("studentName") or "Student Name"
    c.setFillColor(theme_colors["primary"])
    c.setFont("Times-Bold", 28)
    c.drawCentredString(page_width / 2.0, page_height - 190, student_name)

    # Decorative Underline for Name
    name_width = min(400, max(240, len(student_name) * 16))
    c.setStrokeColor(theme_colors["accent"])
    c.setLineWidth(1.5)
    c.line((page_width / 2.0) - (name_width / 2.0), page_height - 200, (page_width / 2.0) + (name_width / 2.0), page_height - 200)

    # 9. Description / Body Text
    test_title = cert_data.get("testTitle") or "Assessment Test"
    score_val = str(cert_data.get("score", 0))
    total_val = str(cert_data.get("totalMarks", 0))
    pct_val = str(cert_data.get("percentage", "0.0"))
    date_val = cert_data.get("date") or ""
    cert_id = cert_data.get("certificateId") or ""

    raw_desc = cert_data.get("certificateDescription") or (
        "For successfully completing the {{TEST_NAME}} assessment with a score of {{SCORE}}/{{TOTAL_MARKS}} ({{PERCENTAGE}}%)."
    )
    desc_text = (
        raw_desc
        .replace("{{STUDENT_NAME}}", student_name)
        .replace("{{TEST_NAME}}", test_title)
        .replace("{{SCORE}}", score_val)
        .replace("{{TOTAL_MARKS}}", total_val)
        .replace("{{PERCENTAGE}}", pct_val)
        .replace("{{DATE}}", date_val)
        .replace("{{CERTIFICATE_ID}}", cert_id)
    )

    styles = getSampleStyleSheet()
    desc_style = ParagraphStyle(
        name="CertDesc",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#374151"),
    )

    p = Paragraph(desc_text, desc_style)
    p_width = 540
    p_height = 40
    p.wrapOn(c, p_width, p_height)
    p.drawOn(c, (page_width - p_width) / 2.0, page_height - 255)

    # 10. Score & Grade Pill Badge
    show_score = cert_data.get("showScore", True)
    show_pct = cert_data.get("showPercentage", True)
    if show_score or show_pct:
        score_text = []
        if show_score:
            score_text.append(f"Score: {score_val} / {total_val}")
        if show_pct:
            score_text.append(f"Percentage: {pct_val}%")
        badge_str = "   •   ".join(score_text)

        badge_y = page_height - 288
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor("#cbd5e1"))
        c.setLineWidth(1)
        c.roundRect((page_width / 2.0) - 140, badge_y - 6, 280, 22, 10, fill=1, stroke=1)

        c.setFillColor(theme_colors["primary"])
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(page_width / 2.0, badge_y, badge_str)

    # 11. Bottom Separator Line
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.setLineWidth(1)
    c.line(margin + 30, 115, page_width - margin - 30, 115)

    # 12. Bottom Left: Date & Certificate ID
    show_date = cert_data.get("showIssueDate", True)
    show_id = cert_data.get("showCertificateId", True)

    c.setFillColor(colors.HexColor("#64748b"))
    c.setFont("Helvetica-Bold", 8)
    if show_date:
        c.drawString(inner_margin + 20, 95, "ISSUE DATE")
        c.setFillColor(colors.HexColor("#1e293b"))
        c.setFont("Helvetica", 10)
        c.drawString(inner_margin + 20, 80, date_val)

    if show_id:
        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(inner_margin + 20, 62, "CERTIFICATE ID")
        c.setFillColor(theme_colors["secondary"])
        c.setFont("Courier-Bold", 10)
        c.drawString(inner_margin + 20, 48, cert_id)

    # 13. Center: Gold Official Seal
    seal_cx = page_width / 2.0
    seal_cy = 76
    c.setFillColor(theme_colors["seal"])
    c.circle(seal_cx, seal_cy, 26, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#fef3c7"))
    c.setLineWidth(1.5)
    c.circle(seal_cx, seal_cy, 22, fill=0, stroke=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(seal_cx, seal_cy - 3, "VERIFIED")

    # 14. Bottom Right: Instructor Signature & QR Code
    signer_title = cert_data.get("teacherSignerTitle") or "Authorized Instructor"
    sig_x = page_width - inner_margin - 170

    # Signature line
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.setLineWidth(1)
    c.line(sig_x, 70, sig_x + 110, 70)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.setFont("Times-Italic", 12)
    c.drawCentredString(sig_x + 55, 75, inst_name)
    c.setFillColor(colors.HexColor("#64748b"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(sig_x + 55, 58, signer_title)

    # Verification QR Code
    show_qr = cert_data.get("showQrCode", True)
    if show_qr and verify_url:
        try:
            qr_img = generate_qr_image(verify_url, size_px=120)
            c.drawInlineImage(qr_img, page_width - inner_margin - 48, 44, width=42, height=42)
            c.setFillColor(colors.HexColor("#94a3b8"))
            c.setFont("Helvetica", 6)
            c.drawCentredString(page_width - inner_margin - 27, 36, "SCAN TO VERIFY")
        except Exception:
            pass

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.getvalue()
