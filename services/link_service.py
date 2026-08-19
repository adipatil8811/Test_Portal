import os
import urllib.parse
from flask import request, current_app

PROD_URL = "https://testportalgvt.vercel.app"

def get_base_url():
    """
    Returns the public base URL of the platform.
    Priority:
    1. APP_URL from Flask config or environment (if not localhost in production)
    2. If in production / Vercel: https://testportalgvt.vercel.app
    3. Host from current request context (if not localhost in production)
    4. Default http://localhost:5000 for local development
    """
    is_prod = False
    if current_app:
        is_prod = bool(current_app.config.get("IS_PRODUCTION", False))
    if not is_prod:
        is_prod = bool(os.getenv("VERCEL") or os.getenv("RENDER") or os.getenv("FLASK_ENV") == "production" or os.getenv("ENV") == "production")

    configured = None
    if current_app:
        configured = current_app.config.get("APP_URL")
    if not configured:
        configured = os.getenv("APP_URL")

    # When in production / on Vercel
    if is_prod:
        if configured and "localhost" not in configured and "127.0.0.1" not in configured:
            return configured.rstrip("/")
        try:
            if request and request.host_url:
                host_url = request.host_url.rstrip("/")
                if "localhost" not in host_url and "127.0.0.1" not in host_url:
                    if host_url.startswith("http://"):
                        host_url = "https://" + host_url[len("http://"):]
                    return host_url
        except Exception:
            pass
        return PROD_URL

    # Local development
    if configured:
        return configured.rstrip("/")
    
    try:
        if request and request.host_url:
            return request.host_url.rstrip("/")
    except Exception:
        pass

    return "http://localhost:5000"

def get_test_share_url(test_id):
    """Generate public student test link"""
    return f"{get_base_url()}/test/{test_id}"

def get_certificate_verify_url(certificate_id):
    """Generate public certificate verification link"""
    return f"{get_base_url()}/verify/{certificate_id}"

def get_certificate_view_url(certificate_id):
    """Generate public certificate viewer link"""
    return f"{get_base_url()}/certificate/{certificate_id}"

def get_whatsapp_share_url(test_title, test_id):
    """Generate a 1-click WhatsApp share link with formatted invitation text"""
    link = get_test_share_url(test_id)
    message = (
        f"Hello Students! Here is the link to complete your \"{test_title}\" assessment:\n\n"
        f"{link}\n\n"
        f"Please take the test and earn your official Certificate of Achievement upon passing. Good luck!"
    )
    return f"https://api.whatsapp.com/send?text={urllib.parse.quote(message)}"
