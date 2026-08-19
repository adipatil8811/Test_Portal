import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from sqlalchemy import text
from config import Config
from models import db
from models.test import Test
from models.question import Question
from models.admin import AdminUser
from routes import register_routes
from utils.security import is_admin_authenticated
from utils.helpers import format_date, generate_test_id, generate_question_id
from services.link_service import get_base_url

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_app(config_class=Config):
    """Flask Application Factory with Production Security & Serverless Support"""
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
        static_url_path="/static"
    )
    app.config.from_object(config_class)

    # Initialize Database
    db.init_app(app)

    # Register Blueprints
    register_routes(app)

    # Health Check Endpoint
    @app.route("/health", methods=["GET"])
    def health_check():
        """Public health check endpoint for monitoring & deployment validation"""
        db_status = "connected"
        db_healthy = True
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"disconnected: {str(e)}"
            db_healthy = False

        status_code = 200 if db_healthy else 503
        return jsonify({
            "status": "ok" if db_healthy else "error",
            "service": "Online Test Portal",
            "institute": app.config.get("INSTITUTE_NAME", "GVT"),
            "database": db_status,
            "production": app.config.get("IS_PRODUCTION", False),
        }), status_code

    # Explicit Static Asset Delivery (Guarantees static file serving on Vercel)
    @app.route("/static/<path:filename>")
    @app.route("/api/static/<path:filename>")
    @app.route("/api/index/static/<path:filename>")
    def custom_static(filename):
        mimetype = None
        lower_name = filename.lower()
        if lower_name.endswith(".css"):
            mimetype = "text/css"
        elif lower_name.endswith(".js"):
            mimetype = "application/javascript"
        elif lower_name.endswith(".svg"):
            mimetype = "image/svg+xml"
        elif lower_name.endswith(".png"):
            mimetype = "image/png"
        elif lower_name.endswith((".jpg", ".jpeg")):
            mimetype = "image/jpeg"
        return send_from_directory(os.path.join(BASE_DIR, "static"), filename, mimetype=mimetype)

    # Production Security Headers Middleware
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response

    # Global Template Context & Filters
    @app.context_processor
    def inject_globals():
        return {
            "is_admin": is_admin_authenticated(),
            "app_url": get_base_url(),
            "portal_name": app.config.get("PORTAL_NAME", "Online Test Portal"),
            "institute_name": app.config.get("INSTITUTE_NAME", "GVT"),
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

    # Initialize Database Tables Safely
    with app.app_context():
        try:
            db.create_all()
            if app.config.get("SEED_DEMO", False):
                seed_initial_data()
        except Exception as err:
            # Don't crash worker on ephemeral connection glitch
            print("Database setup notice:", err)

    return app

def seed_initial_data():
    """Seed initial sample test only when explicitly requested (SEED_DEMO=true)"""
    if Test.query.count() == 0:
        demo_test_id = "t_demo_science"
        sample_test = Test(
            test_id=demo_test_id,
            title="General Science & Physics Fundamentals",
            description="Complete this 4-question assessment. Score 40% or higher to receive your verified Certificate of Achievement.",
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

        questions_data = [
            {
                "id": "q_101",
                "type": "multiple-choice",
                "question": "What is the SI unit of electric current?",
                "options": ["Volt", "Ampere", "Ohm", "Watt"],
                "correctAnswer": "Ampere",
                "marks": 1,
                "required": True,
                "explanation": "The ampere (symbol: A) is the base unit of electric current in the International System of Units (SI)."
            },
            {
                "id": "q_102",
                "type": "true-false",
                "question": "Light travels faster in water than in a vacuum.",
                "options": ["True", "False"],
                "correctAnswer": "False",
                "marks": 1,
                "required": True,
                "explanation": "Light travels fastest in a vacuum (approx 3 x 10^8 m/s) and slows down in denser optical mediums like water."
            },
            {
                "id": "q_103",
                "type": "multiple-correct",
                "question": "Which of the following are Noble Gases? (Select all that apply)",
                "options": ["Helium", "Nitrogen", "Neon", "Argon"],
                "correctAnswers": ["Helium", "Neon", "Argon"],
                "marks": 2,
                "required": True,
                "explanation": "Helium, Neon, and Argon are Group 18 noble gases with full valence electron shells. Nitrogen is in Group 15."
            },
            {
                "id": "q_104",
                "type": "short-answer",
                "question": "What is the chemical formula for water?",
                "correctAnswer": "H2O",
                "marks": 1,
                "required": True,
                "explanation": "Water is composed of two hydrogen atoms bonded to one oxygen atom (H2O)."
            }
        ]

        for i, q in enumerate(questions_data):
            question_obj = Question(
                question_id=q["id"],
                test_id=demo_test_id,
                question_text=q["question"],
                question_type=q["type"],
                options_json=json.dumps(q.get("options", [])),
                correct_answer=q.get("correctAnswer", ""),
                correct_answers_json=json.dumps(q.get("correctAnswers", [])),
                marks=q["marks"],
                required=q.get("required", True),
                explanation=q.get("explanation", ""),
                order_index=i
            )
            db.session.add(question_obj)

        db.session.commit()

# Create application instance for WSGI runners
app = create_app()
handler = app
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
