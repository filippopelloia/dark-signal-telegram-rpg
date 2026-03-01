import json
import os
from typing import Any

_strings: dict[str, dict] = {}

def load_all():
    base = os.path.join(os.path.dirname(__file__), "../localization")
    for lang in ["en", "it", "es"]:
        path = os.path.join(base, f"{lang}.json")
        with open(path, encoding="utf-8") as f:
            _strings[lang] = json.load(f)

def t(player_lang: str, key: str, **kwargs) -> str:
    lang = player_lang if player_lang in _strings else "en"
    data = _strings[lang]
    
    # Support nested keys like "xeno_types.drone"
    parts = key.split(".")
    val = data
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p, None)
        else:
            val = None
            break
    
    if val is None:
        # Fallback to English
        val = _strings["en"]
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p, key)
            else:
                val = key
                break
    
    if isinstance(val, str) and kwargs:
        try:
            val = val.format(**kwargs)
        except KeyError:
            pass
    
    return val if isinstance(val, str) else key

def get_lang_options() -> list[dict]:
    return [
        {"lang": "it", "label": "🇮🇹 Italiano"},
        {"lang": "en", "label": "🇬🇧 English"},
        {"lang": "es", "label": "🇪🇸 Español"},
    ]

# Load on import
load_all()
