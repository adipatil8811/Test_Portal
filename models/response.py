import json
from datetime import datetime, timezone
from models import db

class Response(db.Model):
    __tablename__ = "responses"

    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    test_id = db.Column(db.String(64), db.ForeignKey("tests.test_id", ondelete="CASCADE"), nullable=False, index=True)
    
    test_title = db.Column(db.String(255), default="")
    student_name = db.Column(db.String(128), nullable=False)
    student_email = db.Column(db.String(128), default="")
    student_class = db.Column(db.String(64), default="")
    student_division = db.Column(db.String(64), default="")
    roll_number = db.Column(db.String(64), default="")
    
    score = db.Column(db.Float, default=0.0)
    total_marks = db.Column(db.Integer, default=0)
    percentage = db.Column(db.String(16), default="0.0")
    passed = db.Column(db.Boolean, default=False)
    
    correct_count = db.Column(db.Integer, default=0)
    incorrect_count = db.Column(db.Integer, default=0)
    unanswered_count = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    
    answers_json = db.Column(db.Text, default="{}")
    evaluation_json = db.Column(db.Text, default="[]")
    
    certificate_status = db.Column(db.String(32), default="Not Generated")
    certificate_id = db.Column(db.String(64), nullable=True)
    
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    certificate = db.relationship("Certificate", backref="response", uselist=False, cascade="all, delete-orphan")

    @property
    def answers(self):
        try:
            return json.loads(self.answers_json) if self.answers_json else {}
        except Exception:
            return {}

    @answers.setter
    def answers(self, val):
        self.answers_json = json.dumps(val or {})

    @property
    def evaluation(self):
        try:
            return json.loads(self.evaluation_json) if self.evaluation_json else []
        except Exception:
            return []

    @evaluation.setter
    def evaluation(self, val):
        self.evaluation_json = json.dumps(val or [])

    def to_dict(self):
        return {
            "responseId": self.response_id,
            "testId": self.test_id,
            "testTitle": self.test_title,
            "studentName": self.student_name,
            "studentEmail": self.student_email,
            "studentClass": self.student_class,
            "studentDivision": self.student_division,
            "rollNumber": self.roll_number,
            "score": self.score,
            "totalMarks": self.total_marks,
            "percentage": self.percentage,
            "passed": self.passed,
            "correctCount": self.correct_count,
            "incorrectCount": self.incorrect_count,
            "unansweredCount": self.unanswered_count,
            "totalQuestions": self.total_questions,
            "answers": self.answers,
            "questionReviews": self.evaluation,
            "certificateStatus": self.certificate_status,
            "certificateId": self.certificate_id,
            "submittedAt": self.submitted_at.isoformat() if self.submitted_at else "",
        }
