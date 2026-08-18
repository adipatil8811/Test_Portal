from functools import wraps
from flask import session, redirect, url_for, request, flash, current_app
from werkzeug.security import check_password_hash, generate_password_hash

def login_required(f):
    """Decorator to require teacher/admin login for sensitive routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please sign in to access the Teacher Portal.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def is_admin_authenticated():
    """Check if current session is authenticated as admin"""
    return session.get("admin_logged_in") is True

def login_admin(username="admin"):
    """Set session variables on admin login"""
    session["admin_logged_in"] = True
    session["admin_username"] = username
    session.permanent = True

def logout_admin():
    """Clear admin session on logout"""
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)

def verify_admin_password(password):
    """Verify admin password against environment or database"""
    expected_password = current_app.config.get("ADMIN_PASSWORD", "12345")
    if password == expected_password:
        return True
    
    # Also check AdminUser model in database if exists
    try:
        from models.admin import AdminUser
        admin = AdminUser.query.filter_by(username="admin").first()
        if admin and admin.check_password(password):
            return True
    except Exception:
        pass
    
    return False
