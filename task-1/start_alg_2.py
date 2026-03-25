import sys
import time
from datetime import datetime
from pathlib import Path
import pandas as pd

# Importy Twoich modułów
from graph.prepare import prepare_data_for_astar
from algorithms.dijkstra import dijkstra 
from loaders.loader import load_gtfs
from utils.time_utils import time_to_seconds, secs_to_time

def parse_arguments():
    """Pobiera i wstępnie waliduje argumenty z linii komend."""
    if len(sys.argv) < 5:
        print("Użycie: python start_alg.py <A> <B> <t/p> <HH:MM:SS> [RRRRMMDD]", file=sys.stderr)
        sys.exit(1)

    return {
        "stop_a": sys.argv[1],
        "stop_b": sys.argv[2],
        "criterion": sys.argv[3],
        "start_time": sys.argv[4],
        "date": sys.argv[5] if len(sys.argv) > 5 else "20260303"
    }

def resolve_stop_ids(stop_name, stops_df, graph):
    """
    Mapuje nazwę przystanku na ID. 
    Wybiera ID, które faktycznie istnieje w grafie (obsługa peronów).
    """
    all_ids = stops_df[stops_df['stop_name'] == stop_name]['stop_id'].astype(str).tolist()
    
    # Szukamy pierwszego ID z listy, które ma jakiekolwiek krawędzie wychodzące w grafie
    valid_ids = [s_id for s_id in all_ids if s_id in graph]
    
    if not valid_ids:
        return all_ids[0] if all_ids else None # Fallback do pierwszego lepszego
    return valid_ids[0]

def print_route(path, id_to_name):
    """Wypisuje sformatowaną trasę na stdout."""
    print(f"\n{'Z przystanku':<30} | {'Linia':<10} | {'Odjazd':<10} | {'Przyjazd':<10}")
    print("-" * 75)
    
    last_stop = None
    for step in path:
        name = id_to_name.get(step['from_stop'], step['from_stop'])
        
        # Opcjonalne: Pominięcie powielonych transferów w tym samym miejscu dla czytelności
        if step['line'] == 'WALK' and name == last_stop:
            continue
            
        print(f"{name:<30} | {step['line']:<10} | {secs_to_time(step['dep']):<10} | {secs_to_time(step['arr']):<10}")
        last_stop = name

def print_metrics(path, start_secs, calc_duration, criterion):
    """Wypisuje metryki wykonania na stderr."""
    if not path:
        return
    
    final_arrival = path[-1]['arr']
    total_time = final_arrival - start_secs
    
    print(f"\n--- METRYKI ---", file=sys.stderr)
    print(f"Kryterium ({criterion}): {total_time}s", file=sys.stderr)
    print(f"Czas obliczeń: {calc_duration:.4f}s", file=sys.stderr)

def run_transport_search():
    """Główna orkiestracja procesu."""
    args = parse_arguments()
    data_path = "google_transit/"

    # 1. Inicjalizacja danych
    print(f"Przygotowanie grafu dla daty {args['date']}...", file=sys.stderr)
    final_graph, coords = prepare_data_for_astar(data_path, args['date'])
    gtfs_data = load_gtfs(data_path)
    
    # 2. Mapowanie nazw na ID
    id_a = resolve_stop_ids(args['stop_a'], gtfs_data["stops"], final_graph)
    id_b = resolve_stop_ids(args['stop_b'], gtfs_data["stops"], final_graph)

    if not id_a or not id_b:
        missing = args['stop_a'] if not id_a else args['stop_b']
        print(f"Błąd: Nie znaleziono przystanku '{missing}' w bazie danych.", file=sys.stderr)
        return

    # 3. Obliczenia
    start_secs = time_to_seconds(args['start_time'])
    print(f"Szukanie połączenia ({args['criterion']})...", file=sys.stderr)
    
    start_calc = time.time()
    # Tutaj przesyłamy criterion, aby Dijkstra wiedziała czy naliczać karę za przesiadkę
    path = dijkstra(final_graph, id_a, id_b, start_secs, mode=args['criterion'])
    calc_duration = time.time() - start_calc

    # 4. Wyświetlanie wyników
    if path:
        id_to_name = gtfs_data["stops"].set_index('stop_id')['stop_name'].to_dict()
        print_route(path, id_to_name)
        print_metrics(path, start_secs, calc_duration, args['criterion'])
    else:
        print(f"Nie znaleziono połączenia między '{args['stop_a']}' a '{args['stop_b']}'.", file=sys.stderr)

if __name__ == "__main__":
    run_transport_search()