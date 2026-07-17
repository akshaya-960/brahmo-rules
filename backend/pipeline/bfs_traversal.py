"""
BFS Traversal
Walks the hierarchy DAG in both directions from the entry point, then
expands downward again from same-department ancestors so sibling
units (e.g. TKR Unit) under the same department root are reachable.
"""
from collections import deque, defaultdict

def bfs_traverse(entry_level_id: str, hierarchy_levels: list) -> dict:
    """Returns {level_id: distance_from_entry} for every reachable level."""
    levels_by_id = {h["id"]: h for h in hierarchy_levels}
    children_by_id = defaultdict(list)
    for h in hierarchy_levels:
        for parent_id in (h.get("parent_ids") or []):
            children_by_id[parent_id].append(h["id"])

    distances = {entry_level_id: 0}
    visited = {entry_level_id}

    # ---- Phase 1: walk UP via parent_ids (ancestors) ----
    queue = deque([entry_level_id])
    while queue:
        current_id = queue.popleft()
        current = levels_by_id.get(current_id)
        if not current:
            continue
        for parent_id in (current.get("parent_ids") or []):
            if parent_id in visited:
                continue
            visited.add(parent_id)
            distances[parent_id] = distances[current_id] + 1
            queue.append(parent_id)

    # ---- Phase 2: walk DOWN via children ----
    # Seed from entry point AND from any ancestor sharing entry's department
    # (reaches sibling units like TKR Unit under the same department root),
    # but NOT from department=None ancestors (Clinical Division, Hospital
    # root) -- that would leak other departments' entire subtrees.
    entry_department = levels_by_id.get(entry_level_id, {}).get("department")
    down_seeds = [entry_level_id]
    for level_id in list(distances.keys()):
        if level_id == entry_level_id:
            continue
        level = levels_by_id.get(level_id)
        if level and entry_department is not None and level.get("department") == entry_department:
            down_seeds.append(level_id)

    queue = deque(down_seeds)
    while queue:
        current_id = queue.popleft()
        for child_id in children_by_id.get(current_id, []):
            if child_id in visited:
                continue
            visited.add(child_id)
            distances[child_id] = distances[current_id] + 1
            queue.append(child_id)

    return distances
