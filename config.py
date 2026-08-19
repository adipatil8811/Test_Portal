import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Production-Ready Application Configuration"""

    # Secret Key for Sessions & Cookies
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-1234567890")

    # Session Security Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    
    # Public Application Base URL
    # Production default: https://testportalgvt.vercel.app
    # Development default: http://localhost:5000
    is_vercel = bool(os.getenv("VERCEL"))
    is_prod_env = os.getenv("FLASK_ENV") == "production" or os.getenv("ENV") == "production"
    
    app_url_env = os.getenv("APP_URL")
    if app_url_env:
        APP_URL = app_url_env.rstrip("/")
    elif is_vercel or is_prod_env:
        APP_URL = "https://testportalgvt.vercel.app"
    elif os.getenv("RENDER_EXTERNAL_URL"):
        APP_URL = os.getenv("RENDER_EXTERNAL_URL").rstrip("/")
    else:
        APP_URL = "http://localhost:5000"
    
    # Enable HTTPS cookies in production or on Vercel/Render
    IS_PRODUCTION = bool(is_vercel or is_prod_env or os.getenv("RENDER") or APP_URL.startswith("https://"))
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Database Configuration
    # Supports PostgreSQL in production (Supabase / Neon / Render / Vercel Postgres)
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        # Fix SQLAlchemy compatibility for postgres:// -> postgresql://
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # Check if persistent database is explicitly required
    require_persistent_db = os.getenv("REQUIRE_PERSISTENT_DB", "false").lower() in ("true", "1", "yes")
    if require_persistent_db and not db_url:
        raise RuntimeError(
            "REQUIRE_PERSISTENT_DB is set to true, but DATABASE_URL is missing. "
            "Please configure DATABASE_URL with a valid PostgreSQL connection string."
        )

    # Local development storage fallback
    if os.getenv("VERCEL"):
        INSTANCE_PATH = Path("/tmp")
    else:
        INSTANCE_PATH = BASE_DIR / "instance"
        INSTANCE_PATH.mkdir(exist_ok=True)

    SQLALCHEMY_DATABASE_URI = db_url or f"sqlite:///{INSTANCE_PATH / 'test_portal.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    } if db_url else {}

    # Teacher Admin Authentication Credentials
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "12345")

    # Demo Seed Flag (Default False in production)
    SEED_DEMO = os.getenv("SEED_DEMO", "false").lower() in ("true", "1", "yes")

    # School & Portal Branding Details
    PORTAL_NAME = os.getenv("PORTAL_NAME", "Online Test Portal")
    INSTITUTE_NAME = os.getenv("INSTITUTE_NAME", "GVT")
