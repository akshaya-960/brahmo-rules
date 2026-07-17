"""
Zone 2 Injector
Adds hospital-wide GLOBAL nodes (zone=2) into the BFS-reachable set.
They arrive regardless of traversal path, but still go through all 5 checks.
"""

def inject_zone2(node_map: dict, distance_map: dict, zone2_nodes: list, level_distances: dict) -> None:
    """Mutates node_map / distance_map in place, adding any zone-2 node not already present."""
    max_dist = max(distance_map.values(), default=0)
    for n in zone2_nodes:
        if n["id"] in node_map:
            continue
        node_map[n["id"]] = n
        # If its hierarchy level is already on the BFS path, reuse that distance.
        # Otherwise it arrives "sideways" via injection -> place just past the furthest BFS node.
        distance_map[n["id"]] = level_distances.get(n["hierarchy_level_id"], max_dist + 1)
