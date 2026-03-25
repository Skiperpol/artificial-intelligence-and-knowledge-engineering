import pandas as pd

def build_coords_dict(stops: pd.DataFrame) -> dict[str, dict[str, float]]:
    coords = stops.set_index("stop_id")[["stop_lat", "stop_lon"]].to_dict("index")
    return coords