from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.security import is_admin_authenticated, login_admin, logout_admin, verify_admin_password

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
@auth_bp.route("/api")
@auth_bp.route("/api/")
@auth_bp.route("/api/index")
@auth_bp.route("/api/index.py")
@auth_bp.route("/index")
@auth_bp.route("/index.py")
def index():
    """Homepage route"""
    if is_admin_authenticated():
        return redirect(url_for("admin.dashboard"))
    return render_template("login.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Teacher / Admin Login route"""
    if is_admin_authenticated():
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        next_url = request.args.get("next") or url_for("admin.dashboard")

        if verify_admin_password(password):
            login_admin()
            flash("Welcome back, Teacher!", "success")
            return redirect(next_url)
        else:
            flash("Incorrect admin password. Please try again.", "danger")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    """Teacher Logout route"""
    logout_admin()
    flash("You have been securely signed out.", "info")
    return redirect(url_for("auth.login"))
