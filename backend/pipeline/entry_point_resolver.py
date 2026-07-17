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

    # Only organizational/structural levels are valid entry points.
    # Patient-specific leaves (e.g. "Patient: Rajan") are session-scoped
    # context nodes, not generic entry positions for a user session.
    dept_levels = [
        h for h in hierarchy_levels
        if h["department"] == dept and not h["level_name"].startswith("Patient:")
    ]

    if dept_levels:
        if role == "HOD":
            # HOD enters at the department root (shallowest level for that dept)
            return min(dept_levels, key=lambda h: h["level_number"])
        # VIEWER / EDITOR / QUALITY / AUDITOR enter at their deepest non-patient leaf
        return max(dept_levels, key=lambda h: h["level_number"])

    # Fallback for a department not present in the hierarchy (e.g. surprise-test user)
    return next((h for h in hierarchy_levels if h["level_number"] == 1), hierarchy_levels[0])
