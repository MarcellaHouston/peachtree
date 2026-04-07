# LLM Suggestions: Goal Guidance & Weekly Recap

## Overview

Two new LLM-powered features. **Goal Guidance** is the active build target. Weekly Recap is out of scope for now.

---

## 1. Goal Guidance

### Flow

```
User Input
  → POST /goals/guidance
      → LLM 1: GOAL_GUIDANCE → structured suggestions array
      → LLM 2: GOAL_GUIDANCE_SUMMARY → human-readable summary paragraph
      → Store guidance session transcript in ChromaDB
      ← Return { goal_id, suggestions, summary }
  → User selects suggestions
  → POST /goals/receive_suggestions
      → db.update("goals", ...) for each accepted suggestion field
      → db.assign_weekly_tasks(...) to reassign tasks for that goal
      ← Return { goal_id, applied_updates, schedule }
```

### Request — `/goals/guidance`

```json
POST /goals/guidance
{
  "user_id": "string",
  "goal_id": 42
}
```

### What We Send to LLM 1 (GOAL_GUIDANCE)

Assemble the following context before calling the LLM:

**1. Goal details** — fetched from `goals` table:
- `name`, `description`, `measurable`, `difficulty`, `start_date`, `end_date`, `days_of_week`, `category`

**2. Completion history** — derived from `week_schedule` on the `users` table:
- For each day in `week_schedule`, filter task entries whose `task_id` belongs to this goal (join via `tasks` table on `goal_id`)
- Compute: `tasks_completed` / `tasks_assigned` for the current week
- Also compute per-task completion rates if multiple tasks exist for the goal
- Note: `week_schedule` only stores the current week. If richer history is needed later, add a `task_completion_log` table (see § Future Considerations)

**3. All tasks for the goal** — fetched from `tasks` table where `goal_id` matches:
- `task`, `weekly_frequency`, `weight`, `impetus`

**4. Relevant talking points** — via ChromaDB RAG:
- Call `chroma.query(query_text=goal_name, user_id=user_id, n_results=5)`
- Returns top 5 semantically similar non-static talking points + all static user traits
- Pass `verbose_summary` for each result to the LLM

Assembled context object passed to LLM 1:

```json
{
  "goal": { ...goal fields... },
  "tasks": [ { "task": "...", "weekly_frequency": 3, "weight": 2, "impetus": 4 }, ... ],
  "completion_this_week": {
    "assigned": 6,
    "completed": 4,
    "rate": 0.67,
    "per_task": { "task_id_1": { "assigned": 3, "completed": 2 }, ... }
  },
  "user_context": [ "verbose_summary string 1", "verbose_summary string 2", ... ]
}
```

### LLM 1 Response (GOAL_GUIDANCE)

```json
{
  "suggestions": [
    {
      "field": "difficulty",
      "current_value": "hard",
      "suggested_value": "medium",
      "reasoning": "You've only completed 2 of 6 tasks this week and mentioned feeling overwhelmed."
    },
    {
      "field": "end_date",
      "current_value": "2026-06-01",
      "suggested_value": "2026-08-01",
      "reasoning": "At your current pace, the original deadline may be too aggressive."
    }
  ]
}
```

Valid `field` values: `difficulty`, `end_date`, `description`, `name`, `days_of_week`.

### LLM 2 Input (GOAL_GUIDANCE_SUMMARY)

Pass the `suggestions` array from LLM 1 as context. LLM 2 returns a plain string: a 2-3 sentence warm summary of what was noticed and why the suggestions would help.

### ChromaDB — Store Guidance Session

After both LLM calls, store the session as a talking point:
- `document`: `"Goal guidance for '{goal_name}'"`
- `verbose_summary`: full session narrative (summary + suggestions JSON)
- `static_trait`: `False`
- `end_timestamp`: now + 180 days

### Endpoint Response — `/goals/guidance`

```json
{
  "goal_id": 42,
  "suggestions": [ ...LLM 1 output... ],
  "summary": "...LLM 2 string output..."
}
```

Return HTTP 200 on success, 400 if goal not found or belongs to a different user.

---

### Request — `/goals/receive_suggestions`

```json
POST /goals/receive_suggestions
{
  "user_id": "string",
  "goal_id": 42,
  "suggestions": [
    {
      "field": "difficulty",
      "current_value": "hard",
      "suggested_value": "medium",
      "reasoning": "..."
    }
  ]
}
```

Only the suggestions the user accepted should be included in this array.

### Endpoint Logic — `/goals/receive_suggestions`

1. Validate `user_id` and `goal_id`; return 400 if goal not found or user mismatch
2. For each suggestion, apply `db.update("goals", goal_id, {field: suggested_value})`
   - Only allowed fields: `difficulty`, `end_date`, `description`, `name`, `days_of_week`
3. Call `db.assign_weekly_tasks(user_id, db.this_sunday())` to reassign tasks
4. Return `{ goal_id, applied_updates, schedule }`

---

## 2. New LLM Use Cases

Add two entries to the `UseCase` enum in `bedrock/llm.py` (continuing from existing integers):

```python
GOAL_GUIDANCE = 4          # strength=3 (27B Gemma) — generates structured suggestions
GOAL_GUIDANCE_SUMMARY = 5  # strength=2 (12B Gemma) — summarizes suggestions into prose
```

### Prompt Files

Create two new files under `bedrock/prompts/`:

**`goal_guidance.txt`**

```
You are a personal development coach helping a user improve their goal.
You will receive: goal details, tasks, the user's completion rate this week, and relevant personal context.

Respond with a JSON object in this exact format:
{
  "suggestions": [
    {
      "field": "<goal field name>",
      "current_value": "<current value or null>",
      "suggested_value": "<your recommendation>",
      "reasoning": "<1-2 sentences grounded in the provided context>"
    }
  ]
}

Rules:
- Only suggest changes genuinely warranted by the data. Limit to 3 suggestions maximum.
- Only use these field names: difficulty, end_date, description, name, days_of_week.
- Base reasoning on completion rate and user context. Do not invent facts.
- If no changes are warranted, return an empty suggestions array.

Goal and context:
{context}
```

**`goal_guidance_summary.txt`**

```
You are a personal development coach. You have just generated a set of suggestions for a user's goal.
Summarize these suggestions in 2-3 sentences in a warm, encouraging tone. Explain what you noticed and why the changes would help.

Suggestions:
{context}
```

---

## 3. Implementation Steps

### Step 1 — Add prompt files
Create `bedrock/prompts/goal_guidance.txt` and `bedrock/prompts/goal_guidance_summary.txt` with the content above.

### Step 2 — Extend `LLMClient` in `bedrock/llm.py`
- Add `GOAL_GUIDANCE = 4` and `GOAL_GUIDANCE_SUMMARY = 5` to `UseCase` enum
- Add strength mappings: `GOAL_GUIDANCE → 3`, `GOAL_GUIDANCE_SUMMARY → 2`
- Add response validation for `GOAL_GUIDANCE`:
  - Top-level `suggestions` key is a list
  - Each item has `field`, `current_value`, `suggested_value`, `reasoning`
  - `field` is in `["difficulty", "end_date", "description", "name", "days_of_week"]`
- `GOAL_GUIDANCE_SUMMARY` returns a plain string (same pattern as `SUMMARIZE_TRANSCRIPTION`)

### Step 3 — Add helper to `sql_db.py`
Add `get_goal_completion_this_week(user_id, goal_id)`:
1. Fetch `week_schedule` from `users` table for `user_id`
2. Fetch all `task_id`s for `goal_id` from `tasks` table
3. For each day in `week_schedule`, filter entries to this goal's task_ids
4. Accumulate assigned / completed counts and per-task breakdown
5. Return:
```python
{
  "assigned": n,
  "completed": m,
  "rate": m / n if n > 0 else 0.0,
  "per_task": { task_id: {"assigned": x, "completed": y}, ... }
}
```

### Step 4 — Add `POST /goals/guidance` to `app.py`
1. Validate `user_id` and `goal_id`
2. Fetch goal; return 400 if not found or user mismatch
3. Fetch tasks for goal
4. Call `db.get_goal_completion_this_week(user_id, goal_id)`
5. Call `chroma.query(goal["name"], user_id=user_id, n_results=5)` → extract `verbose_summary` list
6. Assemble context dict
7. Call `LLMClient(UseCase.GOAL_GUIDANCE)` → get suggestions
8. Call `LLMClient(UseCase.GOAL_GUIDANCE_SUMMARY)` with suggestions JSON → get summary (non-fatal on failure)
9. Store session in ChromaDB via `chroma.store_talking_point(...)`
10. Return `{ goal_id, suggestions, summary }`

### Step 5 — Add `POST /goals/receive_suggestions` to `app.py`
1. Validate `user_id`, `goal_id`, `suggestions` list
2. Fetch goal; return 400 if not found or user mismatch
3. Build `updates` dict from accepted suggestions (whitelist fields)
4. Call `db.update("goals", goal_id, updates)` if non-empty
5. Call `db.assign_weekly_tasks(user_id, db.this_sunday())`
6. Return `{ goal_id, applied_updates, schedule }`

---

## 4. Endpoints Summary

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/goals/guidance` | POST | `{ user_id, goal_id }` | `{ goal_id, suggestions[], summary }` |
| `/goals/receive_suggestions` | POST | `{ user_id, goal_id, suggestions[] }` | `{ goal_id, applied_updates, schedule }` |

---

## 5. Out of Scope (this pass)

- Weekly Recap (`/goals/weekly_recap`) — deferred
- `task_completion_log` table for multi-week history (see § Future Considerations)
- Rate limiting / cost optimization

---

## 6. Future Considerations

**Completion history beyond the current week:** `week_schedule` only stores the current week. If the LLM would benefit from multi-week trends, add a `task_completion_log` table:

```sql
CREATE TABLE task_completion_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  task_id INTEGER NOT NULL,
  goal_id INTEGER NOT NULL,
  week_start TEXT NOT NULL,
  assigned INTEGER NOT NULL,
  completed INTEGER NOT NULL
);
```

Populate it at the end of each week during `check_new_week()`. Then `get_goal_completion_this_week` can optionally return the last N weeks.

**Weekly Recap (`/goals/weekly_recap`):** Batch version covering all active goals at once. Same LLM pattern but scoped to all goals. Add `WEEKLY_RECAP` use case at strength=3. Deferred until Goal Guidance is validated.

**Rate limiting:** Both guidance LLM calls use the 27B and 12B models. If cost becomes a concern, `GOAL_GUIDANCE` could fall back to strength 2 for users with simple goals.
