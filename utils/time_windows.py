# utils/time_windows.py

from datetime import datetime, timedelta
import pytz

def get_time_range_for_mode(mode: str):
    moscow_tz = pytz.timezone("Europe/Moscow")
    now = datetime.now(moscow_tz)

    if mode == "morning":
        start_time = now.replace(hour=23, minute=15, second=0, microsecond=0) - timedelta(days=1)
        end_time = now.replace(hour=7, minute=15, second=0, microsecond=0)
    elif mode == "midday":
        start_time = now.replace(hour=7, minute=20, second=0, microsecond=0)
        end_time = now.replace(hour=13, minute=15, second=0, microsecond=0)
    elif mode == "evening":
        start_time = now.replace(hour=15, minute=15, second=0, microsecond=0)
        end_time = now.replace(hour=23, minute=15, second=0, microsecond=0)
    else:
        raise ValueError(f"Неизвестный режим: {mode}")

    return start_time, end_time