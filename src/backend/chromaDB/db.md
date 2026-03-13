# ChromaDB — How It Works

## What is ChromaDB?

ChromaDB is a **vector database**. Unlike a regular database (like SQLite) that finds records by exact matches or comparisons, ChromaDB finds records by **meaning**. You give it a sentence, and it returns the stored documents that are most semantically similar — even if they use completely different words.

This makes it useful for AI applications where you want to ask "what do we know about this topic?" rather than "find the row where column = value".

---

## How Semantic Search Works

When you store a document, ChromaDB runs it through an **embedding model** — a neural network that converts text into a list of numbers (a vector) that captures its meaning. For example:

- `"User is 6'2 tall"` → `[0.23, -0.11, 0.87, ...]`
- `"User's height is 188cm"` → `[0.24, -0.10, 0.85, ...]`

These two sentences have very similar vectors even though they use different words. When you query with `"how tall is the user?"`, ChromaDB embeds that too, then finds the stored vectors closest to it using **cosine similarity** (a measure of how much two vectors point in the same direction). The closest ones are returned as results.

---

## Our Setup

### Client

```python
client = chromadb.PersistentClient(path="./chroma_db")
```

`PersistentClient` saves data to disk at `./chroma_db` (relative to where the script is run from). Data survives between runs — unlike an in-memory client which resets every time.

### Collection

```python
talking_points_collection = client.get_or_create_collection(
    name="talking_points",
    metadata={"hnsw:space": "cosine"},
)
```

A **collection** is like a table. We have one: `talking_points`. The `hnsw:space: cosine` setting tells ChromaDB to use cosine similarity when comparing vectors (better for text than the default euclidean distance).

---

## Document Schema

Each entry in the collection has three parts:

| Part | What it is | Example |
|---|---|---|
| `id` | Unique UUID string | `"a3f2c1d0-..."` |
| `document` | Short LLM summary — **this is what gets embedded and searched** | `"User is lactose intolerant."` |
| `metadata` | Extra fields stored alongside the document, not embedded | see below |

### Metadata fields

| Field | Type | Description |
|---|---|---|
| `user_id` | `str` | Which user this belongs to |
| `verbose_summary` | `str` | Full accurate retelling of the talking point |
| `static_trait` | `bool` | `True` if this info is always relevant (e.g. height, diet) |
| `end_timestamp` | `int` | UNIX timestamp after which this record is considered expired |

> **Static traits** use `end_timestamp = 253402300799` (year 9999) so they never expire.

---

## The Three Functions

### `store_talking_point(...)`

Saves one talking point to the collection. Generates a UUID as the ID automatically.

```python
store_talking_point(
    user_id="user_abc123",
    document="User is lactose intolerant.",          # embedded for search
    verbose_summary="User mentioned during onboarding that they avoid all dairy products.",
    static_trait=True,
    end_timestamp=253402300799,                      # never expires
)
```

### `query(query_text, check_end_timestamp=True, user_id=None, n_results=5)`

Semantically searches the collection. Embeds `query_text` and returns the `n_results` most similar documents.

- `check_end_timestamp=True` *(default)*: only returns records where `end_timestamp >= now` (non-expired)
- `check_end_timestamp=False`: returns all records regardless of expiry
- `user_id`: if provided, filters to only that user's records

Returns a dict with `ids`, `documents`, `metadatas`, and `distances` (lower distance = more similar).

```python
results = query("does the user have any dietary restrictions?", user_id="user_abc123")
# → returns the lactose intolerance record (semantically close)
```

### `get_static_traits(check_end_timestamp=True, user_id=None)`

Retrieves all records where `static_trait=True`. Uses `get()` instead of `query()` — no search text needed, it just fetches by metadata filter.

- `check_end_timestamp=True` *(default)*: also filters to non-expired static traits
- `check_end_timestamp=False`: returns all static traits regardless of expiry

```python
traits = get_static_traits(user_id="user_abc123")
# → returns height, preferred name, dietary restriction, handedness
```

---

## query() vs get()

| | `query()` | `get()` |
|---|---|---|
| How it finds records | Semantic similarity (vector search) | Metadata filters only (exact match) |
| Needs query text | Yes | No |
| Returns distances | Yes | No |
| Use case | "What's relevant to this topic?" | "Give me all static traits" |

---

## Metadata Filtering

Both `query()` and `get()` accept a `where` clause to filter by metadata before (or alongside) the vector search. ChromaDB uses a JSON filter syntax:

```python
# Single condition
{"user_id": {"$eq": "user_abc123"}}

# Multiple conditions — must use $and
{"$and": [
    {"user_id": {"$eq": "user_abc123"}},
    {"end_timestamp": {"$gte": 1741824000}},
]}
```

Supported operators: `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`.

---

## Data Flow

```
Conversation happens
        ↓
LLM extracts talking points
        ↓
store_talking_point() called for each one
        ↓
ChromaDB embeds the document → stores vector + metadata on disk
        ↓
Later: query() called with a topic
        ↓
ChromaDB embeds the query → finds closest stored vectors
        ↓
Returns most relevant talking points (filtered by user + expiry)
```
