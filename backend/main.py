from pathlib import Path
import sys

doctor_core_path = Path(__file__).resolve().parent / "doctor_core"
if str(doctor_core_path) not in sys.path:
    sys.path.insert(0, str(doctor_core_path))

from main import app

__all__ = ["app"]
