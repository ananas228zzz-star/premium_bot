import os
from pathlib import Path
from typing import Optional

_DATA = os.getenv("DATA_DIR", "")
_DIR = Path(_DATA) if _DATA else Path(__file__).resolve().parent / "data"
_FILE = _DIR / "gate_channel.txt"


def get_gate_id() -> Optional[int]:
    env = os.getenv("GATE_CHANNEL_ID", "").strip()
    if env:
        try:
            return int(env)
        except ValueError:
            pass
    try:
        return int(_FILE.read_text().strip())
    except (OSError, ValueError):
        return None


def set_gate_id(chat_id: int) -> None:
    _FILE.parent.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(str(chat_id))
