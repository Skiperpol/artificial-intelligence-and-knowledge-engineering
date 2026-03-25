from pathlib import Path
from utils.calendar_utils import get_active_service_ids
from utils.coords_utils import build_coords_dict
from graph.graph import build_graph, filter_graph_by_services, get_stop_groups, add_transfer_logic
from loaders.loader import load_gtfs

from pathlib import Path
from datetime import datetime, timedelta
from utils.calendar_utils import get_active_service_ids
from utils.coords_utils import build_coords_dict
from graph.graph import build_graph, get_stop_groups, add_transfer_logic
from loaders.loader import load_gtfs

def prepare_data_for_astar(gtfs_folder: str | Path, date_str: str):
    gtfs_data = load_gtfs(gtfs_folder)
    
    full_graph = build_graph(
        stops=gtfs_data["stops"],
        trips=gtfs_data["trips"],
        stop_times=gtfs_data["stop_times"],
        routes=gtfs_data["routes"]
    )

    stop_groups = get_stop_groups(gtfs_data["stops"])
    add_transfer_logic(full_graph, stop_groups)


    current_date_dt = datetime.strptime(date_str, "%Y%m%d")
    next_date_dt = current_date_dt + timedelta(days=1)
    next_date_str = next_date_dt.strftime("%Y%m%d")

    services_today = get_active_service_ids(gtfs_data["calendar"], gtfs_data["calendar_dates"], date_str)
    services_tomorrow = get_active_service_ids(gtfs_data["calendar"], gtfs_data["calendar_dates"], next_date_str)

    final_graph = {}
    SEC_IN_DAY = 86400

    for stop_id, edges in full_graph.items():
        new_edges = []
        for e in edges:
            if e.get('type') == 'transfer':
                new_edges.append(e)
                continue

            s_id = str(e.get("service_id"))
            
            if s_id in services_today:
                new_edges.append(e)
            
            if s_id in services_tomorrow:
                e_tomorrow = e.copy()
                e_tomorrow['dep_time'] += SEC_IN_DAY
                e_tomorrow['arr_time'] += SEC_IN_DAY
                new_edges.append(e_tomorrow)
        
        final_graph[stop_id] = new_edges

    coords = build_coords_dict(gtfs_data["stops"])

    return final_graph, coords