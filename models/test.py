from datetime import datetime, timezone
from models import db

class Test(db.Model):
    __tablename__ = "tests"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")
    subject = db.Column(db.String(128), default="")
    class_name = db.Column(db.String(64), default="")
    division = db.Column(db.String(64), default="")
    duration = db.Column(db.Integer, default=0)  # 0 for unlimited
    total_marks = db.Column(db.Integer, default=0)
    published = db.Column(db.Boolean, default=False)
    
    # Schedule & Availability
    start_date = db.Column(db.String(64), default="")  # YYYY-MM-DDTHH:MM
    end_date = db.Column(db.String(64), default="")
    
    # Student Settings
    show_result = db.Column(db.Boolean, default=True)
    collect_email = db.Column(db.Boolean, default=False)
    require_name = db.Column(db.Boolean, default=True)
    require_class = db.Column(db.Boolean, default=True)
    require_division = db.Column(db.Boolean, default=False)
    require_roll_number = db.Column(db.Boolean, default=True)
    allow_multiple = db.Column(db.Boolean, default=False)
    shuffle_questions = db.Column(db.Boolean, default=False)
    shuffle_options = db.Column(db.Boolean, default=False)
    
    # Certificate Settings
    enable_certificate = db.Column(db.Boolean, default=True)
    certificate_min_percentage = db.Column(db.Integer, default=40)
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
    show_score_on_cert = db.Column(db.Boolean, default=True)
    show_percentage_on_cert = db.Column(db.Boolean, default=True)
    show_cert_id = db.Column(db.Boolean, default=True)
    show_issue_date = db.Column(db.Boolean, default=True)
    show_qr_code = db.Column(db.Boolean, default=True)
    email_certificate = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    questions = db.relationship("Question", backref="test", cascade="all, delete-orphan", order_by="Question.order_index")
    responses = db.relationship("Response", backref="test", cascade="all, delete-orphan", lazy="dynamic")
    certificates = db.relationship("Certificate", backref="test", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self):
        return {
            "testId": self.test_id,
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "class": self.class_name,
            "division": self.division,
            "duration": self.duration,
            "totalMarks": self.total_marks,
            "published": self.published,
            "settings": {
                "showResult": self.show_result,
                "collectEmail": self.collect_email,
                "requireName": self.require_name,
                "requireClass": self.require_class,
                "requireDivision": self.require_division,
                "requireRollNumber": self.require_roll_number,
                "allowMultiple": self.allow_multiple,
                "shuffleQuestions": self.shuffle_questions,
                "shuffleOptions": self.shuffle_options,
                "timeLimit": self.duration,
                "startDate": self.start_date,
                "endDate": self.end_date,
                "enableCertificate": self.enable_certificate,
                "certificateMinPercentage": self.certificate_min_percentage,
                "instituteName": self.institute_name,
                "instituteLogo": self.institute_logo,
                "teacherSignature": self.teacher_signature,
                "teacherSignerTitle": self.teacher_signer_title,
                "certificateTemplate": self.certificate_template,
                "certificateTitle": self.certificate_title,
                "certificateDescription": self.certificate_description,
                "showScoreOnCertificate": self.show_score_on_cert,
                "showPercentageOnCertificate": self.show_percentage_on_cert,
                "showCertificateId": self.show_cert_id,
                "showIssueDate": self.show_issue_date,
                "showQrCode": self.show_qr_code,
                "emailCertificate": self.email_certificate,
            },
            "questions": [q.to_dict() for q in self.questions],
            "questionCount": len(self.questions),
            "responseCount": self.responses.count(),
            "createdAt": self.created_at.isoformat() if self.created_at else "",
            "updatedAt": self.updated_at.isoformat() if self.updated_at else "",
        }
