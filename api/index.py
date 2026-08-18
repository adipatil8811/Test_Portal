import sys
import os

# Ensure root directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app

class VercelPathFix:
    """WSGI middleware to normalize PATH_INFO for Vercel serverless functions"""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path.startswith("/api/index"):
            environ["PATH_INFO"] = path[len("/api/index"):] or "/"
        elif path.startswith("/api") and not path.startswith("/admin/api"):
            environ["PATH_INFO"] = path[len("/api"):] or "/"
        return self.wsgi_app(environ, start_response)

app = VercelPathFix(flask_app)
