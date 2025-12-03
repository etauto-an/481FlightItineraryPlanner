# A simple A* itinerary planner over a flight network.

# This program builds a weighted undirected graph from the provided
# flight JSON files (`connecting_flights.json` and
# `socal_direct_flights.json` - on the future it may use an api) and 
# searches the state-space of (current_airport, visited_targets) to find 
# a minimum-distance route visiting all user-specified destinations using A*.

# Heuristic: MST over remaining targets (using shortest-path distances)
# plus the distance from the current node to the closest remaining
# target. This is admissible and helps prune the search.

# NOTE: max-iterations and time-limit are optional.

# Usage example 1:
#   python main.py --start LAX --targets SFO DEN PHX --max-iterations 100000 --time-limit 5.0
    
# Usage example 2 (as API):
#   from backend.main import compute_itinerary
#     path, cost = compute_itinerary("LAX", ["SFO", "DEN", "PHX"], max_iterations=100000, time_limit=5.0)
#     print("Itinerary:", path)
#     print("Total distance:", cost)


from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

INF = float("inf")

def load_graph_from_files(files: Iterable[Path]) -> Dict[str, Dict[str, float]]:
    """Load a weighted undirected graph from flight JSON files.

    Nodes are IATA airport codes. Edge weight is the minimum
    `circle_distance` observed between two airports across the files.
    """
    graph: Dict[str, Dict[str, float]] = {}

    def add_edge(a: str, b: str, w: float) -> None:
        if not a or not b:
            return
        if a == b:
            return
        graph.setdefault(a, {})
        graph.setdefault(b, {})
        prev = graph[a].get(b)
        if prev is None or w < prev:
            graph[a][b] = w
            graph[b][a] = w

    for f in files:
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Failed to read {f}: {e}", file=sys.stderr)
            continue

        if not isinstance(data, list):
            continue

        for rec in data:
            try:
                a = rec.get("orig_iata") or rec.get("orig_icao")
                b = rec.get("dest_iata") or rec.get("dest_icao")
                w = rec.get("circle_distance") or rec.get("actual_distance")
                if a and b and isinstance(w, (int, float)):
                    add_edge(a, b, float(w))
            except Exception:
                continue

    return graph


def dijkstra(graph: Dict[str, Dict[str, float]], src: str) -> Dict[str, float]:
    dist: Dict[str, float] = {src: 0.0}
    pq: List[Tuple[float, str]] = [(0.0, src)]
    while pq:
        d, node = heapq.heappop(pq)
        if d > dist.get(node, INF):
            continue
        for nb, w in graph.get(node, {}).items():
            nd = d + w
            if nd < dist.get(nb, INF):
                dist[nb] = nd
                heapq.heappush(pq, (nd, nb))
    return dist


def pairwise_shortest_paths(graph: Dict[str, Dict[str, float]], nodes: Iterable[str]) -> Dict[Tuple[str, str], float]:
    nodes = list(nodes)
    pw: Dict[Tuple[str, str], float] = {}
    for i, n in enumerate(nodes):
        dist = dijkstra(graph, n)
        for m in nodes:
            pw[(n, m)] = dist.get(m, INF)
    return pw


def mst_cost_on_complete_graph(nodes: List[str], pairwise: Dict[Tuple[str, str], float]) -> float:
    """Compute MST cost (Prim) on a complete graph whose edge weights are
    provided in `pairwise` mapping. Returns INF if graph disconnected.
    """
    if not nodes:
        return 0.0
    visited = set()
    total = 0.0
    # start from first node
    start = nodes[0]
    visited.add(start)
    # maintain min edge to the growing tree
    import math as _m

    keys: Dict[str, float] = {n: _m.inf for n in nodes}
    for n in nodes:
        if n == start:
            keys[n] = 0.0
        else:
            keys[n] = pairwise.get((start, n), _m.inf)

    while len(visited) < len(nodes):
        # pick node with smallest key not in visited
        cand = None
        cand_w = _m.inf
        for n in nodes:
            if n in visited:
                continue
            if keys[n] < cand_w:
                cand_w = keys[n]
                cand = n
        if cand is None or cand_w == _m.inf:
            return INF
        visited.add(cand)
        total += cand_w
        # update keys
        for n in nodes:
            if n in visited:
                continue
            w = pairwise.get((cand, n), _m.inf)
            if w < keys[n]:
                keys[n] = w

    return total


def heuristic_mst(graph: Dict[str, Dict[str, float]], current: str, remaining: Set[str]) -> float:
    """Admissible heuristic: MST over remaining nodes + min edge from
    current to any remaining node (using shortest-path distances).
    """
    if not remaining:
        return 0.0
    nodes = list(remaining)
    pairwise = pairwise_shortest_paths(graph, nodes)
    mst = mst_cost_on_complete_graph(nodes, pairwise)
    # distance from current to closest remaining (shortest path)
    dist_from_current = dijkstra(graph, current)
    min_to_rem = min((dist_from_current.get(n, INF) for n in nodes), default=INF)
    if mst == INF or min_to_rem == INF:
        return INF
    return mst + min_to_rem


def a_star_visit_all(graph: Dict[str, Dict[str, float]], start: str, targets: Set[str],
                     max_iterations: int = 200_000, time_limit: float = 10.0) -> Optional[Tuple[List[str], float]]:
    """A* search over states (node, visited_set). Returns (path, cost)
    visiting all `targets` in any order starting at `start`.
    """
    start = start.upper()
    targets = {t.upper() for t in targets}
    if start not in graph:
        raise ValueError(f"Start airport '{start}' not in graph")
    for t in targets:
        if t not in graph:
            raise ValueError(f"Target airport '{t}' not in graph")

    initial_visited = frozenset([start]) if start in targets else frozenset()
    init_state = (start, initial_visited)

    def is_goal(visited: frozenset) -> bool:
        return targets.issubset(set(visited))

    # priority queue entries: (f, g, node, visited_frozenset, path)
    pq: List[Tuple[float, float, str, frozenset, List[str]]] = []
    h0 = heuristic_mst(graph, start, set(targets) - set(initial_visited))
    heapq.heappush(pq, (h0, 0.0, start, initial_visited, [start]))

    best_g: Dict[Tuple[str, frozenset], float] = {(start, initial_visited): 0.0}
    iterations = 0
    t0 = time.time()

    while pq:
        if iterations >= max_iterations:
            print("Reached max iterations", file=sys.stderr)
            return None
        if time.time() - t0 > time_limit:
            print("Time limit exceeded", file=sys.stderr)
            return None

        f, g, node, visited, path = heapq.heappop(pq)
        iterations += 1

        if is_goal(visited):
            return path, g

        # if we have a better g recorded, skip
        if g > best_g.get((node, visited), INF):
            continue

        for nb, w in graph.get(node, {}).items():
            ng = g + w
            nvisited = set(visited)
            if nb in targets:
                nvisited.add(nb)
            nvisited_fs = frozenset(nvisited)
            key = (nb, nvisited_fs)
            if ng + 1e-9 >= best_g.get(key, INF):
                continue
            # compute heuristic
            remaining = set(targets) - set(nvisited)
            h = heuristic_mst(graph, nb, remaining)
            if h == INF:
                continue
            best_g[key] = ng
            heapq.heappush(pq, (ng + h, ng, nb, nvisited_fs, path + [nb]))

    return None


def find_itinerary(start: str, targets: Iterable[str], max_iterations: int = 200_000,
                   time_limit: float = 10.0) -> None:
    base = Path(__file__).parent
    files = [base / "connecting_flights.json", base / "socal_direct_flights.json"]
    graph = load_graph_from_files(files)

    targets = list({t.strip().upper() for t in targets if t})
    start = start.strip().upper()

    path_and_cost = a_star_visit_all(graph, start, set(targets), max_iterations=max_iterations, time_limit=time_limit)
    if path_and_cost is None:
        print("No solution found (iteration/time limit or disconnected graph).")
        return
    path, cost = path_and_cost
    print("Found itinerary:")
    print(" -> ".join(path))
    print(f"Total distance: {cost:.1f} (nautical miles as reported in data)")


def compute_itinerary(start: str, targets: Iterable[str], max_iterations: int = 200_000,
                      time_limit: float = 10.0) -> Optional[Tuple[List[str], float]]:
    """Programmatic entrypoint for the itinerary planner.

    Returns (path, cost) or `None` if no solution found in limits.
    Raises ValueError for invalid airports.
    """
    base = Path(__file__).parent
    files = [base / "connecting_flights.json", base / "socal_direct_flights.json"]
    graph = load_graph_from_files(files)

    targets = list({t.strip().upper() for t in targets if t})
    start = start.strip().upper()

    return a_star_visit_all(graph, start, set(targets), max_iterations=max_iterations, time_limit=time_limit)


def main():
    parser = argparse.ArgumentParser(description="A* itinerary planner over flight graph")
    parser.add_argument("--start", required=True, help="Start airport IATA code (e.g., LAX)")
    parser.add_argument("--targets", required=True, nargs="+", help="Target airport IATA codes to visit")
    parser.add_argument("--max-iterations", type=int, default=200_000, help="Max A* iterations")
    parser.add_argument("--time-limit", type=float, default=10.0, help="Time limit (seconds) for search")
    args = parser.parse_args()

    try:
        find_itinerary(args.start, args.targets, max_iterations=args.max_iterations, time_limit=args.time_limit)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
