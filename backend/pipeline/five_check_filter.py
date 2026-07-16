"""
Five-Check Sequential Filter
Each check consumes the OUTPUT of the previous check - never parallel.
"""
from datetime import datetime, timezone

DERIVABILITY_THRESHOLD = 0.7


def check1_isolation(nodes: list, org_id: str) -> list:
    return [n for n in nodes if n["org_id"] == org_id]


def check2_compliance(nodes: list, user_clearance: set) -> list:
    return [n for n in nodes if not (set(n.get("compliance_tags") or []) - user_clearance)]


def check3_permission(nodes: list, perms: dict, level_number_by_id: dict) -> list:
    passed = []
    for n in nodes:
        # Zone 2 (GLOBAL) nodes are hospital-wide safety policy - every cleared role must
        # see them regardless of hierarchy ceiling, so they bypass the ceiling check here.
        if n["zone"] == 2:
            passed.append(n)
            continue
        level_number = level_number_by_id.get(n["hierarchy_level_id"], 999)
        if perms.get(level_number, {}).get("can_read"):
            passed.append(n)
    return passed


def check4_temporal(nodes: list) -> list:
    now = datetime.now(timezone.utc)
    passed = []
    for n in nodes:
        if n["status"] in ("SUPERSEDED", "EXPIRED"):
            continue
        valid_until = n.get("valid_until")
        if valid_until:
            vu = datetime.fromisoformat(str(valid_until).replace("Z", "+00:00"))
            if vu <= now:
                continue
        passed.append(n)
    return passed


def check5_derivability(nodes: list, threshold: float = DERIVABILITY_THRESHOLD) -> list:
    return [n for n in nodes if float(n["derivability_score"]) < threshold]
