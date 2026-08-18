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
@student_bp.route("/api/test/<test_id>", methods=["GET"])
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
@student_bp.route("/api/test/<test_id>/submit", methods=["POST"])
def submit_test(test_id):
    """Authoritative server-side test evaluation and result storage"""
    test = Test.query.filter_by(test_id=test_id).first_or_404()
    is_preview = request.form.get("isPreview") == "true" and is_admin_authenticated()

    # Server-side validation of test availability
    if not test.published and not is_preview:
        return render_template(
            "student/test_unavailable.html",
            test=test,
            reason="This assessment is currently closed and not accepting submissions."
        )

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    if not is_preview and test.end_date and test.end_date < now_str:
        return render_template(
            "student/test_unavailable.html",
            test=test,
            reason="This assessment has ended and the submission window is closed."
        )

    student_name = request.form.get("studentName", "").strip()
    student_email = request.form.get("studentEmail", "").strip()
    student_class = request.form.get("studentClass", "").strip()
    student_division = request.form.get("studentDivision", "").strip()
    roll_number = request.form.get("rollNumber", "").strip()

    # Validate required fields
    if not student_name and (test.require_name or True):
        flash("Student Name is required.", "danger")
        return redirect(url_for("student.take_test", test_id=test_id))

    if test.require_roll_number and not roll_number:
        flash("Roll Number is required.", "danger")
        return redirect(url_for("student.take_test", test_id=test_id))

    if test.collect_email and not student_email:
        flash("Email address is required.", "danger")
        return redirect(url_for("student.take_test", test_id=test_id))

    # Single-submission constraint check
    if not test.allow_multiple and not is_preview:
        existing_query = Response.query.filter_by(test_id=test_id)
        if roll_number:
            existing = existing_query.filter_by(roll_number=roll_number).first()
        elif student_email:
            existing = existing_query.filter_by(student_email=student_email).first()
        else:
            existing = existing_query.filter_by(student_name=student_name).first()

        if existing:
            return render_template(
                "student/test_unavailable.html",
                test=test,
                reason="You have already submitted this assessment. Multiple submissions are not allowed."
            )

    # Parse student submitted answers
    answers = {}
    for q in test.questions:
        if q.question_type == "multiple-correct":
            vals = request.form.getlist(f"answer_{q.question_id}")
            answers[q.question_id] = vals
        else:
            val = request.form.get(f"answer_{q.question_id}", "").strip()
            answers[q.question_id] = val

    # Server-side authoritative evaluation
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
            institute_name=test.institute_name or "GVT",
            institute_logo=test.institute_logo,
            teacher_signature=test.teacher_signature,
            teacher_signer_title=test.teacher_signer_title or "Authorized Instructor",
            certificate_template=test.certificate_template or "classic",
            certificate_title=test.certificate_title or "Certificate of Achievement",
            certificate_description=test.certificate_description or "",
            show_score=test.show_score_on_cert,
            show_percentage=test.show_percentage_on_cert,
            show_certificate_id=test.show_cert_id,
            show_issue_date=test.show_issue_date,
            show_qr_code=test.show_qr_code,
        )
        db.session.add(cert_obj)

    # Save student response record
    if not is_preview:
        response_record = Response(
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
            certificate_status="Issued" if cert_obj else "Not Eligible",
            certificate_id=cert_id,
        )
        db.session.add(response_record)
        db.session.commit()

    verify_url = get_certificate_verify_url(cert_id) if cert_id else ""

    return render_template(
        "student/result.html",
        test=test,
        result=eval_result,
        student_name=student_name,
        certificate_id=cert_id,
        certificate=cert_obj,
        verify_url=verify_url,
        is_preview=is_preview,
    )

@student_bp.route("/student/certificates", methods=["GET"], endpoint="my_certificates")
@student_bp.route("/api/student/certificates", methods=["GET"], endpoint="student_certificates")
def my_certificates():
    """Search and lookup student certificates by roll number or email"""
    query = request.args.get("q", "").strip()
    certificates = []
    
    if query:
        # Search by student name, roll number, email, or certificate ID
        matching_responses = Response.query.filter(
            (Response.student_name.ilike(f"%{query}%")) |
            (Response.roll_number.ilike(f"%{query}%")) |
            (Response.student_email.ilike(f"%{query}%")) |
            (Response.certificate_id.ilike(f"%{query}%"))
        ).all()

        cert_ids = [r.certificate_id for r in matching_responses if r.certificate_id]
        if cert_ids:
            certificates = Certificate.query.filter(Certificate.certificate_id.in_(cert_ids)).all()
        else:
            certificates = Certificate.query.filter(
                (Certificate.certificate_id.ilike(f"%{query}%")) |
                (Certificate.student_name.ilike(f"%{query}%"))
            ).all()

    return render_template(
        "student/my_certificates.html",
        certificates=certificates,
        search_query=query,
    )
