import heapq
import itertools

from algorithms.utils import calculate_edge_params, reconstruct_path

def dijkstra(graph, start_stop, end_stop, start_time_secs, mode='t'):
    visited_count = 0
    counter = itertools.count()
    
    d_distances = {(start_stop, None): start_time_secs}
    p_predecessors = {} 

    queue = [(start_time_secs, start_time_secs, next(counter), start_stop, None)]

    while queue:
        curr_cost, real_time, _, u, last_trip_id = heapq.heappop(queue)
        visited_count += 1

        if curr_cost > d_distances.get((u, last_trip_id), float('inf')):
            continue

        for edge in graph.get(u, []):
            params = calculate_edge_params(curr_cost, real_time, edge, last_trip_id, mode)
            
            if params is None:
                continue
                
            new_cost, new_real_time, dep_time, new_trip_id = params
            v = edge['to']
            state = (v, new_trip_id)

            if new_cost < d_distances.get(state, float('inf')):
                d_distances[state] = new_cost
                p_predecessors[state] = {
                    "from_stop": u, 
                    "from_trip": last_trip_id,
                    "to_stop": v,
                    "line": edge.get('route_name', 'WALK'),
                    "dep": dep_time,
                    "arr": new_real_time
                }
                heapq.heappush(queue, (new_cost, new_real_time, next(counter), v, new_trip_id))

    path, total_cost = reconstruct_path(p_predecessors, d_distances, end_stop)
    return path, total_cost, visited_count