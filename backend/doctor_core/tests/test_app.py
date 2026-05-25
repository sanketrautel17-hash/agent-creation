from pathlib import Path
import sys

service_root = Path(__file__).resolve().parents[1]
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

from main import app


def test_app_exists() -> None:
    assert app.title == "Doctor AI Platform"
