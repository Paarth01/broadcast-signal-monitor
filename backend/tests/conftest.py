import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Set before any `app.*` module is imported, so config.py picks these up.
os.environ.setdefault("SIMULATOR_TICK_SECONDS", "0.2")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_signal_monitor.db")

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    yield
    db_file = Path(__file__).resolve().parents[1] / "test_signal_monitor.db"
    if db_file.exists():
        db_file.unlink()
