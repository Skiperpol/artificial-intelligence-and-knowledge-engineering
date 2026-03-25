import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Importy Twoich modułów
from graph.prepare import prepare_data_for_astar
from algorithms.dijkstra import dijkstra 
from loaders.loader import load_gtfs # Potrzebne do wczytania nazw przystanków
from utils.time_utils import time_to_seconds, secs_to_time
from algorithms.astar import a_star
from algorithms.weighted_astar import weighted_astar
def main():
    # 1. Sprawdzenie argumentów wejściowych [cite: 211, 223]
    if len(sys.argv) < 5:
        print("Użycie: python start_alg.py <Przystanek_A> <Przystanek_B> <t/p> <HH:MM:SS> [RRRRMMDD] [astar/dijkstra/weighted_astar]", file=sys.stderr)
        return

    stop_a_name = sys.argv[1]    # Nazwa przystanku A [cite: 147, 212]
    stop_b_name = sys.argv[2]    # Nazwa przystanku B [cite: 147, 213]
    criterion = sys.argv[3]      # t (czas) lub p (przesiadki) 
    start_time_str = sys.argv[4] # Czas startu [cite: 215]
    date_str = sys.argv[5] if len(sys.argv) > 5 else "20260303" # [cite: 116, 188]

    if criterion not in ['t', 'p']:
        print("Błąd: Kryterium musi być 't' (czas) lub 'p' (przesiadki).", file=sys.stderr)
        return

    # 2. Przygotowanie danych i grafu [cite: 190, 191]
    print(f"Ładowanie danych i budowa grafu...", file=sys.stderr)
    # final_graph musi być przygotowany pod konkretną datę [cite: 206, 207]
    final_graph, coords = prepare_data_for_astar("google_transit/", date_str)
    
    # Musimy załadować stops.txt, aby zamienić nazwy na ID [cite: 142, 145]
    gtfs_data = load_gtfs("google_transit/")
    stops_df = gtfs_data["stops"]

    # 3. Mapowanie nazw na ID [cite: 145, 147]
    # Szukamy wszystkich ID odpowiadających danej nazwie (np. różne perony tej samej stacji) 
    def get_stop_ids(name, df):
        ids = df[df['stop_name'] == name]['stop_id'].astype(str).tolist()
        return ids

    ids_a = get_stop_ids(stop_a_name, stops_df)
    ids_b = get_stop_ids(stop_b_name, stops_df)

    if not ids_a or not ids_b:
        print(f"Nie znaleziono przystanku: {stop_a_name if not ids_a else stop_b_name}", file=sys.stderr)
        return

    start_secs = time_to_seconds(start_time_str)
    algo_type = sys.argv[6] if len(sys.argv) > 6 else "astar" # Domyślnie A*
    # 4. Uruchomienie algorytmu [cite: 218, 219]
    # W Twojej Dijkstrze musisz obsłużyć karę za przesiadkę jeśli criterion == 'p' [cite: 220]
    start_calc = time.time()
    
    # Ponieważ stacja może mieć wiele ID (peronów), najprościej sprawdzić pierwszy 
    # lub zmodyfikować Dijkstrę by przyjmowała listę startową [cite: 143, 193]
    if algo_type == "astar":
        print(f"Uruchamiam A* (kryterium: {criterion})...", file=sys.stderr)
        path, total_cost, visited_nodes = a_star(final_graph, ids_a[0], ids_b[0], start_secs, coords, criterion)
    elif algo_type == "weighted_astar":
        print(f"Uruchamiam Weighted A* (kryterium: {criterion})...", file=sys.stderr)
        path, total_cost, visited_nodes = weighted_astar(final_graph, ids_a[0], ids_b[0], start_secs, coords, criterion)
    else:
        print(f"Uruchamiam Dijkstrę (kryterium: {criterion})...", file=sys.stderr)
        path, total_cost, visited_nodes = dijkstra(final_graph, ids_a[0], ids_b[0], start_secs, criterion)
    calc_duration = time.time() - start_calc

    # 5. Wyniki [cite: 216]
    if not path:
        print(f"Nie znaleziono połączenia.", file=sys.stderr)
        return

    # Wyjście standardowe (szczegóły trasy) [cite: 216]
    print(f"{'Z przystanku':<30} | {'Linia':<10} | {'Odjazd':<10} | {'Przyjazd':<10}")
    print("-" * 75)
    
    # Tworzymy mapę ID -> Nazwa dla czytelnego wydruku [cite: 145, 147]
    id_to_name = stops_df.set_index('stop_id')['stop_name'].to_dict()

    for step in path:
        name = id_to_name.get(step['from_stop'], step['from_stop'])
        print(f"{name:<30} | {step['line']:<10} | {secs_to_time(step['dep']):<10} | {secs_to_time(step['arr']):<10}")

    # Wyjście błędów (metryki) [cite: 216]
    final_arrival = path[-1]['arr']
    print(f"--- METRYKI WYDAJNOŚCI ---", file=sys.stderr)
    print(f"Algorytm: {algo_type.upper()}", file=sys.stderr)
    print(f"Odwiedzone stany (wierzchołki): {visited_nodes}", file=sys.stderr)
    print(f"Czas obliczeń: {calc_duration:.4f}s", file=sys.stderr)
    print(f"Wartość kryterium: {total_cost - start_secs} (jednostki kosztu)", file=sys.stderr)


if __name__ == "__main__":
    main()