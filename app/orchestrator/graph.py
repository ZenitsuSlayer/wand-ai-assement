from __future__ import annotations
from typing import Dict, List, Set, Tuple
from app.models import WorkflowSpec

def build_graph(spec: WorkflowSpec) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    adj: Dict[str, List[str]] = {n.id: [] for n in spec.nodes}
    indeg: Dict[str, int] = {n.id: 0 for n in spec.nodes}
    for e in spec.edges:
        if e.source not in adj or e.target not in adj:
            raise ValueError(f"Edge references unknown node: {e.source}->{e.target}")
        adj[e.source].append(e.target)
        indeg[e.target] += 1
    return adj, indeg

def topo_levels(adj: Dict[str, List[str]], indeg: Dict[str, int]) -> List[List[str]]:
    # Kahn's algorithm, return levels for parallel execution
    zero = [n for n, d in indeg.items() if d == 0]
    levels: List[List[str]] = []
    while zero:
        level = list(zero)
        levels.append(level)
        next_zero: List[str] = []
        for u in level:
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    next_zero.append(v)
        zero = next_zero
    # Validate no cycles
    if any(d > 0 for d in indeg.values()):
        raise ValueError("Graph has cycles; DAG required.")
    return levels
