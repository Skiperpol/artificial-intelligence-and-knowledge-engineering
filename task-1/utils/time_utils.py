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


def add_time_in_seconds(stop_times: pd.DataFrame) -> pd.DataFrame:
    stop_times = stop_times.copy()
    stop_times["arrival_secs"] = stop_times["arrival_time"].apply(gtfs_time_to_seconds)
    stop_times["departure_secs"] = stop_times["departure_time"].apply(gtfs_time_to_seconds)
    return stop_times

