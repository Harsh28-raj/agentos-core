"""Central configuration. Every environment variable the backend reads is defined here."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
# Text-only models cannot read images; this must be a Groq vision-capable model.
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# --- Storage ---
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL", "")
REDIS_URL = os.getenv("REDIS_URL")
# auto | postgres | redis | memory
CHECKPOINTER = os.getenv("CHECKPOINTER", "auto").lower()

# --- Auth ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
ACCESS_TOKEN_EXPIRE_DAYS = _int("ACCESS_TOKEN_EXPIRE_DAYS", 7)

# --- HTTP ---
# Comma separated list of allowed origins. Auth uses bearer tokens (no cookies),
# so credentials are never allowed cross-origin.
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

# --- Agent behaviour ---
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")
CONTEXT_WINDOW_MESSAGES = _int("CONTEXT_WINDOW_MESSAGES", 12)
MAX_AGENT_HOPS = _int("MAX_AGENT_HOPS", 3)
RECURSION_LIMIT = _int("RECURSION_LIMIT", 25)

# The code interpreter runs model-written Python on this server. It is OFF unless
# explicitly enabled, because it is not a real sandbox (see docs/SECURITY.md).
ENABLE_CODE_INTERPRETER = _bool("ENABLE_CODE_INTERPRETER", False)
CODE_TIMEOUT_SECONDS = _int("CODE_TIMEOUT_SECONDS", 15)

# --- Uploads ---
MAX_UPLOAD_MB = _int("MAX_UPLOAD_MB", 10)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", Path(__file__).resolve().parents[2] / "uploads")).resolve()

# --- Google OAuth (Gmail + Calendar) ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/calendar",
]
