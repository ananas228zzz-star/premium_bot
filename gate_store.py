from typing import Optional

import config

_FILE = config.BASE_DIR / "data" / "gate_channel.txt"


def get_gate_id() -> Optional[int]:
    try:
        return int(_FILE.read_text().strip())
    except (OSError, ValueError):
        return None


def set_gate_id(chat_id: int) -> None:
    _FILE.parent.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(str(chat_id))