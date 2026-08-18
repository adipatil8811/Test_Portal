import time
import random
import string
import json
from datetime import datetime, timezone

def generate_test_id():
    """Generate a clean URL-friendly unique test identifier"""
    timestamp = int(time.time())
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"t_{timestamp}_{rand}"

def generate_question_id():
    """Generate a unique question identifier"""
    timestamp = int(time.time() * 1000)
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"q_{timestamp}_{rand}"

def generate_response_id():
    """Generate a unique response tracking ID"""
    year = datetime.now(timezone.utc).year
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"RESP-{year}-{rand}"

def generate_certificate_id():
    """Generate an official unique certificate verification code"""
    year = datetime.now(timezone.utc).year
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"CERT-{year}-{rand}"

def format_date(dt, fmt="%d %B %Y"):
    """Format datetime object or ISO string nicely for display"""
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return dt
    return dt.strftime(fmt)

def format_datetime_local(dt):
    """Format datetime to YYYY-MM-DDTHH:MM for HTML datetime-local input"""
    if not dt:
        return ""
    if isinstance(dt, str):
        return dt
    return dt.strftime("%Y-%m-%dT%H:%M")
