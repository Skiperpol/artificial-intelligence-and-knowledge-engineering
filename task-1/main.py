import sys
import time

from algorithms.astar import a_star
from algorithms.dijkstra import dijkstra
from algorithms.tabu_search import run_tabu_search
from algorithms.weighted_astar import weighted_astar
from graph.prepare import prepare_data_for_astar
from loaders.loader import load_gtfs
from utils.time_utils import secs_to_time, time_to_seconds

DEFAULT_GTFS_FOLDER = "google_transit/"
DEFAULT_DATE_STR = "20260303"
ALLOWED_CRITERIA = {"t", "p"}
ALLOWED_ALGOS = {"astar", "dijkstra", "weighted_astar"}


def parse_cli_args(argv: list[str]) -> dict | None:
    if len(argv) < 4:
        print(
            "Użycie: python start_alg.py <Przystanek_A> <Przystanek_B> <t/p> <HH:MM:SS> "
            "[RRRRMMDD] [astar/dijkstra/weighted_astar]",
            file=sys.stderr,
        )
        return None

    stop_a_name = argv[0]
    stop_b_name = argv[1]
    criterion = argv[2]
    start_time_str = argv[3]
    date_str = argv[4] if len(argv) > 4 else DEFAULT_DATE_STR
    algo_type = argv[5] if len(argv) > 5 else "astar"

    if criterion not in ALLOWED_CRITERIA:
        print("Błąd: Kryterium musi być 't' (czas) lub 'p' (przesiadki).", file=sys.stderr)
        return None

    if algo_type not in ALLOWED_ALGOS:
        print(
            f"Błąd: Nieznany algorytm '{algo_type}'. Dozwolone: {sorted(ALLOWED_ALGOS)}.",
            file=sys.stderr,
        )
        return None

    start_secs = time_to_seconds(start_time_str)
    if start_secs is None:
        print("Błąd: Niepoprawny format czasu startu (oczekiwane HH:MM:SS).", file=sys.stderr)
        return None

    return {
        "stop_a_name": stop_a_name,
        "stop_b_name": stop_b_name,
        "criterion": criterion,
        "start_time_str": start_time_str,
        "date_str": date_str,
        "algo_type": algo_type,
        "start_secs": start_secs,
    }


def get_stop_ids_by_name(name: str, stops_df) -> list[str]:
    ids = stops_df[stops_df["stop_name"] == name]["stop_id"].astype(str).tolist()
    return ids


def parse_tsp_stop_names(stop_b_name: str) -> list[str]:
    return [s.strip() for s in stop_b_name.split(";") if s.strip()]


def resolve_stop_ids_for_tsp(stop_b_name: str, stops_df) -> list[str]:
    stop_names = parse_tsp_stop_names(stop_b_name)
    ids: list[str] = []
    for name in stop_names:
        found = get_stop_ids_by_name(name, stops_df)
        if found:
            ids.append(found[0])
    return ids


def build_graph_and_stops(gtfs_folder: str, date_str: str):
    final_graph, coords = prepare_data_for_astar(gtfs_folder, date_str)
    gtfs_data = load_gtfs(gtfs_folder)
    stops_df = gtfs_data["stops"]
    return final_graph, coords, stops_df


def print_route(path, stops_df) -> None:
    print(f"{'Z przystanku':<30} | {'Linia':<10} | {'Odjazd':<10} | {'Przyjazd':<10}")
    print("-" * 75)

    id_to_name = stops_df.set_index("stop_id")["stop_name"].to_dict()
    for step in path:
        name = id_to_name.get(step["from_stop"], step["from_stop"])
        print(
            f"{name:<30} | {step['line']:<10} | {secs_to_time(step['dep']):<10} | {secs_to_time(step['arr']):<10}"
        )


def run_tsp(start_id: str, stop_ids: list[str], start_secs: int, final_graph, coords, criterion: str):
    if not stop_ids:
        return None, float("inf"), 0.0

    print("Uruchamiam Tabu Search...", file=sys.stderr)
    start_calc = time.time()
    path, total_cost = run_tabu_search(
        start_id, stop_ids, start_secs, final_graph, coords, criterion, weighted_astar
    )
    calc_duration = time.time() - start_calc
    return path, total_cost, calc_duration


def run_single_search(
    algo_type: str,
    final_graph,
    start_id: str,
    end_id: str,
    start_secs: int,
    coords,
    criterion: str,
):
    print(f"Uruchamiam {algo_type} (kryterium: {criterion})...", file=sys.stderr)
    start_calc = time.time()

    if algo_type == "astar":
        path, total_cost, visited_nodes = a_star(final_graph, start_id, end_id, start_secs, coords, criterion)
    elif algo_type == "weighted_astar":
        path, total_cost, visited_nodes = weighted_astar(
            final_graph, start_id, end_id, start_secs, coords, criterion
        )
    else:
        path, total_cost, visited_nodes = dijkstra(final_graph, start_id, end_id, start_secs, criterion)

    calc_duration = time.time() - start_calc
    return path, total_cost, visited_nodes, calc_duration


def print_metrics_single(
    algo_type: str,
    total_cost: float,
    start_secs: int,
    visited_nodes,
    calc_duration: float,
    criterion: str,
) -> None:
    print(f"--- METRYKI WYDAJNOŚCI ---", file=sys.stderr)
    print(f"Algorytm: {algo_type}", file=sys.stderr)
    print(f"Odwiedzone stany (wierzchołki): {visited_nodes}", file=sys.stderr)
    print(f"Czas obliczeń: {calc_duration:.4f}s", file=sys.stderr)
    print(f"Wartość kryterium: {total_cost - start_secs} (jednostki kosztu)", file=sys.stderr)


def print_metrics_tsp(calc_duration: float, total_cost, criterion: str) -> None:
    print(f"--- METRYKI TSP ---", file=sys.stderr)
    print(f"Czas obliczeń: {calc_duration:.4f}s", file=sys.stderr)
    print(f"Łączny koszt ({criterion}): {total_cost}", file=sys.stderr)


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    parsed = parse_cli_args(argv)
    if parsed is None:
        return

    stop_a_name = parsed["stop_a_name"]
    stop_b_name = parsed["stop_b_name"]
    criterion = parsed["criterion"]
    start_secs = parsed["start_secs"]
    date_str = parsed["date_str"]
    algo_type = parsed["algo_type"]

    print("Ładowanie danych i budowa grafu...", file=sys.stderr)
    gtfs_folder = DEFAULT_GTFS_FOLDER
    final_graph, coords, stops_df = build_graph_and_stops(gtfs_folder, date_str)

    ids_a = get_stop_ids_by_name(stop_a_name, stops_df)
    if not ids_a:
        print(f"Nie znaleziono przystanku: {stop_a_name}", file=sys.stderr)
        return

    is_tsp = ";" in stop_b_name
    if is_tsp:
        ids_l = resolve_stop_ids_for_tsp(stop_b_name, stops_df)
        if not ids_l:
            print("Nie znaleziono żadnych przystanków do TSP.", file=sys.stderr)
            return

        path, total_cost, calc_duration = run_tsp(
            ids_a[0], ids_l, start_secs, final_graph, coords, criterion
        )
        if not path:
            print("Nie znaleziono poprawnej trasy TSP (pętli).", file=sys.stderr)
            return

        print_route(path, stops_df)
        print_metrics_tsp(calc_duration, total_cost, criterion)
        return

    ids_b = get_stop_ids_by_name(stop_b_name, stops_df)
    if not ids_b:
        print(f"Nie znaleziono przystanku: {stop_b_name}", file=sys.stderr)
        return

    path, total_cost, visited_nodes, calc_duration = run_single_search(
        algo_type,
        final_graph,
        ids_a[0],
        ids_b[0],
        start_secs,
        coords,
        criterion,
    )

    if not path:
        print("Nie znaleziono połączenia.", file=sys.stderr)
        return

    print_route(path, stops_df)
    print_metrics_single(
        algo_type=algo_type,
        total_cost=total_cost,
        start_secs=start_secs,
        visited_nodes=visited_nodes,
        calc_duration=calc_duration,
        criterion=criterion,
    )


if __name__ == "__main__":
    main()
