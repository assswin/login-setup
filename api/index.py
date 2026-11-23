import sys
from pathlib import Path

# Add project root and backend directory to sys.path for Vercel serverless runtime
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from backend.main import app

# Vercel serverless entrypoint
handler = app
