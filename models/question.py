import json
from models import db

class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.String(64), nullable=False, index=True)
    test_id = db.Column(db.String(64), db.ForeignKey("tests.test_id", ondelete="CASCADE"), nullable=False)
    
    question_text = db.Column(db.Text, nullable=False, default="")
    question_type = db.Column(db.String(32), nullable=False, default="multiple-choice")
    options_json = db.Column(db.Text, default="[]")
    correct_answer = db.Column(db.Text, default="")
    correct_answers_json = db.Column(db.Text, default="[]")
    
    marks = db.Column(db.Integer, default=1)
    required = db.Column(db.Boolean, default=True)
    explanation = db.Column(db.Text, default="")
    order_index = db.Column(db.Integer, default=0)

    @property
    def options(self):
        try:
            return json.loads(self.options_json) if self.options_json else []
        except Exception:
            return []

    @options.setter
    def options(self, val):
        self.options_json = json.dumps(val or [])

    @property
    def correct_answers(self):
        try:
            return json.loads(self.correct_answers_json) if self.correct_answers_json else []
        except Exception:
            return []

    @correct_answers.setter
    def correct_answers(self, val):
        self.correct_answers_json = json.dumps(val or [])

    def to_dict(self):
        return {
            "id": self.question_id,
            "type": self.question_type,
            "question": self.question_text,
            "options": self.options,
            "correctAnswer": self.correct_answer,
            "correctAnswers": self.correct_answers,
            "marks": self.marks,
            "required": self.required,
            "explanation": self.explanation,
            "orderIndex": self.order_index,
        }
