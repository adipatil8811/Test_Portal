import os
import json
from flask import Flask, render_template
from config import Config
from models import db
from models.test import Test
from models.question import Question
from models.admin import AdminUser
from routes import register_routes
from utils.security import is_admin_authenticated
from utils.helpers import format_date, generate_test_id, generate_question_id

def create_app(config_class=Config):
    """Flask Application Factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Database
    db.init_app(app)

    # Register Blueprints
    register_routes(app)

    # Context Processors & Template Filters
    @app.context_processor
    def inject_globals():
        return {
            "is_admin": is_admin_authenticated(),
            "app_url": app.config.get("APP_URL", "http://localhost:5000"),
            "portal_name": app.config.get("PORTAL_NAME", "Online Test Portal"),
        }

    @app.template_filter("format_date")
    def filter_format_date(val, fmt="%d %B %Y"):    
        return format_date(val, fmt)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

    # Initialize Database Tables & Seed Demo Test if empty
    with app.app_context():
        db.create_all()
        seed_initial_data()

    return app

def seed_initial_data():
    """Seed initial sample test if database is fresh"""
    if Test.query.count() == 0:
        demo_test_id = "t_demo_science"
        sample_test = Test(
            test_id=demo_test_id,
            title="General Science & Physics Fundamentals",
            description="Complete this 5-question assessment. Score 40% or higher to receive your verified Certificate of Achievement.",
            subject="Science",
            class_name="Class 10",
            duration=15,
            total_marks=5,
            published=True,
            enable_certificate=True,
            certificate_min_percentage=40,
            institute_name="GVT",
            teacher_signer_title="Head Instructor",
            certificate_template="classic",
            certificate_title="Certificate of Achievement",
            certificate_description="For successfully completing the {{TEST_NAME}} assessment with a score of {{SCORE}}/{{TOTAL_MARKS}} ({{PERCENTAGE}}%).",
            show_score_on_cert=True,
            show_percentage_on_cert=True,
            show_cert_id=True,
            show_issue_date=True,
            show_qr_code=True,
        )
        db.session.add(sample_test)

        # Seed 4 Questions
        q1 = Question(
            question_id="q_101",
            test_id=demo_test_id,
            question_text="What is the SI unit of electric current?",
            question_type="multiple-choice",
            options_json=json.dumps(["Volt", "Ampere", "Ohm", "Watt"]),
            correct_answer="Ampere",
            marks=1,
            required=True,
            explanation="The SI unit of electric current is the Ampere (A), named after André-Marie Ampère.",
            order_index=0,
        )
        q2 = Question(
            question_id="q_102",
            test_id=demo_test_id,
            question_text="Light travels faster in vacuum than through glass.",
            question_type="true-false",
            options_json=json.dumps(["True", "False"]),
            correct_answer="True",
            marks=1,
            required=True,
            explanation="Light travels at its maximum speed of ~300,000 km/s in a vacuum and slows down in optical mediums like glass.",
            order_index=1,
        )
        q3 = Question(
            question_id="q_103",
            test_id=demo_test_id,
            question_text="Which of the following are noble gases? (Check all that apply)",
            question_type="multiple-correct",
            options_json=json.dumps(["Helium", "Oxygen", "Neon", "Argon"]),
            correct_answers_json=json.dumps(["Helium", "Neon", "Argon"]),
            marks=2,
            required=True,
            explanation="Helium, Neon, and Argon belong to Group 18 (noble gases). Oxygen is a diatomic reactive gas in Group 16.",
            order_index=2,
        )
        q4 = Question(
            question_id="q_104",
            test_id=demo_test_id,
            question_text="What is the chemical formula for water?",
            question_type="multiple-choice",
            options_json=json.dumps(["CO2", "H2O", "NaCl", "CH4"]),
            correct_answer="H2O",
            marks=1,
            required=True,
            explanation="Water consists of two hydrogen atoms bonded to one oxygen atom (H2O).",
            order_index=3,
        )

        db.session.add_all([q1, q2, q3, q4])
        db.session.commit()

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
