import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "a3_submission"))

from wsgi import app  # noqa: E402
