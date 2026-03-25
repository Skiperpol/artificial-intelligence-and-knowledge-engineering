
import heapq
import itertools

from algorithms.utils import calculate_edge_params, reconstruct_path
from algorithms.heuristics import get_heuristic


def a_star(graph, start_stop, end_stop, start_time_secs, coords, mode='t'):
    visited_count = 0
    counter = itertools.count()
    d_distances = {(start_stop, None): start_time_secs}
    p_predecessors = {} 
    
    h_start = get_heuristic(start_stop, end_stop, coords, mode)
    queue = [(start_time_secs + h_start, start_time_secs, start_time_secs, next(counter), start_stop, None)]

    while queue:
        f_curr, g_curr, real_time, _, u, last_trip_id = heapq.heappop(queue)
        visited_count += 1

        if u == end_stop:
            break

        if g_curr > d_distances.get((u, last_trip_id), float('inf')):
            continue

        for edge in graph.get(u, []):
            params = calculate_edge_params(g_curr, real_time, edge, last_trip_id, mode)
            if params is None: continue
                
            new_g, new_real, dep_t, new_tid = params
            v = edge['to']
            state = (v, new_tid)

            if new_g < d_distances.get(state, float('inf')):
                d_distances[state] = new_g
                h_val = get_heuristic(v, end_stop, coords, mode)
                p_predecessors[state] = {
                    "from_stop": u, "from_trip": last_trip_id, "to_stop": v,
                    "line": edge.get('route_name', 'WALK'), "dep": dep_t, "arr": new_real
                }
                heapq.heappush(queue, (new_g + h_val, new_g, new_real, next(counter), v, new_tid))

    path, total_cost = reconstruct_path(p_predecessors, d_distances, end_stop)
    return path, total_cost, visited_count