import time
import random
from collections import deque

def get_route_full_details(permutation, start_id, start_secs, graph, coords, criterion, algo_func):
    current_time = start_secs
    total_path = []
    
    full_sequence = [start_id] + list(permutation) + [start_id]
    
    for i in range(len(full_sequence) - 1):
        u, v = full_sequence[i], full_sequence[i+1]
        segment_path, _, _ = algo_func(graph, u, v, current_time, coords, criterion)
        
        if not segment_path:
            return None, float('inf')
        
        total_path.extend(segment_path)
        current_time = segment_path[-1]['arr']
        
    final_cost = current_time - start_secs if criterion == 't' else len(total_path)
    return total_path, final_cost


def run_tabu_search(start_id, stop_ids, start_secs, graph, coords, criterion, algo_func):
    tabu_size = len(stop_ids) * 2
    tabu_list = deque(maxlen=tabu_size)
    
    current_sol = list(stop_ids)
    random.shuffle(current_sol)
    
    best_path, best_cost = get_route_full_details(current_sol, start_id, start_secs, graph, coords, criterion, algo_func)
    best_sol = list(current_sol)

    for k in range(50):
        neighbors = []
        for i in range(len(current_sol)):
            for j in range(i + 1, len(current_sol)):
                neighbor = list(current_sol)
                neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
                neighbors.append(tuple(neighbor))
        
        if len(neighbors) > 10:
            neighbors = random.sample(neighbors, 10)

        best_neighbor = None
        min_neighbor_cost = float('inf')

        for neighbor in neighbors:
            n_path, n_cost = get_route_full_details(neighbor, start_id, start_secs, graph, coords, criterion, algo_func)
            
            if neighbor not in tabu_list or n_cost < best_cost:
                if n_cost < min_neighbor_cost:
                    min_neighbor_cost = n_cost
                    best_neighbor = neighbor

        if best_neighbor:
            current_sol = list(best_neighbor)
            tabu_list.append(best_neighbor)
            if min_neighbor_cost < best_cost:
                best_cost = min_neighbor_cost
                best_sol = list(current_sol)
                best_path = n_path

    return best_path, best_cost
