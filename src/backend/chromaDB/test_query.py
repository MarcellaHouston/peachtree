from backend.chromaDB.chroma_db import (
    query_goals,
    get_transcript,
    get_user_conversations,
)

USER_ID = "user_abc123"

# ── 1. Semantic search: find goals related to fitness ─────────────────────────
print("=" * 60)
print("QUERY: 'Social anxiety'")
print("=" * 60)
results = query_goals("Social anxiety", user_id=USER_ID, n_results=3)
for title, context, meta in zip(
    [m["goal_title"] for m in results["metadatas"][0]],
    results["documents"][0],
    results["metadatas"][0],
):
    print(f"\nTitle:   {title}")
    print(f"Convo:   {meta['conversation_id']}  |  timestamp: {meta['timestamp']}")
    print(f"Context: {context[:120]}...")

# ── 2. Semantic search: find goals related to money ───────────────────────────
print("\n" + "=" * 60)
print("QUERY: 'saving money and finances'")
print("=" * 60)
results = query_goals("saving money and finances", user_id=USER_ID, n_results=3)
for title, meta in zip(
    [m["goal_title"] for m in results["metadatas"][0]],
    results["metadatas"][0],
):
    print(f"\nTitle:  {title}")
    print(f"Convo:  {meta['conversation_id']}  |  timestamp: {meta['timestamp']}")

# ── 3. Filter by time: only goals from January 2025 onwards ──────────────────
print("\n" + "=" * 60)
print("QUERY: 'morning routine habits'  |  SINCE: Jan 1 2025")
print("=" * 60)
jan_1_2025 = 1735689600
results = query_goals(
    "morning routine habits", user_id=USER_ID, n_results=3, since_timestamp=jan_1_2025
)
for title, meta in zip(
    [m["goal_title"] for m in results["metadatas"][0]],
    results["metadatas"][0],
):
    print(f"\nTitle:  {title}")
    print(f"Convo:  {meta['conversation_id']}  |  timestamp: {meta['timestamp']}")

# ── 4. Fetch the full transcript for a specific conversation ──────────────────
print("\n" + "=" * 60)
print("GET TRANSCRIPT: conv_010")
print("=" * 60)
result = get_transcript("conv_010")
print(f"\nTimestamp: {result['metadata']['timestamp']}")
print(f"Transcript:\n{result['transcript']}")

# ── 5. Get all conversations for a user ───────────────────────────────────────
print("\n" + "=" * 60)
print("ALL CONVERSATIONS for user_abc123")
print("=" * 60)
convos = get_user_conversations(USER_ID)
for cid, meta in zip(convos["ids"], convos["metadatas"]):
    print(f"  {cid}  |  timestamp: {meta['timestamp']}")
