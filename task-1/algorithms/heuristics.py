import math

def haversine_distance(coords1, coords2):
    lat1, lon1 = float(coords1['stop_lat']), float(coords1['stop_lon'])
    lat2, lon2 = float(coords2['stop_lat']), float(coords2['stop_lon'])

    if lat1 == 0 or lat2 == 0:
        return 0.0

    R = 6371 
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(d_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
    
def get_heuristic(curr_stop_id, end_stop_id, coords, mode='t'):
    if mode == 'p' or curr_stop_id not in coords or end_stop_id not in coords:
        return 0
    distance_km = haversine_distance(coords[curr_stop_id], coords[end_stop_id])
    return (distance_km / 120) * 3600