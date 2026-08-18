from datetime import datetime, timezone
from models import db

class Certificate(db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)
    certificate_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    response_id = db.Column(db.String(64), db.ForeignKey("responses.response_id", ondelete="CASCADE"), nullable=False, index=True)
    test_id = db.Column(db.String(64), db.ForeignKey("tests.test_id", ondelete="CASCADE"), nullable=False, index=True)
    
    student_name = db.Column(db.String(128), nullable=False)
    student_email = db.Column(db.String(128), default="")
    test_title = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Float, default=0.0)
    total_marks = db.Column(db.Integer, default=0)
    percentage = db.Column(db.String(16), default="0.0")
    
    is_revoked = db.Column(db.Boolean, default=False)
    revoke_reason = db.Column(db.String(255), default="")
    
    institute_name = db.Column(db.String(255), default="")
    institute_logo = db.Column(db.String(512), default="")
    teacher_signature = db.Column(db.String(512), default="")
    teacher_signer_title = db.Column(db.String(128), default="Authorized Instructor")
    
    certificate_template = db.Column(db.String(64), default="classic")
    certificate_title = db.Column(db.String(255), default="Certificate of Achievement")
    certificate_description = db.Column(
        db.Text,
        default="For successfully completing the {{TEST_NAME}} assessment with a score of {{SCORE}}/{{TOTAL_MARKS}} ({{PERCENTAGE}}%)."
    )
    
    show_score = db.Column(db.Boolean, default=True)
    show_percentage = db.Column(db.Boolean, default=True)
    show_certificate_id = db.Column(db.Boolean, default=True)
    show_issue_date = db.Column(db.Boolean, default=True)
    show_qr_code = db.Column(db.Boolean, default=True)
    
    email_status = db.Column(db.String(32), default="Not Sent")
    generated_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        date_str = self.generated_date.strftime("%d %B %Y") if self.generated_date else ""
        return {
            "certificateId": self.certificate_id,
            "responseId": self.response_id,
            "testId": self.test_id,
            "studentName": self.student_name,
            "studentEmail": self.student_email,
            "testTitle": self.test_title,
            "score": self.score,
            "totalMarks": self.total_marks,
            "percentage": self.percentage,
            "date": date_str,
            "isRevoked": self.is_revoked,
            "revokeReason": self.revoke_reason,
            "instituteName": self.institute_name,
            "instituteLogo": self.institute_logo,
            "teacherSignature": self.teacher_signature,
            "teacherSignerTitle": self.teacher_signer_title,
            "certificateTemplate": self.certificate_template,
            "certificateTitle": self.certificate_title,
            "certificateDescription": self.certificate_description,
            "showScore": self.show_score,
            "showPercentage": self.show_percentage,
            "showCertificateId": self.show_certificate_id,
            "showIssueDate": self.show_issue_date,
            "showQrCode": self.show_qr_code,
            "emailStatus": self.email_status,
            "generatedDate": self.generated_date.isoformat() if self.generated_date else "",
        }
