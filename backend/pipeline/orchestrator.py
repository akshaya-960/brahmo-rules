"""
Pipeline Orchestrator
Permission Compiler -> Entry Point Resolver -> BFS -> Zone2 Injection ->
Five-Check Filter -> Candidate Assembler, with per-stage timing + funnel counts.
"""
import time

from backend.db import get_hierarchy_levels, get_knowledge_nodes, get_user
from backend.pipeline.permission_compiler import compile_permissions
from backend.pipeline.entry_point_resolver import resolve_entry_point
from backend.pipeline.bfs_traversal import bfs_traverse
from backend.pipeline.zone2_injector import inject_zone2
from backend.pipeline.five_check_filter import (
    check1_isolation, check2_compliance, check3_permission,
    check4_temporal, check5_derivability,
)
from backend.pipeline.candidate_assembler import assemble_candidates


def run_pipeline(user_id: str, supabase, include_zone2: bool = True) -> dict:
    t_start = time.perf_counter()

    user = get_user(user_id)
    if not user:
        raise ValueError(f"Unknown user_id: {user_id}")
    org_id = user["org_id"]

    t0 = time.perf_counter()
    hierarchy_levels = get_hierarchy_levels(org_id)
    all_nodes = get_knowledge_nodes(org_id)
    t_fetch = (time.perf_counter() - t0) * 1000

    total_nodes = len(all_nodes)
    level_number_by_id = {h["id"]: h["level_number"] for h in hierarchy_levels}

    t0 = time.perf_counter()
    perms = compile_permissions(user)
    t_compile = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    entry_level = resolve_entry_point(user, hierarchy_levels)
    t_entry = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    level_distances = bfs_traverse(entry_level["id"], hierarchy_levels)
    t_bfs = (time.perf_counter() - t0) * 1000

    reachable_level_ids = list(level_distances.keys())

    node_map = {
        n["id"]: n for n in all_nodes
        if n["hierarchy_level_id"] in reachable_level_ids
    }
    distance_map = {
        n["id"]: level_distances.get(n["hierarchy_level_id"], 0)
        for n in node_map.values()
    }
    after_bfs = len(node_map)

    t0 = time.perf_counter()
    if include_zone2:
        zone2_nodes = [n for n in all_nodes if n["zone"] == 2]
        inject_zone2(node_map, distance_map, zone2_nodes, level_distances)
    t_zone2 = (time.perf_counter() - t0) * 1000
    after_zone2 = len(node_map)

    combined = list(node_map.values())

    t0 = time.perf_counter()
    c1 = check1_isolation(combined, org_id)
    t_c1 = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    clearance = set(user.get("compliance_clearance") or [])
    c2 = check2_compliance(c1, clearance)
    t_c2 = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    c3 = check3_permission(c2, perms, level_number_by_id)
    t_c3 = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    c4 = check4_temporal(c3)
    t_c4 = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    c5 = check5_derivability(c4)
    t_c5 = (time.perf_counter() - t0) * 1000

    candidate_set = assemble_candidates(c5, distance_map)
    total_ms = (time.perf_counter() - t_start) * 1000

    return {
        "user": user["id"],
        "user_name": user["name"],
        "role": user["role"],
        "ceiling_level": user["ceiling_level"],
        "entry_point": entry_level["id"],
        "pipeline_timing": {
            "fetch_ms": round(t_fetch, 2),
            "permission_compile_ms": round(t_compile, 2),
            "entry_resolve_ms": round(t_entry, 2),
            "bfs_ms": round(t_bfs, 2),
            "zone2_inject_ms": round(t_zone2, 2),
            "check1_isolation_ms": round(t_c1, 2),
            "check2_compliance_ms": round(t_c2, 2),
            "check3_permission_ms": round(t_c3, 2),
            "check4_temporal_ms": round(t_c4, 2),
            "check5_derivability_ms": round(t_c5, 2),
            "total_ms": round(total_ms, 2),
        },
        "funnel": {
            "total_nodes": total_nodes,
            "after_bfs": after_bfs,
            "after_zone2": after_zone2,
            "after_check1": len(c1),
            "after_check2": len(c2),
            "after_check3": len(c3),
            "after_check4": len(c4),
            "after_check5": len(c5),
        },
        "candidate_set": candidate_set,
    }
