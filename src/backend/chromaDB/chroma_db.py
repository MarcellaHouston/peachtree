import time
import uuid
import chromadb
from typing import Optional

client = chromadb.PersistentClient(path="./chroma_db")

# Stores individual goals (embedded for semantic RAG search).
# Each document is one goal; llm_summary lives in metadata alongside
# user_id, conversation_id, and UNIX timestamp.
goals_collection = client.get_or_create_collection(
    name="conversation_goals",
    metadata={"hnsw:space": "cosine"},
)

# Stores the full transcript per conversation, keyed by conversation_id.
# Not embedded for semantic search — retrieved by ID or user filter.
transcripts_collection = client.get_or_create_collection(
    name="conversation_transcripts",
    metadata={"hnsw:space": "cosine"},
)


def store_conversation(
    user_id: str,
    goal_titles: list[str],
    goal_contexts: list[str],
    llm_summary: str,
    full_transcript: str,
    conversation_id: Optional[str] = None,
    timestamp: Optional[int] = None,
) -> str:
    """
    Persist a conversation's extracted goals, LLM summary, and full transcript.

    Each goal is stored as its own document in `conversation_goals`. The embedded
    document is `goal_contexts[i]` — a rich, goal-specific snippet describing the
    goal, its current status, and relevant user context from this conversation.
    The short `goal_titles[i]` is stored in metadata for display purposes.

    This separation means retrieval returns self-contained, goal-specific context
    rather than a bare goal string with a noisy conversation-level summary.

    Args:
        user_id:          ID of the user who had the conversation.
        goal_titles:      Short goal labels (e.g. "Go to the gym 3x/week").
                          Stored in metadata for display; not embedded.
        goal_contexts:    Rich goal-specific snippets to embed. Should describe
                          the goal, its status in this conversation, and any
                          relevant user context. Must match length of goal_titles.
        llm_summary:      LLM-generated summary of the full conversation.
                          Stored in metadata as supplementary context.
        full_transcript:  The complete transcribed conversation text.
        conversation_id:  Optional; auto-generated UUID if not supplied.
        timestamp:        UNIX timestamp; defaults to now.

    Returns:
        The conversation_id used for this entry.
    """
    if len(goal_titles) != len(goal_contexts):
        raise ValueError("goal_titles and goal_contexts must be the same length.")
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())
    if timestamp is None:
        timestamp = int(time.time())

    if goal_contexts:
        goals_collection.add(
            documents=goal_contexts,
            ids=[f"{conversation_id}_goal_{i}" for i in range(len(goal_contexts))],
            metadatas=[
                {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "timestamp": timestamp,
                    "goal_title": goal_titles[i],
                    "llm_summary": llm_summary,
                    "goal_index": i,
                }
                for i in range(len(goal_contexts))
            ],
        )

    transcripts_collection.add(
        documents=[full_transcript],
        ids=[conversation_id],
        metadatas=[
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "timestamp": timestamp,
            }
        ],
    )

    return conversation_id


def query_goals(
    query_text: str,
    user_id: Optional[str] = None,
    n_results: int = 5,
    since_timestamp: Optional[int] = None,
) -> dict:
    """
    Semantically search goals, optionally filtered by user and/or time window.

    Returns ChromaDB query results including the matched goal context snippet,
    distance, and metadata (goal_title, llm_summary, conversation_id, timestamp).
    """
    # Build a list of metadata filter conditions to narrow the vector search
    conditions = []
    if user_id:
        # Only return goals belonging to this user
        conditions.append({"user_id": {"$eq": user_id}})
    if since_timestamp is not None:
        # Only return goals from conversations at or after this UNIX timestamp
        conditions.append({"timestamp": {"$gte": since_timestamp}})

    # Combine conditions: ChromaDB requires $and when there are multiple filters,
    # a single dict when there's one, or None when there are no filters at all
    where = (
        {"$and": conditions}
        if len(conditions) > 1
        else conditions[0] if conditions else None
    )

    # query_texts: ChromaDB embeds this string and finds the closest goal contexts
    # n_results: how many top matches to return
    kwargs: dict = {"query_texts": [query_text], "n_results": n_results}
    if where:
        kwargs["where"] = where  # attach metadata filters if any were set

    # Runs the vector similarity search against the embedded goal_contexts
    return goals_collection.query(**kwargs)


def get_transcript(conversation_id: str) -> Optional[dict]:
    """
    Retrieve the full transcript for a given conversation_id.

    Returns a dict with 'transcript' and 'metadata', or None if not found.
    """
    result = transcripts_collection.get(ids=[conversation_id])
    if not result["documents"]:
        return None
    return {
        "conversation_id": conversation_id,
        "transcript": result["documents"][0],
        "metadata": result["metadatas"][0],
    }


def get_user_conversations(
    user_id: str,
    since_timestamp: Optional[int] = None,
) -> dict:
    """
    Retrieve all transcript metadata for a user, optionally filtered by time.

    Returns ChromaDB get() results (ids, documents, metadatas).
    """
    conditions = [{"user_id": {"$eq": user_id}}]
    if since_timestamp is not None:
        conditions.append({"timestamp": {"$gte": since_timestamp}})

    where = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    return transcripts_collection.get(where=where)
