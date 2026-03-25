import pandas as pd
import math


def build_coords_dict(stops: pd.DataFrame) -> dict[str, dict[str, float]]:
    coords = stops.set_index("stop_id")[["stop_lat", "stop_lon"]].to_dict("index")
    return coords

def haversine_distance(lat1, lon1, lat2, lon2):
    # Przelicznik stopnia na metry (w przybliżeniu dla Polski)
    # 1 stopień szerokości to ok. 111 km
    # 1 stopień długości (na poziomie Wrocławia) to ok. 70 km
    d_lat = abs(lat1 - lat2) * 111000
    d_lon = abs(lon1 - lon2) * 70000
    return (d_lat + d_lon) / 22.0  # 22 m/s to ok. 80 km/h

def get_heuristic(current_stop, end_stop, coords, criterion):
    if criterion == 'p':
        return 0  # Gwarantuje najmniejszą liczbę przesiadek
    
    c1 = coords.get(current_stop)
    c2 = coords.get(end_stop)
    if not c1 or not c2: return 0
    
    # Odległość euklidesowa w rzucie płaskim (szybka)
    dist = math.sqrt(((c1['stop_lat'] - c2['stop_lat']) * 111000)**2 + 
                     ((c1['stop_lon'] - c2['stop_lon']) * 70000)**2)
    
    # WAŻNE: Mnożnik (Weight A*). 
    # Wartość 1.0 = klasyczny A* (optymalny)
    # Wartość 1.5 = szybszy, ale może nieznacznie ominąć ideał
    weight = 1.1 
    
    return (dist / 25.0) * weight # 25 m/s = 90 km/h (KD jeżdżą szybko)