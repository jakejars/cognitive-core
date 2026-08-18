"""
Lockbox Partition Definitions — Cognitive Core Gen-2

Following Research Contract §3.1, tasks are split into three tiers:
  DEV GAUNTLET        — frequent iteration, model selection, prompt tuning
  REPLICATION GAUNTLET — second seed / second task sample confirmation
  FINAL LOCKBOX       — never used for development; only touched at milestone evaluation

Rules:
  - Lockbox tasks: NEVER used for model selection, prompt tuning, coefficient tuning,
    skill mining, retrieval-index construction, or synthetic-data generation
  - System must not retrieve from, train on, or mine skills from protected gauntlets
"""

# Partition strategy:
# Stratify by gauntlet family, assign ~60% dev, ~23% replication, ~15% lockbox
#
# M01 (4 tasks):    2 dev, 1 replication, 1 lockbox
# LCTX01 (3 tasks): 2 dev, 1 lockbox
# LCTX02 (2 tasks): 1 dev, 1 replication
# LCTX03 (2 tasks): 1 dev, 1 replication
# SA01 (2 tasks):   1 dev, 1 lockbox
# Total: 13 tasks → 7 dev, 3 replication, 3 lockbox

DEV_TASK_IDS = {
    "M01-001",      # M01 basic equivalence
    "M01-003",      # M01 renaming equivalence
    "LCTX01-001",   # LCTX01 basic fact recall
    "LCTX01-002",   # LCTX01 structured data
    "LCTX02-001",   # LCTX02 multi-fact planets
    "LCTX03-001",   # LCTX03 multi-hop chain
    "SA01-001",     # SA01 session continuity
}

REPLICATION_TASK_IDS = {
    "M01-002",      # M01 difference detection
    "LCTX02-002",   # LCTX02 multi-fact TODO list
    "LCTX03-002",   # LCTX03 multi-hop computation
}

LOCKBOX_TASK_IDS = {
    "M01-004",      # M01 semantic difference (upper vs lower) — NEVER TOUCH
    "LCTX01-003",   # LCTX01 conversation retrieval — NEVER TOUCH
    "SA01-002",     # SA01 configuration state — NEVER TOUCH
}


def get_partition(task_id: str) -> str:
    """Return 'dev', 'replication', or 'lockbox' for a task ID."""
    if task_id in DEV_TASK_IDS:
        return "dev"
    elif task_id in REPLICATION_TASK_IDS:
        return "replication"
    elif task_id in LOCKBOX_TASK_IDS:
        return "lockbox"
    return "unknown"


def verify_partition_coverage(all_task_ids: set) -> bool:
    """Verify every task is assigned to exactly one partition."""
    assigned = DEV_TASK_IDS | REPLICATION_TASK_IDS | LOCKBOX_TASK_IDS
    unassigned = all_task_ids - assigned
    over_assigned = (DEV_TASK_IDS & REPLICATION_TASK_IDS) | \
                    (DEV_TASK_IDS & LOCKBOX_TASK_IDS) | \
                    (REPLICATION_TASK_IDS & LOCKBOX_TASK_IDS)
    if unassigned:
        print(f"⚠️  Unassigned tasks: {unassigned}")
    if over_assigned:
        print(f"⚠️  Over-assigned tasks: {over_assigned}")
    if not unassigned and not over_assigned:
        print(f"✅ All {len(assigned)} tasks partitioned correctly "
              f"(dev={len(DEV_TASK_IDS)}, replication={len(REPLICATION_TASK_IDS)}, lockbox={len(LOCKBOX_TASK_IDS)})")
    return not unassigned and not over_assigned


if __name__ == "__main__":
    from gauntlets.gauntlet_tasks import all_tasks
    task_ids = {t["id"] for t in all_tasks()}
    verify_partition_coverage(task_ids)

    print("\nPartition mapping:")
    for t in sorted(all_tasks(), key=lambda x: x["id"]):
        part = get_partition(t["id"])
        print(f"  {t['id']:15s} → {part:12s} ({t['gauntlet']} — {t['difficulty']})")