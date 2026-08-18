import sys
import os

# Ensure project root directory is on Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app

def app(environ, start_response):
    """
    WSGI Entrypoint for Vercel Serverless Functions.
    Accurately reconstructs the original browser request path
    from Vercel proxy headers and strips serverless routing prefixes.
    """
    # 1. Look for original requested URI in standard reverse proxy headers
    raw_uri = (
        environ.get("HTTP_X_FORWARDED_URI")
        or environ.get("HTTP_X_NOW_ROUTE")
        or environ.get("RAW_URI")
        or environ.get("REQUEST_URI")
        or environ.get("PATH_INFO", "/")
    )

    # 2. Separate query string if embedded in raw_uri
    if "?" in raw_uri:
        path, query_str = raw_uri.split("?", 1)
        environ["QUERY_STRING"] = query_str
    else:
        path = raw_uri

    # 3. Strip any serverless handler prefixes added by Vercel rewrites
    for prefix in ("/api/index.py", "/api/index", "/api"):
        if path == prefix:
            path = "/"
            break
        elif path.startswith(prefix + "/"):
            # Don't strip /admin/api routes that legitimately belong to Flask
            if not path.startswith("/admin/api"):
                path = path[len(prefix):]
                break

    if not path or not path.startswith("/"):
        path = "/" + path

    environ["PATH_INFO"] = path
    return flask_app(environ, start_response)
