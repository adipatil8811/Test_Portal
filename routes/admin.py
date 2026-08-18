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
