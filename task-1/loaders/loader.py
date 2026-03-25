import pandas as pd
from pathlib import Path

from loaders.dtypes import GTFS_DTYPES
from utils.time_utils import time_to_seconds

def _load_one_file(path: Path, name: str) -> pd.DataFrame:
    file_path = path / f"{name}.txt"
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_csv(file_path, dtype=GTFS_DTYPES.get(name, {}))


def _add_stop_times_seconds(stop_times: pd.DataFrame) -> pd.DataFrame:
    if stop_times.empty:
        return stop_times

    stop_times = stop_times.copy()
    stop_times["arrival_secs"] = (
        stop_times["arrival_time"].apply(time_to_seconds).astype("Int64")
    )
    stop_times["departure_secs"] = (
        stop_times["departure_time"].apply(time_to_seconds).astype("Int64")
    )
    return stop_times


def load_gtfs(folder: str | Path) -> dict[str, pd.DataFrame]:
    path = Path(folder)
    data = {}
    for name in GTFS_DTYPES:
        data[name] = _load_one_file(path, name)
    data["stop_times"] = _add_stop_times_seconds(data["stop_times"])
    return data

