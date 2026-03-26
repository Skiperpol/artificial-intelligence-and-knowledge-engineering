import math

def calculate_edge_params(curr_cost, real_time, edge, last_trip_id, mode='t'):
    if edge.get('type') == 'transfer':
        new_real_time = real_time + edge['duration']
        new_cost = curr_cost + (edge['duration'] if mode == 't' else 0)
        dep_from_u = real_time
        return new_cost, new_real_time, dep_from_u, last_trip_id 
    
    new_trip_id = edge.get('trip_id')
    if edge['dep_time'] < real_time:
        return None

    new_real_time = edge['arr_time']
    if mode == 't':
        new_cost = curr_cost + (edge['arr_time'] - real_time)
        if last_trip_id is not None and new_trip_id != last_trip_id:
            new_cost += 300
    else:
        trip_change = False
        if last_trip_id and new_trip_id:
            trip_change = last_trip_id != new_trip_id
        new_cost = curr_cost + (1 if trip_change else 0)
    dep_from_u = edge['dep_time']
    
    return new_cost, new_real_time, dep_from_u, new_trip_id

def reconstruct_path(p_predecessors, d_distances, end_stop):
    best_final_state = None
    min_final_cost = float('inf')
    
    for (s, tid), cost in d_distances.items():
        if s == end_stop and cost < min_final_cost:
            min_final_cost = cost
            best_final_state = (s, tid)

    if not best_final_state:
        return None
    
    path = []
    curr_state = best_final_state
    while curr_state in p_predecessors:
        step = p_predecessors[curr_state]
        path.append(step)
        curr_state = (step['from_stop'], step['from_trip'])
    
    return path[::-1], min_final_cost