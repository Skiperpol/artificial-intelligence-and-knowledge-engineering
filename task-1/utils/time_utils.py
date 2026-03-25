import pandas as pd
from typing import Any

def time_to_seconds(time: Any) -> int | None:
    if pd.isna(time) or str(time).lower() in ("nan", ""):
        return None

    try:
        hours, minutes, seconds = map(int, str(time).split(":"))
        return hours * 3600 + minutes * 60 + seconds
    except ValueError:
        return None

def secs_to_time(secs):
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"