import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db
from models.test import Test
from models.question import Question
from models.response import Response
from models.certificate import Certificate
from utils.security import login_required
from utils.helpers import generate_test_id, generate_question_id
from services.link_service import get_test_share_url, get_whatsapp_share_url

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("")
@admin_bp.route("/")
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    """Teacher / Admin Dashboard Overview"""
    tests = Test.query.order_by(Test.created_at.desc()).all()
    
    total_tests = len(tests)
    published_tests = sum(1 for t in tests if t.published)
    draft_tests = total_tests - published_tests
    total_responses = Response.query.count()
    total_certificates = Certificate.query.filter_by(is_revoked=False).count()

    stats = {
        "totalTests": total_tests,
        "publishedTests": published_tests,
        "draftTests": draft_tests,
        "totalResponses": total_responses,
        "totalCertificates": total_certificates,
    }

    test_cards = []
    for t in tests:
        test_cards.append({
            "test": t,
            "shareUrl": get_test_share_url(t.test_id),
            "questionCount": len(t.questions),
            "responseCount": t.responses.count(),
        })

    return render_template("admin/dashboard.html", stats=stats, test_cards=test_cards)

@admin_bp.route("/tests/new")
@login_required
def create_test():
    """Render Test Builder in creation mode"""
    new_test_id = generate_test_id()
    return render_template("admin/test_builder.html", test=None, new_test_id=new_test_id, is_new=True)

@admin_bp.route("/tests/<test_id>")
@login_required
def edit_test(test_id):
    """Render Test Builder in edit mode"""
    test = Test.query.filter_by(test_id=test_id).first_or_404()
    return render_template("admin/test_builder.html", test=test, new_test_id=test.test_id, is_new=False)

@admin_bp.route("/api/tests/save", methods=["POST"])
@login_required
def save_test():
    """AJAX endpoint to save or update test and its questions"""
    data = request.get_json() or {}
    test_id = data.get("testId") or generate_test_id()

    test = Test.query.filter_by(test_id=test_id).first()
    if not test:
        test = Test(test_id=test_id)
        db.session.add(test)

    # Core Test Details
    test.title = data.get("title", "").strip() or "Untitled Test"
    test.description = data.get("description", "").strip()
    test.subject = data.get("subject", "").strip()
    test.class_name = data.get("class", "").strip()
    test.division = data.get("division", "").strip()
    test.duration = int(data.get("duration") or 0)
    
    # Settings
    settings = data.get("settings") or {}
    test.show_result = bool(settings.get("showResult", True))
    test.collect_email = bool(settings.get("collectEmail", False))
    test.require_name = bool(settings.get("requireName", True))
    test.require_class = bool(settings.get("requireClass", True))
    test.require_division = bool(settings.get("requireDivision", False))
    test.require_roll_number = bool(settings.get("requireRollNumber", True))
    test.allow_multiple = bool(settings.get("allowMultiple", False))
    test.shuffle_questions = bool(settings.get("shuffleQuestions", False))
    test.shuffle_options = bool(settings.get("shuffleOptions", False))
    
    # Scheduling
    test.start_date = settings.get("startDate", "") or ""
    test.end_date = settings.get("endDate", "") or ""

    # Certificate Configuration
    test.enable_certificate = bool(settings.get("enableCertificate", True))
    test.certificate_min_percentage = int(settings.get("certificateMinPercentage", 40) or 40)
    test.institute_name = settings.get("instituteName", "").strip()
    test.institute_logo = settings.get("instituteLogo", "").strip()
    test.teacher_signature = settings.get("teacherSignature", "").strip()
    test.teacher_signer_title = settings.get("teacherSignerTitle", "Authorized Instructor").strip()
    test.certificate_template = settings.get("certificateTemplate", "classic")
    test.certificate_title = settings.get("certificateTitle", "Certificate of Achievement").strip()
    test.certificate_description = settings.get("certificateDescription", "").strip()
    test.show_score_on_cert = bool(settings.get("showScoreOnCertificate", True))
    test.show_percentage_on_cert = bool(settings.get("showPercentageOnCertificate", True))
    test.show_cert_id = bool(settings.get("showCertificateId", True))
    test.show_issue_date = bool(settings.get("showIssueDate", True))
    test.show_qr_code = bool(settings.get("showQrCode", True))
    test.email_certificate = bool(settings.get("emailCertificate", False))

    # Questions Sync (Replace or Update)
    raw_questions = data.get("questions") or []
    
    # Delete existing questions to maintain order
    Question.query.filter_by(test_id=test_id).delete()

    total_marks = 0
    for idx, q_data in enumerate(raw_questions):
        q_id = q_data.get("id") or generate_question_id()
        q_marks = int(q_data.get("marks") or 1)
        total_marks += q_marks

        opts = q_data.get("options") or []
        corr_answers = q_data.get("correctAnswers") or []

        q = Question(
            question_id=q_id,
            test_id=test_id,
            question_text=q_data.get("question", "").strip(),
            question_type=q_data.get("type", "multiple-choice"),
            options_json=json.dumps(opts),
            correct_answer=str(q_data.get("correctAnswer") or "").strip(),
            correct_answers_json=json.dumps(corr_answers),
            marks=q_marks,
            required=bool(q_data.get("required", True)),
            explanation=q_data.get("explanation", "").strip(),
            order_index=idx,
        )
        db.session.add(q)

    test.total_marks = total_marks
    db.session.commit()

    return jsonify({
        "success": True,
        "testId": test.test_id,
        "shareUrl": get_test_share_url(test.test_id),
        "message": "Test saved successfully as draft.",
    })

@admin_bp.route("/tests/<test_id>/publish", methods=["POST"])
@login_required
def toggle_publish(test_id):
    """Publish or unpublish a test with validation"""
    test = Test.query.filter_by(test_id=test_id).first_or_404()
    target_status = request.form.get("published") == "true" or request.json and request.json.get("published")

    if target_status:
        # Validate test before publishing
        if not test.title.strip():
            return jsonify({"success": False, "error": "Please provide a Test Title before publishing."}), 400
        if not test.questions:
            return jsonify({"success": False, "error": "Please add at least one question before publishing."}), 400
        
        for idx, q in enumerate(test.questions):
            if not q.question_text.strip():
                return jsonify({"success": False, "error": f"Question {idx + 1} is missing question text."}), 400
            if q.question_type in ("multiple-choice", "true-false") and not q.correct_answer.strip():
                return jsonify({"success": False, "error": f"Question {idx + 1} does not have a correct answer selected."}), 400
            if q.question_type == "multiple-correct" and not q.correct_answers:
                return jsonify({"success": False, "error": f"Question {idx + 1} must have at least one correct answer checked."}), 400

    test.published = bool(target_status)
    db.session.commit()

    if request.is_json:
        return jsonify({
            "success": True,
            "published": test.published,
            "shareUrl": get_test_share_url(test.test_id),
            "message": "Test published and active!" if test.published else "Test unpublished (disabled).",
        })

    flash("Test published and live for students!" if test.published else "Test unpublished.", "success" if test.published else "info")
    return redirect(request.referrer or url_for("admin.dashboard"))

@admin_bp.route("/tests/<test_id>/duplicate", methods=["POST"])
@login_required
def duplicate_test(test_id):
    """Duplicate an existing test with its questions"""
    original = Test.query.filter_by(test_id=test_id).first_or_404()
    new_id = generate_test_id()

    dup = Test(
        test_id=new_id,
        title=f"{original.title} (Copy)",
        description=original.description,
        subject=original.subject,
        class_name=original.class_name,
        division=original.division,
        duration=original.duration,
        total_marks=original.total_marks,
        published=False,  # Duplicate starts as Draft
        start_date=original.start_date,
        end_date=original.end_date,
        show_result=original.show_result,
        collect_email=original.collect_email,
        require_name=original.require_name,
        require_class=original.require_class,
        require_division=original.require_division,
        require_roll_number=original.require_roll_number,
        allow_multiple=original.allow_multiple,
        shuffle_questions=original.shuffle_questions,
        shuffle_options=original.shuffle_options,
        enable_certificate=original.enable_certificate,
        certificate_min_percentage=original.certificate_min_percentage,
        institute_name=original.institute_name,
        institute_logo=original.institute_logo,
        teacher_signature=original.teacher_signature,
        teacher_signer_title=original.teacher_signer_title,
        certificate_template=original.certificate_template,
        certificate_title=original.certificate_title,
        certificate_description=original.certificate_description,
    )
    db.session.add(dup)

    for q in original.questions:
        dup_q = Question(
            question_id=generate_question_id(),
            test_id=new_id,
            question_text=q.question_text,
            question_type=q.question_type,
            options_json=q.options_json,
            correct_answer=q.correct_answer,
            correct_answers_json=q.correct_answers_json,
            marks=q.marks,
            required=q.required,
            explanation=q.explanation,
            order_index=q.order_index,
        )
        db.session.add(dup_q)

    db.session.commit()
    flash(f"Test duplicated successfully as '{dup.title}'!", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/tests/<test_id>/delete", methods=["POST"])
@login_required
def delete_test(test_id):
    """Delete a test and all its questions and responses"""
    test = Test.query.filter_by(test_id=test_id).first_or_404()
    title = test.title
    db.session.delete(test)
    db.session.commit()
    flash(f"Test '{title}' has been deleted.", "info")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/api/share-info/<test_id>")
@login_required
def share_info(test_id):
    """Return JSON share metadata for modal"""
    test = Test.query.filter_by(test_id=test_id).first_or_404()
    return jsonify({
        "testId": test.test_id,
        "title": test.title,
        "published": test.published,
        "shareUrl": get_test_share_url(test.test_id),
        "whatsappUrl": get_whatsapp_share_url(test.title, test.test_id),
    })

@admin_bp.route("/question-paper/<test_id>")
@login_required
def question_paper(test_id):
    """Render printable question paper HTML view"""
    test = Test.query.filter_by(test_id=test_id).first_or_404()
    return render_template("admin/question_paper.html", test=test)

@admin_bp.route("/question-paper/<test_id>/pdf")
@login_required
def question_paper_pdf(test_id):
    """Generate and stream a downloadable PDF question paper for Android"""
    import re as _re
    from flask import Response as FlaskResponse
    from io import BytesIO

    test = Test.query.filter_by(test_id=test_id).first_or_404()
    buffer = BytesIO()


    # Use ReportLab if available, otherwise generate plain-text PDF via minimal approach
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib import colors

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm, leftMargin=20*mm,
            topMargin=20*mm, bottomMargin=20*mm,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle("title", parent=styles["Heading1"],
            fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)
        meta_style = ParagraphStyle("meta", parent=styles["Normal"],
            fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor("#64748b"), spaceAfter=12)
        q_style = ParagraphStyle("q", parent=styles["Normal"],
            fontSize=11, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=14)
        opt_style = ParagraphStyle("opt", parent=styles["Normal"],
            fontSize=10.5, leftIndent=16, spaceAfter=2)
        ans_style = ParagraphStyle("ans", parent=styles["Normal"],
            fontSize=9, textColor=colors.HexColor("#475569"), leftIndent=16, spaceAfter=6)

        story = []
        story.append(Paragraph(test.title, title_style))

        meta_parts = []
        if test.subject: meta_parts.append(f"Subject: {test.subject}")
        if test.class_name: meta_parts.append(f"Class: {test.class_name}")
        if test.duration and test.duration > 0: meta_parts.append(f"Duration: {test.duration} mins")
        meta_parts.append(f"Total Marks: {test.total_marks}")
        story.append(Paragraph("   |   ".join(meta_parts), meta_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=10))

        if test.description:
            inst_style = ParagraphStyle("inst", parent=styles["Normal"],
                fontSize=9.5, textColor=colors.HexColor("#475569"),
                borderPad=6, spaceAfter=12,
                backColor=colors.HexColor("#f8fafc"), borderColor=colors.HexColor("#e2e8f0"),
                borderWidth=1, borderRadius=4)
            story.append(Paragraph(f"<b>Instructions:</b> {test.description}", inst_style))

        for idx, q in enumerate(test.questions):
            q_text = f"Q{idx+1}.  {q.question_text}  [{q.marks} {'mark' if q.marks == 1 else 'marks'}]"
            story.append(Paragraph(q_text, q_style))

            if q.question_type in ("multiple-choice", "multiple-correct"):
                labels = ["(A)", "(B)", "(C)", "(D)", "(E)", "(F)"]
                for oi, opt in enumerate(q.options):
                    if opt:
                        label = labels[oi] if oi < len(labels) else f"({oi+1})"
                        story.append(Paragraph(f"{label} {opt}", opt_style))
            elif q.question_type == "true-false":
                story.append(Paragraph("(A) True       (B) False", opt_style))
            elif q.question_type in ("short-answer",):
                story.append(Paragraph("Answer: _______________________________________________", opt_style))
            elif q.question_type == "paragraph":
                for _ in range(3):
                    story.append(Paragraph("___________________________________________________________________", opt_style))

        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
        story.append(Paragraph("— End of Question Paper —", meta_style))

        doc.build(story)

    except Exception as e:
        # Fallback: minimal PDF if ReportLab not available
        buffer.write(b"%PDF-1.4\n1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj\n"
                     b"2 0 obj<</Type /Pages /Kids[3 0 R] /Count 1>>endobj\n"
                     b"3 0 obj<</Type /Page /Parent 2 0 R /MediaBox[0 0 595 842]>>endobj\n"
                     b"xref\n0 4\n0000000000 65535 f\ntrailer<</Size 4 /Root 1 0 R>>\n%%EOF")

    pdf_bytes = buffer.getvalue()
    clean_title = _re.sub(r"[^a-zA-Z0-9_-]", "_", test.title.strip())
    filename = f"QuestionPaper_{clean_title}.pdf"

    return FlaskResponse(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/pdf",
        }
    )

