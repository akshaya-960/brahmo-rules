# Architecture: BFS Traversal + 5-Check Filter Pipeline

## Overview

The Rules Engine takes a user identity and returns a "candidate set" of knowledge
nodes that user is authorized and relevantly scoped to see -- with ZERO LLM calls
anywhere in the decision path. Every decision is a deterministic graph traversal
or a boolean filter. The same graph produces different candidate sets for
different users purely as a function of role, department, ceiling level, and
compliance clearance.

## Pipeline Order (strict, sequential)User -> Permission Compiler -> Entry Point Resolver -> BFS Traversal
-> Zone 2 Injection -> Check 1 (Isolation) -> Check 2 (Compliance)
-> Check 3 (Permission) -> Check 4 (Temporal) -> Check 5 (Derivability)
-> Candidate Set Assembler -> JSON responseEach check consumes the *output* of the previous check, never runs in parallel.
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
  can_write levels >= write_ceiling. (QUALITY/AUDITOR are not explicitly
  defined in the original spec text but exist in the DB's role constraint;
  treating them like EDITOR is the closest fit given they carry a
  write_ceiling value in the seed data.)
- `HOD`: can_read ALL levels (a department head can see everything in their
  organization's knowledge graph, not just their own department's depth);
  can_write levels >= write_ceiling.
- `ADMIN`: can_read and can_write everything.

## 2. Entry Point Resolver

Maps a user to the single hierarchy_levels node where their BFS traversal
begins.

- `ADMIN` -> always the hospital root (`HL-01`). Entry point doesn't gate an
  admin's reach since they can read everything anyway.
- `HOD` -> the shallowest node in their department (their department root),
  since HODs read all levels regardless of ceiling.
- All other roles -> the node in their department whose level_number is
  closest to their own ceiling_level. This is deliberately NOT simply "the
  deepest node in the department" -- a department can have multiple levels
  below a user's ceiling (e.g. a ward level AND a specific-patient level both
  sit below an EDITOR's ceiling of 8), and blindly picking the deepest one
  would start that user's traversal at an arbitrary patient's chart rather
  than their actual department scope.
- No hierarchy node exists for the user's department at all (e.g. a
  pharmacist in a "pharmacy" department, or a QA officer in "quality" --
  departments with no dedicated DAG node in this seed set) -> fall back to
  the hospital root. This is what lets the pipeline handle a "surprise user"
  with zero code changes: BFS from the root plus the five checks (in
  particular the permission ceiling in Check 3) still correctly scope what
  that user ultimately sees, even though their literal entry point is
  maximally broad.

## 3. BFS Traversal (Multi-Parent DAG Handling)

Standard FIFO-queue breadth-first search, but walking UPWARD through each
node's `parent_ids` array rather than downward through children. A node like
"Post-TKR Protocol Area" has two parents (`HL-05-ORTHO` and `HL-05-SURG`),
since it is legitimately relevant to both departments. The `visited` set
guarantees:
1. Correctness: a multi-parent node is only added to the reachable set once,
   regardless of how many paths lead to it.
2. Safety: if a cycle were ever accidentally introduced into the graph
   (Node A -> Node B -> Node C -> Node A), the visited set prevents an
   infinite loop -- a node already visited is simply skipped rather than
   re-queued.

Distance from entry is tracked during traversal (`distance_from_entry`),
which downstream feeds directly into the candidate assembler's
`compression_hint` (closer nodes get fuller detail, farther nodes get
progressively compressed).

**Cycle prevention on write** (not required for this assessment's static
seed data, but the production-correct answer): a real system would validate
on `INSERT`/`UPDATE` to `hierarchy_levels.parent_ids` that adding an edge does
not create a path back to any of the node's own descendants -- e.g. a
topological sort check or a reachability check from the new parent back to
the node itself before allowing the write. The visited set is the runtime
safety net; insert-time validation is the structural prevention.

## 4. Zone 2 Injection

After BFS completes, all nodes tagged `zone = 2` (GLOBAL) are injected into
the reachable set, regardless of whether the user's traversal path reached
them. These represent hospital-wide constraints (e.g. "never combine
Warfarin with NSAIDs") that must reach every user irrespective of department.

Injection happens strictly BEFORE the five checks -- Zone 2 nodes are not
automatically exempt from filtering. A Zone 2 node CAN still be excluded by
Check 2 (compliance), Check 4 (temporal), or Check 5 (derivability). The one
deliberate exception is Check 3 (permission ceiling): Zone 2 nodes bypass the
literal `hierarchy_level >= ceiling` comparison. This is a necessary
correction to what would otherwise be a self-contradiction in the naive rule
-- Global nodes are stored at a shallow hierarchy level (Level 3) specifically
because they're organization-wide, but a naive ceiling check would then
INCORRECTLY exclude them for any user whose ceiling is deeper than 3 (which
is every non-admin user in this seed set). Bypassing the ceiling check for
Zone 2 nodes specifically is what makes "Zone 2 saves lives" actually true in
practice, not just in the demo narrative.

## 5. Five-Check Sequential Filter

| Check | Rule | Enforcement layer in this implementation |
|---|---|---|
| 1. Isolation | `org_id = user.org_id` | SQL WHERE clause on the initial fetch (true GAP 5 compliance -- cross-tenant data never leaves the database) |
| 2. Compliance | node's `compliance_tags` must be a subset of `user.compliance_clearance` | Application-level (Python), post-fetch |
| 3. Permission | `hierarchy_level >= user.ceiling_level`, via the compiled O(1) map; Zone 2 nodes bypass this | Application-level (Python), post-fetch |
| 4. Temporal | excludes `SUPERSEDED`/`EXPIRED` status and any `valid_until` in the past | Application-level (Python), post-fetch |
| 5. Derivability | excludes nodes with `derivability_score >= 0.7` (configurable per org) | Application-level (Python), post-fetch |

### GAP 5 tradeoff -- acknowledged directly

The spec's stated ideal is that restricted data should never be retrieved
from the database before a permission check clears it -- ideally as SQL
WHERE clauses or Postgres Row-Level Security policies, so a compliance- or
permission-restricted row never crosses the network at all.

This implementation partially achieves that: the initial fetch from Supabase
is already bounded to (a) the user's `org_id` and (b) the specific
BFS-reachable `hierarchy_level_id`s plus Zone 2 nodes -- NOT the entire
knowledge_nodes table. For a graph of any realistic size, this means the
nodes that reach Python memory are already a small, structurally-relevant
subset (bounded by the user's reachable subgraph, not the total graph size).

However, Checks 2 through 5 then run as Python filters on that already-small
set, rather than as additional SQL WHERE clauses or RLS policies. This means
a small number of compliance-restricted rows (e.g. an MNPI-tagged budget
node) do briefly exist in backend application memory before being filtered
out, even though they never reach the frontend or the end user.

This is an explicitly acceptable tradeoff for this assessment (per its own
FAQ: "application-level filtering is faster to build... if you use
application-level, acknowledge the tradeoff"). The production-correct
migration path is to convert Checks 2, 4, and 5 into either:
1. Additional SQL WHERE clauses appended to the same query that already
   filters by org_id and hierarchy_level_id, or
2. Postgres Row-Level Security policies on `knowledge_nodes`, keyed off a
   `current_setting()` session variable set per-request to the requesting
   user's clearance/ceiling -- so Postgres itself enforces the boundary and
   no restricted row is ever returned by any query path, including one that
   bypasses this API entirely.

Check 3 (permission) is the one check that's harder to push fully into SQL
without also pushing the O(1) permission-compilation logic into SQL (e.g. as
a stored function) -- for this assessment's scale (50 nodes, 15 levels) the
performance difference is negligible either way, but at the "15,000 nodes
across 12 hospitals" scale mentioned in the assessment's scalability
question, converting Check 3 into a SQL join against a small
per-session permissions table (rather than a per-row Python dict lookup)
would be the next optimization.

## 6. Candidate Set Assembler

Surviving nodes are annotated with `distance_from_entry`-derived
`compression_hint`:
- distance 0-1 -> `FULL` (close to the user's actual context, full detail
  warranted)
- distance 2 -> `COMPRESSED`
- distance 3+ -> `CONSTRAINT_ONLY` (far from the user's context; only the
  binding rule matters, not full explanatory detail)

This is the interface contract with the (not-built-in-this-assessment)
downstream Composition Agent, which would use these hints to decide how much
of each node's `content` to actually spend token budget on.

## Performance Characteristics

The pipeline's cost scales with the user's REACHABLE subgraph, not the total
graph size. Priya's BFS touches roughly the same number of nodes whether the
hospital has 50 nodes or 15,000 -- because her traversal is bounded by her
department's depth in the hierarchy, not by total node count. Checks 1
(isolation) is a true SQL WHERE clause and scales with a database index on
`org_id`. Derivability scores are pre-computed at seed/ingest time, not
computed at query time, so Check 5 never triggers additional computation
regardless of graph size. The one component whose cost isn't inherently
graph-size-independent is Checks 2-5 running in Python on the
BFS-plus-Zone2-bounded fetch -- but since that fetch is already bounded by
reachable subgraph size (not total graph size), this remains proportional to
what the user can actually see, not to the organization's total knowledge
base.

## Known Limitations / Future Work

- Checks 2, 4, and 5 run as application-level Python filters rather than SQL
  WHERE clauses or RLS policies (see GAP 5 discussion above).
- Derivability scores are manually seeded in this assessment rather than
  computed by an actual heuristic or embedding-similarity pipeline; a
  production version would compute these as a batch job (e.g. comparing node
  content against a general medical knowledge embedding index, or simpler
  heuristics like matching against common textbook phrasing patterns).
- Cycle prevention exists at BFS runtime (visited set) but not yet as an
  insert-time validation constraint on `hierarchy_levels.parent_ids`.
