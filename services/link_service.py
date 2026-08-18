import os
import urllib.parse
from flask import request, current_app

def get_base_url():
    """
    Returns the public base URL of the platform.
    Priority:
    1. Config APP_URL (e.g. https://your-domain.com)
    2. VERCEL_URL (auto-injected on Vercel deployment)
    3. request.host_url (if within a request context)
    4. Default http://localhost:5000
    """
    configured = current_app.config.get("APP_URL") if current_app else os.getenv("APP_URL")
    if configured and configured not in ("http://localhost:5000", "http://127.0.0.1:5000"):
        return configured.rstrip("/")
    
    vercel_url = os.getenv("VERCEL_URL")
    if vercel_url:
        return f"https://{vercel_url}".rstrip("/")

    try:
        if request and request.host_url:
            return request.host_url.rstrip("/")
    except Exception:
        pass
    
    return (configured or "http://localhost:5000").rstrip("/")

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
