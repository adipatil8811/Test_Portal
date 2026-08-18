from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db
from models.test import Test
from models.response import Response
from utils.security import login_required

results_bp = Blueprint("results", __name__, url_prefix="/admin")

@results_bp.route("/tests/<test_id>/responses")
@login_required
def test_responses(test_id):
    """View all student submissions for a specific test"""
    test = Test.query.filter_by(test_id=test_id).first_or_404()
    search = request.args.get("search", "").strip()

    query = Response.query.filter_by(test_id=test_id).order_by(Response.submitted_at.desc())
    if search:
        query = query.filter(
            (Response.student_name.ilike(f"%{search}%")) |
            (Response.roll_number.ilike(f"%{search}%")) |
            (Response.student_email.ilike(f"%{search}%"))
        )

    responses = query.all()
    total_submissions = len(responses)
    avg_score = (sum(r.score for r in responses) / total_submissions) if total_submissions > 0 else 0.0
    passed_count = sum(1 for r in responses if r.passed)

    summary = {
        "totalSubmissions": total_submissions,
        "avgScore": round(avg_score, 1),
        "passedCount": passed_count,
        "passRate": round((passed_count / total_submissions) * 100, 1) if total_submissions > 0 else 0.0,
    }

    return render_template(
        "admin/responses.html",
        test=test,
        responses=responses,
        summary=summary,
        search=search,
    )

@results_bp.route("/tests/<test_id>/responses/<response_id>")
@login_required
def response_detail(test_id, response_id):
    """View detailed breakdown of an individual student's submission"""
    test = Test.query.filter_by(test_id=test_id).first_or_404()
    resp = Response.query.filter_by(test_id=test_id, response_id=response_id).first_or_404()

    return render_template(
        "admin/response_detail.html",
        test=test,
        response=resp,
        reviews=resp.evaluation,
    )
