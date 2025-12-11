# A simple A* itinerary planner over a flight network.
# Now supports rich flight details.

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Any

INF = float("inf")

def load_graph_from_files(files: Iterable[Path]) -> Dict[str, Dict[str, dict]]:
    """Load a weighted DIRECTED graph from flight JSON files.
    
    Nodes: IATA airport codes.
    Edges: Directed connection with 'weight' (Kilometers) and 'data' (flight record).
    """
    graph: Dict[str, Dict[str, dict]] = {}

    def add_edge(a: str, b: str, w_km: float, record: dict) -> None:
        if not a or not b:
            return
        if a == b:
            return
        
        graph.setdefault(a, {})
        
        # We just use the raw Kilometer value for the weight
        current_edge = graph[a].get(b)
        if current_edge is None or w_km < current_edge['weight']:
            graph[a][b] = {'weight': w_km, 'data': record}

    for f in files:
        if not f.exists():
            continue
        try:
            text = f.read_text(encoding="utf-8")
            if not text.strip(): continue
            data = json.loads(text)
        except Exception as e:
            print(f"Failed to read {f}: {e}", file=sys.stderr)
            continue

        if not isinstance(data, list):
            continue

        for rec in data:
            try:
                a = rec.get("orig_iata") or rec.get("orig_icao")
                b = rec.get("dest_iata") or rec.get("dest_icao")
                
                # Read the raw distance (which is already in KM)
                dist_km = rec.get("circle_distance") or rec.get("actual_distance")
                
                if a and b and isinstance(dist_km, (int, float)):
                    # Store it directly. No conversion, no copying needed.
                    add_edge(a, b, float(dist_km), rec)
            except Exception:
                continue

    return graph


def dijkstra(graph: Dict[str, Dict[str, dict]], src: str) -> Dict[str, float]:
    dist: Dict[str, float] = {src: 0.0}
    pq: List[Tuple[float, str]] = [(0.0, src)]
    
    while pq:
        d, node = heapq.heappop(pq)
        if d > dist.get(node, INF):
            continue
        
        # nb is neighbor, edge_info contains {'weight': ..., 'data': ...}
        for nb, edge_info in graph.get(node, {}).items():
            w = edge_info['weight']
            nd = d + w
            if nd < dist.get(nb, INF):
                dist[nb] = nd
                heapq.heappush(pq, (nd, nb))
    return dist


def pairwise_shortest_paths(graph: Dict[str, Dict[str, dict]], nodes: Iterable[str]) -> Dict[Tuple[str, str], float]:
    nodes = list(nodes)
    pw: Dict[Tuple[str, str], float] = {}
    for i, n in enumerate(nodes):
        dist = dijkstra(graph, n)
        for m in nodes:
            pw[(n, m)] = dist.get(m, INF)
    return pw


def mst_cost_on_complete_graph(nodes: List[str], pairwise: Dict[Tuple[str, str], float]) -> float:
    if not nodes:
        return 0.0
    visited = set()
    total = 0.0
    start = nodes[0]
    visited.add(start)
    
    keys: Dict[str, float] = {n: INF for n in nodes}
    for n in nodes:
        if n == start:
            keys[n] = 0.0
        else:
            keys[n] = pairwise.get((start, n), INF)

    while len(visited) < len(nodes):
        cand = None
        cand_w = INF
        for n in nodes:
            if n in visited:
                continue
            if keys[n] < cand_w:
                cand_w = keys[n]
                cand = n
        if cand is None or cand_w == INF:
            return INF
        visited.add(cand)
        total += cand_w
        
        for n in nodes:
            if n in visited:
                continue
            w = pairwise.get((cand, n), INF)
            if w < keys[n]:
                keys[n] = w

    return total


def heuristic_mst(graph: Dict[str, Dict[str, dict]], current: str, remaining: Set[str]) -> float:
    if not remaining:
        return 0.0
    nodes = list(remaining)
    pairwise = pairwise_shortest_paths(graph, nodes)
    mst = mst_cost_on_complete_graph(nodes, pairwise)
    
    dist_from_current = dijkstra(graph, current)
    min_to_rem = min((dist_from_current.get(n, INF) for n in nodes), default=INF)
    
    if mst == INF or min_to_rem == INF:
        return INF
    return mst + min_to_rem


def a_star_visit_all(graph: Dict[str, Dict[str, dict]], start: str, targets: Set[str],
                     max_iterations: int = 200_000, time_limit: float = 10.0) -> Optional[Tuple[List[str], float]]:
    start = start.upper()
    targets = {t.upper() for t in targets}
    
    if start not in graph:
        # Check if start exists in the graph at all (maybe only as a destination)
        # But for A* we need outgoing edges from start
        pass 

    initial_visited = frozenset([start]) if start in targets else frozenset()
    
    def is_goal(visited: frozenset) -> bool:
        return targets.issubset(set(visited))

    # priority queue entries: (f, g, node, visited_frozenset, path)
    pq: List[Tuple[float, float, str, frozenset, List[str]]] = []
    
    # Calculate initial heuristic
    remaining_targets = set(targets) - set(initial_visited)
    h0 = heuristic_mst(graph, start, remaining_targets)
    
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

        if g > best_g.get((node, visited), INF):
            continue

        # Look at neighbors
        for nb, edge_info in graph.get(node, {}).items():
            w = edge_info['weight']
            ng = g + w
            
            nvisited = set(visited)
            if nb in targets:
                nvisited.add(nb)
            nvisited_fs = frozenset(nvisited)
            
            key = (nb, nvisited_fs)
            if ng + 1e-9 >= best_g.get(key, INF):
                continue
                
            remaining = set(targets) - set(nvisited)
            h = heuristic_mst(graph, nb, remaining)
            if h == INF:
                continue
                
            best_g[key] = ng
            heapq.heappush(pq, (ng + h, ng, nb, nvisited_fs, path + [nb]))

    return None


def compute_itinerary(start: str, targets: Iterable[str], max_iterations: int = 200_000,
                      time_limit: float = 10.0) -> Optional[Tuple[List[str], List[dict], float]]:
    """
    Returns (path_of_airport_codes, path_of_flight_details, total_cost)
    """
    base = Path(__file__).parent
    files = [base / "connecting_flights.json", base / "socal_direct_flights.json"]
    graph = load_graph_from_files(files)

    targets = list({t.strip().upper() for t in targets if t})
    start = start.strip().upper()

    result = a_star_visit_all(graph, start, set(targets), max_iterations=max_iterations, time_limit=time_limit)
    
    if result is None:
        return None
        
    path_nodes, cost = result
    
    # Reconstruct detailed flight path
    detailed_path = []
    for i in range(len(path_nodes) - 1):
        u, v = path_nodes[i], path_nodes[i+1]
        edge_data = graph[u][v]['data']
        detailed_path.append(edge_data)
        
    return path_nodes, detailed_path, cost

def main():
    # Simple CLI wrapper
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True)
    parser.add_argument("--targets", required=True, nargs="+")
    args = parser.parse_args()
    
    res = compute_itinerary(args.start, args.targets)
    if res:
        print("Path:", " -> ".join(res[0]))
        print("Cost:", res[2])
    else:
        print("No path found.")

if __name__ == "__main__":
    main()