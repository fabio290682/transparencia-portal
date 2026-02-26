import sys
from pathlib import Path

# Make flask_version importable when running on Vercel.
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "flask_version"))

from app import app  # noqa: E402,F401

