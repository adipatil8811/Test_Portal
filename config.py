import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Application Configuration Settings"""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-1234567890")
    
    # Database Configuration
    # On Vercel serverless, local storage is only writable in /tmp
    if os.getenv("VERCEL"):
        INSTANCE_PATH = Path("/tmp")
    else:
        INSTANCE_PATH = BASE_DIR / "instance"
        INSTANCE_PATH.mkdir(exist_ok=True)
    
    # Support standard DATABASE_URL (for PostgreSQL/Supabase/Neon in production) or SQLite locally
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        # Fix SQLAlchemy postgres:// vs postgresql:// compatibility
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = db_url or f"sqlite:///{INSTANCE_PATH / 'test_portal.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Teacher Admin Authentication
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secretteacherpassword")
    
    # Public Application Base URL
    # Automatically resolves VERCEL_URL if deployed on Vercel and APP_URL is not set
    vercel_url = os.getenv("VERCEL_URL")
    default_prod_url = f"https://{vercel_url}" if vercel_url else "http://localhost:5000"
    APP_URL = os.getenv("APP_URL", default_prod_url).rstrip("/")
    
    # Portal Details
    PORTAL_NAME = os.getenv("PORTAL_NAME", "Online Test Portal")
    INSTITUTE_NAME = os.getenv("INSTITUTE_NAME", "Online Test Academy")
