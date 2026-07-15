from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent

def get_root():
    return Path(os.environ.get(
        "HANDS_OFF_ROOT",
        PROJECT_ROOT
    ))

ROOT = get_root()
STATE = ROOT / "state"
FINANCE = ROOT / "finance"
CONFIG = ROOT / "config"
