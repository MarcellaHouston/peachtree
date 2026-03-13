from backend.chromaDB.chroma_db import query, get_static_traits
import time

USER_ID = "user_abc123"
NOW = int(time.time())

# Counts from seed.py — update these if seed data changes
SEED_STATIC_TRAITS = 4
SEED_EXPIRED = 3       # talking points with end_timestamp < now
SEED_TOTAL = 11        # total talking points


def print_query_results(results: dict) -> None:
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    ids = results["ids"][0]
    if not docs:
        print("  (no results)")
        return
    for doc, meta, rid in zip(docs, metas, ids):
        expired = meta["end_timestamp"] < NOW
        print(f"\n  ID:           {rid[:8]}...")
        print(f"  Document:     {doc}")
        print(f"  Static trait: {meta['static_trait']}")
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
print(f"Results: {len(results_filtered['documents'][0])}")
print_query_results(results_filtered)

# No expired docs should appear
for meta in results_filtered["metadatas"][0]:
    assert meta["end_timestamp"] >= NOW, (
        f"check_end_timestamp=True returned an expired doc: end_timestamp={meta['end_timestamp']}"
    )
print("  PASS: no expired docs returned")

# ── 2. query() with check_end_timestamp=False ─────────────────────────────────
print("\n" + "=" * 60)
print("QUERY: 'fitness and running'  |  check_end_timestamp=False")
print("=" * 60)
results_all = query("fitness and running", check_end_timestamp=False, user_id=USER_ID, n_results=5)
print(f"Results: {len(results_all['documents'][0])}")
print_query_results(results_all)

# Returning all docs should yield >= results than the filtered query
assert len(results_all["documents"][0]) >= len(results_filtered["documents"][0]), (
    "check_end_timestamp=False should return >= results than True"
)
print("  PASS: unfiltered query returns >= filtered query count")

# ── 3. query() for static traits content ─────────────────────────────────────
print("\n" + "=" * 60)
print("QUERY: 'physical attributes and diet'  |  check_end_timestamp=True")
print("=" * 60)
results_static_query = query("physical attributes and diet", check_end_timestamp=True, user_id=USER_ID, n_results=3)
print(f"Results: {len(results_static_query['documents'][0])}")
print_query_results(results_static_query)

# Static traits are valid (never expire), so they should appear
assert len(results_static_query["documents"][0]) > 0, (
    "Expected static trait docs to surface for 'physical attributes and diet'"
)
for meta in results_static_query["metadatas"][0]:
    assert meta["end_timestamp"] >= NOW, "Static trait doc appears expired — check seed end_timestamp"
print("  PASS: static trait docs are present and not expired")

# ── 4. get_static_traits() with check_end_timestamp=True ─────────────────────
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

# ── 5. get_static_traits() with check_end_timestamp=False ────────────────────
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
