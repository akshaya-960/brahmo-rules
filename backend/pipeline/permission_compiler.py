"""
Permission Compiler
Compiles a user role/ceiling into an O(1) lookup table ONCE per session.
Avoids per-node DB queries (N+1 problem) during the five-check filter.
"""

def compile_permissions(user: dict) -> dict:
    role = user["role"]
    ceiling = user["ceiling_level"]
    write_ceiling = user.get("write_ceiling")

    perms = {}
    for level in range(1, 16):
        if role == "ADMIN":
            can_read, can_write = True, True
        elif role == "HOD":
            can_read = True
            can_write = write_ceiling is not None and level >= write_ceiling
        elif role == "EDITOR":
            can_read = level >= ceiling
            can_write = write_ceiling is not None and level >= write_ceiling
        else:  # VIEWER, QUALITY, AUDITOR, etc.
            can_read = level >= ceiling
            can_write = False
        perms[level] = {"can_read": can_read, "can_write": can_write}
    return perms
