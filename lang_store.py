import json
import os
from pathlib import Path
from typing import Optional

_DATA = os.getenv("DATA_DIR", "")
_DIR = Path(_DATA) if _DATA else Path(__file__).resolve().parent / "data"
_FILE = _DIR / "langs.json"

RU_CODES = ("ru", "uk", "be", "kk")


def _load() -> dict:
    try:
        return json.loads(_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def get_lang(user_id: int) -> Optional[str]:
    return _load().get(str(user_id))


def set_lang(user_id: int, lang: str) -> None:
    data = _load()
    data[str(user_id)] = lang
    try:
        _DIR.mkdir(parents=True, exist_ok=True)
        _FILE.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


def default_from_code(code: Optional[str]) -> str:
    if code and code.lower().split("-")[0] in RU_CODES:
        return "ru"
    return "en"


def resolve(user_id: int, code: Optional[str]) -> str:
    lang = get_lang(user_id)
    if lang in ("ru", "en"):
        return lang
    lang = default_from_code(code)
    set_lang(user_id, lang)
    return lang
