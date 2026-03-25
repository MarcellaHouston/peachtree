import time
import uuid
import chromadb
from typing import Optional

client = chromadb.PersistentClient(path="./chroma_db")

# Single collection storing one document per talking point.
# Each document is a short LLM summary (embedded for semantic search).
# Metadata holds end_timestamp (expiry), verbose_summary, static_trait, user_id.
talking_points_collection = client.get_or_create_collection(
    name="talking_points",
    metadata={"hnsw:space": "cosine"},
)


def store_talking_point(
    user_id: str,
    document: str,
    verbose_summary: str,
    static_trait: bool,
    end_timestamp: int,
) -> str:
    """
    Store a single talking point in the collection.

    Args:
        user_id:         ID of the user this talking point belongs to.
        document:        Short LLM summary of the talking point (embedded for search).
        verbose_summary: Accurate full retelling of the talking point.
        static_trait:    True if this info is always relevant (e.g. user's height).
                         Static traits should use end_timestamp=253402300799 (year 9999).
        end_timestamp:   UNIX timestamp after which this record is considered expired.

    Returns:
        The UUID assigned to this talking point.
    """
    point_id = str(uuid.uuid4())
    talking_points_collection.add(
        ids=[point_id],
        documents=[document],
        metadatas=[
            {
                "user_id": user_id,
                "verbose_summary": verbose_summary,
                "static_trait": static_trait,
                "end_timestamp": end_timestamp,
            }
        ],
    )
    return point_id


def query(
    query_text: str,
    check_end_timestamp: bool = True,
    user_id: Optional[str] = None,
    n_results: int = 5,
) -> dict:
    """
    Semantically search talking points.

    Returns the top n_results non-static talking points by relevance, plus
    all static traits unconditionally (they are never crowded out by n_results).

    Args:
        query_text:           Text to embed and search against stored documents.
        check_end_timestamp:  If True (default), exclude records where end_timestamp
                              is in the past (i.e. expired). If False, return all.
        user_id:              Optional filter to restrict results to one user.
        n_results:            Number of top non-static matches to return.

    Returns:
        Dict with keys ids, documents, metadatas, distances.
        Static trait entries have distance=None (fetched via get, not query).
    """
    # --- Non-static semantic search ---
    conditions = [{"static_trait": {"$eq": False}}]

    if user_id:
        conditions.append({"user_id": {"$eq": user_id}})
    if check_end_timestamp:
        conditions.append({"end_timestamp": {"$gte": int(time.time())}})

    where = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    non_static = talking_points_collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where,
    )

    # Unpack the single-query wrapper (list-of-lists) from ChromaDB
    ns_ids = non_static["ids"][0]
    ns_docs = non_static["documents"][0]
    ns_metas = non_static["metadatas"][0]
    ns_distances = non_static["distances"][0]

    # --- Static traits (all of them, always) ---
    static = get_static_traits(check_end_timestamp=check_end_timestamp, user_id=user_id)

    combined_ids = ns_ids + static["ids"]
    combined_docs = ns_docs + static["documents"]
    combined_metas = ns_metas + static["metadatas"]
    combined_distances = ns_distances + [None] * len(static["ids"])

    return {
        "ids": combined_ids,
        "documents": combined_docs,
        "metadatas": combined_metas,
        "distances": combined_distances,
    }


def get_static_traits(
    check_end_timestamp: bool = True,
    user_id: Optional[str] = None,
) -> dict:
    """
    Retrieve all talking points marked as static traits.

    Args:
        check_end_timestamp:  If True (default), exclude expired static traits.
                              If False, return all static traits regardless of expiry.
        user_id:              Optional filter to restrict results to one user.

    Returns:
        ChromaDB get() result dict (ids, documents, metadatas).
    """
    conditions: list = [{"static_trait": {"$eq": True}}]

    if user_id:
        conditions.append({"user_id": {"$eq": user_id}})
    if check_end_timestamp:
        conditions.append({"end_timestamp": {"$gte": int(time.time())}})

    where = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    return talking_points_collection.get(where=where)
