# Architecture: BFS Traversal + 5-Check Filter Pipeline

## Overview

The Rules Engine takes a user identity and returns a "candidate set" of knowledge
nodes that user is authorized and relevantly scoped to see -- with ZERO LLM calls
anywhere in the decision path. Every decision is a deterministic graph traversal
or a boolean filter. The same graph produces different candidate sets for
different users purely as a function of role, department, ceiling level, and
compliance clearance.

## Pipeline Order (strict, sequential)

User -> Permission Compiler -> Entry Point Resolver -> BFS Traversal
-> Zone 2 Injection -> Check 1 (Isolation) -> Check 2 (Compliance)
-> Check 3 (Permission) -> Check 4 (Temporal) -> Check 5 (Derivability)
-> Candidate Set Assembler -> JSON response

Each check consumes the *output* of the previous check, never runs in parallel.
This matters concretely: a node excluded by Check 2 (compliance) must never even
be evaluated by Check 3 (permission) -- if checks ran in parallel or in a
different order, a node could theoretically pass permission but still leak
through if compliance exclusion were applied afterward as an afterthought
rather than as a true prerequisite.

## 1. Permission Compiler

Compiles `{level_number: {can_read, can_write}}` for all 15 levels, ONCE per
pipeline run, before any node is evaluated. This converts what would otherwise
be up to 500+ per-node permission lookups (an N+1 database query pattern) into
a single O(1) dictionary lookup per node during Check 3.

Rules:
- `VIEWER`: can_read levels >= ceiling_level; cannot write.
- `EDITOR` / `QUALITY` / `AUDITOR`: can_read levels >= ceiling_level;
  can_write levels >= write_ceiling.
- `HOD`: can_read ALL levels; can_write levels >= write_ceiling.
- `ADMIN`: can_read and can_write everything.

## 2. Entry Point Resolver

- `ADMIN` -> hospital root (`HL-01`).
- `HOD` -> the shallowest node in their department (department root).
- All other roles -> the node in their department whose level_number is
  closest to their own ceiling_level.
- No hierarchy node exists for the user's department -> fall back to the
  hospital root, letting the pipeline handle a "surprise user" with zero
  code changes.

## 3. BFS Traversal (Multi-Parent DAG Handling)

FIFO-queue breadth-first search walking UPWARD through `parent_ids`, then
downward from same-department ancestors. The `visited` set guarantees
correctness for multi-parent nodes and prevents infinite loops on any
accidental cycle.

**Cycle prevention on write** (not yet implemented, production-correct
answer documented): validate on `INSERT`/`UPDATE` to
`hierarchy_levels.parent_ids` that the new edge does not create a path back
to the node's own descendants, before allowing the write. The BFS visited
set is the runtime safety net; insert-time validation is the structural
prevention -- currently missing in this implementation.

## 4. Zone 2 Injection

After BFS, nodes tagged `zone = 2` are injected into the reachable set
regardless of traversal path, then go through all 5 checks like any other
node -- except Check 3, where Zone 2 nodes bypass the ceiling comparison
(since they're stored at a shallow hierarchy level for organization-wide
relevance, and a naive ceiling check would otherwise incorrectly exclude
them for every non-admin user).

## 5. Five-Check Sequential Filter

| Check | Rule | Enforcement layer in this implementation |
|---|---|---|
| 1. Isolation | `org_id = user.org_id` | SQL WHERE clause on the initial fetch |
| 2. Compliance | `compliance_tags` subset of `user.compliance_clearance` | Application-level (Python), post-fetch |
| 3. Permission | `hierarchy_level >= ceiling_level` via compiled map; Zone 2 bypasses | Application-level (Python), post-fetch |
| 4. Temporal | excludes `SUPERSEDED`/`EXPIRED`/expired `valid_until` | Application-level (Python), post-fetch |
| 5. Derivability | excludes `derivability_score >= 0.7` | Application-level (Python), post-fetch |

### GAP 5 tradeoff -- acknowledged directly

In the current implementation, the initial fetch from Supabase is bounded
only by (a) the user's `org_id` -- it pulls every knowledge_node belonging
to that organization, unconditionally, before BFS, Zone 2 injection, or any
of the five checks run. All five checks (including Check 1, Isolation) then
execute as Python filters in application memory on that full org-scoped set,
not as additional SQL WHERE clauses or RLS policies.

This means every node in the organization -- including ones a given user has
no permission or compliance clearance to see -- briefly exists in backend
application memory before being filtered out, even though restricted nodes
never reach the frontend or the end user. For this assessment's scale (50
nodes), the exposure surface of this is negligible; at production scale
(15,000+ nodes across multiple hospitals), this is the highest-priority item
to migrate first, since a full-org fetch is exactly the anti-pattern GAP 5
calls out.

This is an explicitly acceptable tradeoff for this assessment (per its own
FAQ: "application-level filtering is faster to build... if you use
application-level, acknowledge the tradeoff"). The production-correct
migration path is Postgres Row-Level Security policies on `knowledge_nodes`,
keyed off a `current_setting()` session variable set per-request to the
requesting user's clearance/ceiling -- so Postgres itself enforces the
boundary and no restricted row is ever returned by any query path.

## 6. Candidate Set Assembler

Surviving nodes are annotated with `distance_from_entry`-derived
`compression_hint`: distance 0-1 -> `FULL`, distance 2 -> `COMPRESSED`,
distance 3+ -> `CONSTRAINT_ONLY`.

## Known Limitations / Future Work

- All 5 checks run as application-level Python filters on a full org-scoped
  fetch, rather than SQL WHERE clauses or RLS policies (see GAP 5 above).
- Derivability scores are manually seeded rather than computed by an actual
  heuristic or embedding-similarity pipeline.
- Cycle prevention exists at BFS runtime (visited set) but not yet as an
  insert-time validation constraint on `hierarchy_levels.parent_ids`.
