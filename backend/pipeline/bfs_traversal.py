"""
BFS Traversal
Walks UP the hierarchy DAG from the entry point via parent_ids.
Visited set prevents re-processing multi-parent nodes and blocks cycles.
"""
from collections import deque


def bfs_traverse(entry_level_id: str, hierarchy_levels: list) -> dict:
    """Returns {level_id: distance_from_entry} for every reachable level."""
    levels_by_id = {h["id"]: h for h in hierarchy_levels}
    distances = {entry_level_id: 0}
    visited = {entry_level_id}
    queue = deque([entry_level_id])

    while queue:
        current_id = queue.popleft()
        current = levels_by_id.get(current_id)
        if not current:
            continue
        for parent_id in current.get("parent_ids") or []:
            if parent_id in visited:
                continue  # visited set -> no re-processing, no infinite loop on a cycle
            visited.add(parent_id)
            distances[parent_id] = distances[current_id] + 1
            queue.append(parent_id)

    return distances
