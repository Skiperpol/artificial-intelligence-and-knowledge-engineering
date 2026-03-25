from typing import Any

import pandas as pd

def _prepare_merged_data(stop_times: pd.DataFrame, trips: pd.DataFrame, routes: pd.DataFrame) -> pd.DataFrame:
    trips_with_routes = trips.merge(routes[["route_id", "route_short_name", "route_long_name"]], on="route_id", how="left")
    trips_with_routes["route_name"] = trips_with_routes["route_short_name"].fillna(trips_with_routes["route_long_name"])
    trips_subset = trips_with_routes[["trip_id", "route_name", "service_id"]]
    merged = stop_times.merge(trips_subset, on="trip_id", how="left")
    return merged.sort_values(["trip_id", "stop_sequence"])

def _create_edge(prev_row, current_row) -> dict[str, Any]:
    return {
        "to": str(current_row.stop_id),
        "dep_time": prev_row.departure_secs,
        "arr_time": current_row.arrival_secs,
        "trip_id": current_row.trip_id,
        "route_name": current_row.route_name,
        "service_id": current_row.service_id,
        "type": "travel"
    }

def build_graph(stops, trips, stop_times, routes):
    merged = _prepare_merged_data(stop_times, trips, routes)
    graph = {}

    poprzedni = None
    for wiersz in merged.itertuples():
        curr_stop = str(wiersz.stop_id)
        if curr_stop not in graph: 
            graph[curr_stop] = []
            
        if poprzedni is not None and wiersz.trip_id == poprzedni.trip_id:
            from_stop = str(poprzedni.stop_id)

            can_pickup = getattr(poprzedni, 'pickup_type', 0) != 1
            if can_pickup:
                edge = _create_edge(poprzedni, wiersz)
                graph[from_stop].append(edge)
        poprzedni = wiersz
    return graph

def get_stop_groups(stops_df: pd.DataFrame) -> dict:
    stops_df['group_id'] = stops_df['parent_station'].fillna(stops_df['stop_id'])
    groups = stops_df.groupby('group_id')['stop_id'].apply(list).to_dict()
    return groups

def add_transfer_logic(graph, stop_groups):
    for group_id, child_stops in stop_groups.items():
        child_stops = [str(s) for s in child_stops]
        for s1 in child_stops:
            for s2 in child_stops:
                if s1 != s2:
                    if s1 not in graph: graph[s1] = []
                    graph[s1].append({
                        'to': s2,
                        'type': 'transfer',
                        'duration': 0,
                        'route_name': 'WALK'
                    })
