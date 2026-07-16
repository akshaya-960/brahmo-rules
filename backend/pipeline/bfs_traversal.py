"""
BFS Traversal
Walks the hierarchy DAG in BOTH directions from the entry point:
  - UPWARD via parent_ids (ancestors) -- broader/more general context,
    e.g. a ward nurse gains visibility into her department's and the
    hospital's cross-cutting policies as she "climbs" the tree.
  - DOWNWARD via each node's own children (descendants of the ENTRY POINT
    ONLY) -- more specific context that structurally sits below the user's
    own position, e.g. a department HOD sees every ward/unit/patient node
    beneath their department root, not just the path up to the hospital.

CRITICAL: downward expansion starts ONLY from the entry point itself and
never cascades further downward from an ancestor discovered during upward
traversal. Without this restriction, climbing to a shared ancestor (e.g.
"Clinical Division") would incorrectly unlock every sibling department's
entire subtree (Medicine, Cardiology, Paediatrics, etc), breaking
department isolation. Ancestors are included as single nodes, not as
whole subtrees.

This also fixes a structural edge case: when a user's entry point IS the
hospital root (e.g. ADMIN, or any role whose department has no dedicated
DAG node and falls back to root), pure upward-only traversal would reach
almost nothing, since the root has no parents to walk to. Downward
expansion from the root correctly reaches the entire graph -- which is
exactly the intended behavior for an admin sitting at the top of the
hierarchy.

Visited set prevents re-processing multi-parent nodes and blocks cycles
in both directions.
"""
from collections import deque, defaultdict


def bfs_traverse(entry_level_id: str, hierarchy_levels: list) -> dict:
    """Returns {level_id: distance_from_entry} for every reachable level."""
    levels_by_id = {h["id"]: h for h in hierarchy_levels}

    # Reverse index: parent_id -> [child_ids], built once per call.
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

    # ---- Phase 2: walk DOWN via children, starting ONLY from entry ----
    # (never from ancestors found in Phase 1 -- that would leak sibling
    # departments' entire subtrees through a shared ancestor.)
    queue = deque([entry_level_id])
    while queue:
        current_id = queue.popleft()
        for child_id in children_by_id.get(current_id, []):
            if child_id in visited:
                continue
            visited.add(child_id)
            distances[child_id] = distances[current_id] + 1
            queue.append(child_id)

    return distances
