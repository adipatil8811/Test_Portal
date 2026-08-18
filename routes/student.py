import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from models import db
from models.test import Test
from models.question import Question
from models.response import Response
from models.certificate import Certificate
from services.evaluation_service import evaluate_test_submission
from utils.helpers import generate_response_id, generate_certificate_id, format_date
from utils.security import is_admin_authenticated
from services.link_service import get_certificate_verify_url

student_bp = Blueprint("student", __name__)

@student_bp.route("/test/<test_id>", methods=["GET"])
def take_test(test_id):
    """Student test registration & live question runner"""
    test = Test.query.filter_by(test_id=test_id).first_or_404()
    is_preview = request.args.get("preview") == "true" and is_admin_authenticated()

    # If test is unpublished and not teacher preview, show unavailable
    if not test.published and not is_preview:
        return render_template(
            "student/test_unavailable.html",
            test=test,
            reason="This test is currently closed or unpublished by the instructor."
        )

    # Check Date Scheduling
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    if not is_preview:
        if test.start_date and test.start_date > now_str:
            return render_template(
                "student/test_unavailable.html",
                test=test,
                reason=f"This assessment has not started yet. It will open on {test.start_date.replace('T', ' ')}."
            )
        if test.end_date and test.end_date < now_str:
            return render_template(
                "student/test_unavailable.html",
                test=test,
                reason="This assessment has ended and is no longer accepting submissions."
            )

    return render_template(
        "student/test_taking.html",
        test=test,
        is_preview=is_preview,
    )

@student_bp.route("/test/<test_id>/submit", methods=["POST"])
def submit_test(test_id):
    """Authoritative server-side test evaluation and result storage"""
    test = Test.query.filter_by(test_id=test_id).first_or_404()
    is_preview = request.form.get("isPreview") == "true" and is_admin_authenticated()

    student_name = request.form.get("studentName", "").strip() or "Student"
    student_email = request.form.get("studentEmail", "").strip()
    student_class = request.form.get("studentClass", "").strip()
    student_division = request.form.get("studentDivision", "").strip()
    roll_number = request.form.get("rollNumber", "").strip()

    # Parse student submitted answers
    answers = {}
    for q in test.questions:
        if q.question_type == "multiple-correct":
            # Multiple checkboxes
            vals = request.form.getlist(f"answer_{q.question_id}")
            answers[q.question_id] = vals
        else:
            val = request.form.get(f"answer_{q.question_id}", "").strip()
            answers[q.question_id] = val

    # Evaluate answers on the server
    eval_result = evaluate_test_submission(test, answers)
    response_id = generate_response_id()

    cert_obj = None
    cert_id = None

    # If eligible for certificate and certificate is enabled
    if test.enable_certificate and eval_result["passed"] and not is_preview:
        cert_id = generate_certificate_id()
        cert_obj = Certificate(
            certificate_id=cert_id,
            response_id=response_id,
            test_id=test.test_id,
            student_name=student_name,
            student_email=student_email,
            test_title=test.title,
            score=eval_result["score"],
            total_marks=eval_result["totalMarks"],
            percentage=eval_result["percentage"],
            institute_name=test.institute_name or "Online Test Academy",
            institute_logo=test.institute_logo,
            teacher_signature=test.teacher_signature,
            teacher_signer_title=test.teacher_signer_title or "Authorized Instructor",
            certificate_template=test.certificate_template or "classic",
            certificate_title=test.certificate_title or "Certificate of Achievement",
            certificate_description=test.certificate_description,
            show_score=test.show_score_on_cert,
            show_percentage=test.show_percentage_on_cert,
            show_certificate_id=test.show_cert_id,
            show_issue_date=test.show_issue_date,
            show_qr_code=test.show_qr_code,
        )
        db.session.add(cert_obj)

    if not is_preview:
        resp = Response(
            response_id=response_id,
            test_id=test.test_id,
            test_title=test.title,
            student_name=student_name,
            student_email=student_email,
            student_class=student_class,
            student_division=student_division,
            roll_number=roll_number,
            score=eval_result["score"],
            total_marks=eval_result["totalMarks"],
            percentage=eval_result["percentage"],
            passed=eval_result["passed"],
            correct_count=eval_result["correctCount"],
            incorrect_count=eval_result["incorrectCount"],
            unanswered_count=eval_result["unansweredCount"],
            total_questions=eval_result["totalQuestions"],
            answers_json=json.dumps(answers),
            evaluation_json=json.dumps(eval_result["questionReviews"]),
            certificate_status="Generated" if cert_id else "Not Eligible",
            certificate_id=cert_id,
        )
        db.session.add(resp)
        db.session.commit()

    return render_template(
        "student/result.html",
        test=test,
        student_name=student_name,
        result=eval_result,
        certificate=cert_obj,
        response_id=response_id,
        is_preview=is_preview,
        verify_url=get_certificate_verify_url(cert_id) if cert_id else "",
    )

@student_bp.route("/student/certificates")
def my_certificates():
    """Student portal for looking up certificates"""
    lookup_id = request.args.get("id", "").strip()
    cert = None
    if lookup_id:
        cert = Certificate.query.filter_by(certificate_id=lookup_id, is_revoked=False).first()
    return render_template("student/my_certificates.html", cert=cert, lookup_id=lookup_id)
