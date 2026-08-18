from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.student import student_bp
from routes.results import results_bp
from routes.certificates import certificates_bp

def register_routes(app):
    """Register all Flask blueprints"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(certificates_bp)
