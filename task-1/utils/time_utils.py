import pandas as pd
from typing import Any


def gtfs_time_to_seconds(time: Any) -> int | None:
    if pd.isna(time) or str(time).lower() in ("nan", ""):
        return None

    try:
        hours, minutes, seconds = map(int, str(time).split(":"))
        return hours * 3600 + minutes * 60 + seconds
    except ValueError:
        return None
