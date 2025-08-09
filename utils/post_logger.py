import os
import json
from datetime import datetime
from typing import Any, Dict


LOG_FILE_PATH = "logs/post_events.log"


def log_post_event(event: Dict[str, Any]) -> None:
    """
    Append a JSON line with post event details to logs/post_events.log.
    Ensures logs directory exists. UTF-8, keep non-ASCII.
    """
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        **event,
    }
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
