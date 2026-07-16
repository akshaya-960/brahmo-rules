"""
Candidate Set Assembler
Annotates surviving nodes with the metadata the downstream Composition Agent needs.
"""

def assemble_candidates(nodes: list, distance_map: dict) -> list:
    candidates = []
    for n in nodes:
        dist = distance_map.get(n["id"], 0)
        if dist <= 1:
            hint = "FULL"
        elif dist == 2:
            hint = "COMPRESSED"
        else:
            hint = "CONSTRAINT_ONLY"
        candidates.append({
            "id": n["id"],
            "type": n["type"],
            "title": n["title"],
            "content": n["content"],
            "importance": float(n["importance"]),
            "zone": n["zone"],
            "hierarchy_level_id": n["hierarchy_level_id"],
            "department": n.get("department"),
            "distance_from_entry": dist,
            "compression_hint": hint,
        })
    candidates.sort(key=lambda c: (-c["importance"], c["distance_from_entry"]))
    return candidates
