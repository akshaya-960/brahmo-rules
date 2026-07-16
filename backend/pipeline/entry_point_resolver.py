"""
Entry Point Resolver
Maps a user to the hierarchy_levels row that is their BFS starting position.
"""

def resolve_entry_point(user: dict, hierarchy_levels: list) -> dict:
    dept = user["department"]
    role = user["role"]

    if role == "ADMIN":
        root = next((h for h in hierarchy_levels if h["level_number"] == 1), None)
        if root:
            return root

    dept_levels = [h for h in hierarchy_levels if h["department"] == dept]

    if dept_levels:
        if role == "HOD":
            # HOD enters at the department root (shallowest level for that dept)
            return min(dept_levels, key=lambda h: h["level_number"])
        # VIEWER / EDITOR / QUALITY / AUDITOR enter at their deepest leaf in the dept
        return max(dept_levels, key=lambda h: h["level_number"])

    # Fallback for a department not present in the hierarchy (e.g. surprise-test user)
    # -> enter at the hospital root so the pipeline never crashes on an unseen dept.
    return next((h for h in hierarchy_levels if h["level_number"] == 1), hierarchy_levels[0])
