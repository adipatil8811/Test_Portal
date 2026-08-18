import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify
from models import db
from models.certificate import Certificate
from services.certificate_service import generate_certificate_pdf
from services.link_service import get_certificate_verify_url
from utils.security import login_required

certificates_bp = Blueprint("certificates", __name__)

@certificates_bp.route("/certificate/<certificate_id>")
def view_certificate(certificate_id):
    """Render dedicated web certificate viewer"""
    cert = Certificate.query.filter_by(certificate_id=certificate_id).first_or_404()
    verify_url = get_certificate_verify_url(cert.certificate_id)
    return render_template("certificate/view.html", cert=cert, verify_url=verify_url)

@certificates_bp.route("/certificate/<certificate_id>/download")
def download_certificate(certificate_id):
    """Generate and stream ReportLab PDF certificate download"""
    cert = Certificate.query.filter_by(certificate_id=certificate_id).first_or_404()
    verify_url = get_certificate_verify_url(cert.certificate_id)

    cert_data = cert.to_dict()
    pdf_bytes = generate_certificate_pdf(cert_data, verify_url=verify_url)

    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', cert.student_name.strip())
    clean_test = re.sub(r'[^a-zA-Z0-9_-]', '_', cert.test_title.strip())
    filename = f"Certificate_{clean_name}_{clean_test}.pdf"

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@certificates_bp.route("/verify/<certificate_id>")
def verify_certificate(certificate_id):
    """Public certificate authenticity verification portal"""
    cert = Certificate.query.filter_by(certificate_id=certificate_id).first()
    verify_url = get_certificate_verify_url(certificate_id)
    return render_template(
        "certificate/verify.html",
        cert=cert,
        certificate_id=certificate_id,
        verify_url=verify_url,
    )

@certificates_bp.route("/admin/certificates")
@login_required
def admin_certificates():
    """Teacher certificate management list with filters and revocation"""
    status_filter = request.args.get("status", "all")  # all, active, revoked
    search = request.args.get("search", "").strip()

    query = Certificate.query.order_by(Certificate.generated_date.desc())

    if status_filter == "active":
        query = query.filter_by(is_revoked=False)
    elif status_filter == "revoked":
        query = query.filter_by(is_revoked=True)

    if search:
        query = query.filter(
            (Certificate.student_name.ilike(f"%{search}%")) |
            (Certificate.certificate_id.ilike(f"%{search}%")) |
            (Certificate.test_title.ilike(f"%{search}%"))
        )

    certificates = query.all()
    total_count = Certificate.query.count()
    active_count = Certificate.query.filter_by(is_revoked=False).count()
    revoked_count = total_count - active_count

    return render_template(
        "admin/certificates.html",
        certificates=certificates,
        status_filter=status_filter,
        search=search,
        stats={
            "total": total_count,
            "active": active_count,
            "revoked": revoked_count,
        }
    )

@certificates_bp.route("/admin/certificates/<certificate_id>/revoke", methods=["POST"])
@login_required
def revoke_certificate(certificate_id):
    """Revoke an issued certificate with a reason"""
    cert = Certificate.query.filter_by(certificate_id=certificate_id).first_or_404()
    reason = request.form.get("reason", "").strip() or "Administrative revocation"
    cert.is_revoked = True
    cert.revoke_reason = reason
    db.session.commit()
    flash(f"Certificate {cert.certificate_id} has been revoked.", "warning")
    return redirect(request.referrer or url_for("certificates.admin_certificates"))

@certificates_bp.route("/admin/certificates/<certificate_id>/reinstate", methods=["POST"])
@login_required
def reinstate_certificate(certificate_id):
    """Reinstate a previously revoked certificate"""
    cert = Certificate.query.filter_by(certificate_id=certificate_id).first_or_404()
    cert.is_revoked = False
    cert.revoke_reason = ""
    db.session.commit()
    flash(f"Certificate {cert.certificate_id} has been reinstated successfully.", "success")
    return redirect(request.referrer or url_for("certificates.admin_certificates"))
