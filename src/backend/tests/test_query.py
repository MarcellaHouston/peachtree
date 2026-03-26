from backend.chromaDB.chroma_db import query, get_static_traits
import time

USER_ID = "user_abc123"
NOW = int(time.time())

# Counts from seed.py — update these if seed data changes
SEED_STATIC_TRAITS = 4
SEED_VALID_NON_STATIC = 4   # non-static talking points with end_timestamp >= now
SEED_EXPIRED = 3            # non-static talking points with end_timestamp < now


def print_query_results(results: dict) -> None:
    docs = results["documents"]
    metas = results["metadatas"]
    ids = results["ids"]
    distances = results["distances"]
    if not docs:
        print("  (no results)")
        return
    for doc, meta, rid, dist in zip(docs, metas, ids, distances):
        expired = meta["end_timestamp"] < NOW
        dist_str = f"{dist:.4f}" if dist is not None else "N/A (static)"
        print(f"\n  ID:           {rid[:8]}...")
        print(f"  Document:     {doc}")
        print(f"  Static trait: {meta['static_trait']}")
        print(f"  Distance:     {dist_str}")
        print(f"  End ts:       {meta['end_timestamp']}  {'[EXPIRED]' if expired else '[valid]'}")


def print_get_results(results: dict) -> None:
    docs = results["documents"]
    metas = results["metadatas"]
    ids = results["ids"]
    if not docs:
        print("  (no results)")
        return
    for doc, meta, rid in zip(docs, metas, ids):
        expired = meta["end_timestamp"] < NOW
        print(f"\n  ID:           {rid[:8]}...")
        print(f"  Document:     {doc}")
        print(f"  End ts:       {meta['end_timestamp']}  {'[EXPIRED]' if expired else '[valid]'}")
        print(f"  Verbose:      {meta['verbose_summary'][:80]}...")


# ── 1. query() with check_end_timestamp=True (default) ───────────────────────
print("=" * 60)
print("QUERY: 'fitness and running'  |  check_end_timestamp=True")
print("=" * 60)
results_filtered = query("fitness and running", check_end_timestamp=True, user_id=USER_ID, n_results=5)
print(f"Results: {len(results_filtered['documents'])}")
print_query_results(results_filtered)

# No non-static doc should be expired
for meta in results_filtered["metadatas"]:
    if not meta["static_trait"]:
        assert meta["end_timestamp"] >= NOW, (
            f"check_end_timestamp=True returned an expired non-static doc: end_timestamp={meta['end_timestamp']}"
        )
print("  PASS: no expired non-static docs returned")

# Static traits must always be present
static_in_results = [m for m in results_filtered["metadatas"] if m["static_trait"]]
assert len(static_in_results) == SEED_STATIC_TRAITS, (
    f"Expected all {SEED_STATIC_TRAITS} static traits in results, got {len(static_in_results)}"
)
print(f"  PASS: all {SEED_STATIC_TRAITS} static traits present")

# ── 2. query() with check_end_timestamp=False ─────────────────────────────────
print("\n" + "=" * 60)
print("QUERY: 'fitness and running'  |  check_end_timestamp=False")
print("=" * 60)
results_all = query("fitness and running", check_end_timestamp=False, user_id=USER_ID, n_results=5)
print(f"Results: {len(results_all['documents'])}")
print_query_results(results_all)

# Unfiltered should return >= results (more expired non-static docs can appear)
assert len(results_all["documents"]) >= len(results_filtered["documents"]), (
    "check_end_timestamp=False should return >= results than True"
)
print("  PASS: unfiltered query returns >= filtered query count")

# Static traits must still be present
static_in_all = [m for m in results_all["metadatas"] if m["static_trait"]]
assert len(static_in_all) == SEED_STATIC_TRAITS, (
    f"Expected {SEED_STATIC_TRAITS} static traits in unfiltered results, got {len(static_in_all)}"
)
print(f"  PASS: all {SEED_STATIC_TRAITS} static traits present in unfiltered results")

# ── 3. query() static traits always appear regardless of n_results ────────────
print("\n" + "=" * 60)
print("QUERY: 'fitness and running'  |  n_results=1  (static traits must still all appear)")
print("=" * 60)
results_narrow = query("fitness and running", check_end_timestamp=True, user_id=USER_ID, n_results=1)
print(f"Results: {len(results_narrow['documents'])}")
print_query_results(results_narrow)

non_static_in_narrow = [m for m in results_narrow["metadatas"] if not m["static_trait"]]
static_in_narrow = [m for m in results_narrow["metadatas"] if m["static_trait"]]
assert len(non_static_in_narrow) == 1, (
    f"Expected 1 non-static result with n_results=1, got {len(non_static_in_narrow)}"
)
assert len(static_in_narrow) == SEED_STATIC_TRAITS, (
    f"Expected all {SEED_STATIC_TRAITS} static traits even with n_results=1, got {len(static_in_narrow)}"
)
print(f"  PASS: 1 non-static result + all {SEED_STATIC_TRAITS} static traits returned with n_results=1")

# ── 4. query() static trait distances are None ────────────────────────────────
print("\n" + "=" * 60)
print("QUERY: distances — static=None, non-static=float")
print("=" * 60)
for meta, dist in zip(results_filtered["metadatas"], results_filtered["distances"]):
    if meta["static_trait"]:
        assert dist is None, f"Static trait should have distance=None, got {dist}"
    else:
        assert isinstance(dist, float), f"Non-static result should have float distance, got {dist}"
print("  PASS: static traits have distance=None, non-static have float distances")

# ── 5. get_static_traits() with check_end_timestamp=True ─────────────────────
print("\n" + "=" * 60)
print("GET STATIC TRAITS  |  check_end_timestamp=True")
print("=" * 60)
traits_filtered = get_static_traits(check_end_timestamp=True, user_id=USER_ID)
print(f"Results: {len(traits_filtered['documents'])}")
print_get_results(traits_filtered)

assert len(traits_filtered["documents"]) == SEED_STATIC_TRAITS, (
    f"Expected {SEED_STATIC_TRAITS} static traits, got {len(traits_filtered['documents'])}"
)
for meta in traits_filtered["metadatas"]:
    assert meta["static_trait"] is True, f"Non-static doc returned by get_static_traits: {meta}"
    assert meta["end_timestamp"] >= NOW, f"Expired static trait returned: end_timestamp={meta['end_timestamp']}"
print(f"  PASS: {SEED_STATIC_TRAITS} static traits returned, all valid and marked static")

# ── 6. get_static_traits() with check_end_timestamp=False ────────────────────
print("\n" + "=" * 60)
print("GET STATIC TRAITS  |  check_end_timestamp=False")
print("=" * 60)
traits_all = get_static_traits(check_end_timestamp=False, user_id=USER_ID)
print(f"Results: {len(traits_all['documents'])}")
print_get_results(traits_all)

assert len(traits_all["documents"]) == SEED_STATIC_TRAITS, (
    f"Expected {SEED_STATIC_TRAITS} static traits, got {len(traits_all['documents'])}"
)
for meta in traits_all["metadatas"]:
    assert meta["static_trait"] is True, f"Non-static doc returned by get_static_traits: {meta}"
assert len(traits_all["documents"]) == len(traits_filtered["documents"]), (
    "check_end_timestamp=True/False should return same count for static traits (none expire)"
)
print(f"  PASS: counts match between check_end_timestamp=True and False ({SEED_STATIC_TRAITS} each)")

print("\n" + "=" * 60)
print("ALL ASSERTIONS PASSED")
print("=" * 60)
