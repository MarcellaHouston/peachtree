"""
Seed the SQLite database with sample data for the "Reach staff" user.

Run from the src/backend directory:
    python seed.py
"""

import json
from sql_db import Database

db = Database(create=True)

# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

db.insert(
    "users",
    [
        "Reach staff",
        "password",
        None,  # week_schedule — populated automatically by check_new_week
        json.dumps(
            {
                "monday": 5,
                "tuesday": 5,
                "wednesday": 5,
                "thursday": 5,
                "friday": 5,
                "saturday": 5,
                "sunday": 5,
            }
        ),
    ],
)

# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------

# insert args: name, description, measurable, start_date, end_date,
#              user_id, active_date, difficulty, category, days_of_week

db.insert(
    "goals",
    [
        "Improve Team Communication",
        "Hold regular syncs and improve async written communication across the org",
        "completion",
        "2026-01-01",
        "2026-12-31",
        "Reach staff",
        "2026-01-01",
        "medium",
        "Operations",
        "monday,tuesday,thursday,saturday",
    ],
)

db.insert(
    "goals",
    [
        "Grow Revenue by 20%",
        "Increase MRR through new accounts and expansion of existing ones",
        "scalar",
        "2026-01-01",
        "2026-12-31",
        "Reach staff",
        "2026-01-01",
        "high",
        "Sales",
        "monday,tuesday,thursday,saturday",
    ],
)

db.insert(
    "goals",
    [
        "Reduce Onboarding Time",
        "Cut the time-to-first-value for new users from 14 days to 7",
        "count",
        "2026-03-01",
        "2026-09-30",
        "Reach staff",
        "2026-03-01",
        "medium",
        "Product",
        "monday,tuesday,thursday,saturday",
    ],
)

db.insert(
    "goals",
    [
        "Increase Product NPS",
        "Push Net Promoter Score from 32 to 50 by end of year",
        "range",
        "2026-01-01",
        "2026-12-31",
        "Reach staff",
        "2026-01-01",
        "high",
        "Product",
        "monday,tuesday,thursday,saturday",
    ],
)

# ---------------------------------------------------------------------------
# Tasks  (goal_id, task, weekly_frequency, weight, days_of_week,
#          start_date, end_date, impetus)
# ---------------------------------------------------------------------------

goal_rows = db.select("goals", "all")
ids = {row[1]: row[0] for row in goal_rows}

# Goal: Improve Team Communication
db.insert(
    "tasks",
    [
        ids["Improve Team Communication"],
        "Send written team update",
        2,
        2,
        None,  # twice a week — enough to stay in sync without overdoing it
        "2026-01-01",
        "2026-12-31",
        4,
    ],
)
db.insert(
    "tasks",
    [
        ids["Improve Team Communication"],
        "Run 30-min all-hands sync",
        1,
        3,
        None,  # once a week — a recurring scheduled meeting
        "2026-01-01",
        "2026-12-31",
        3,
    ],
)
db.insert(
    "tasks",
    [
        ids["Improve Team Communication"],
        "Review and respond to async messages",
        5,
        1,
        None,  # daily Mon–Fri — keeping communication flowing every workday
        "2026-01-01",
        "2026-12-31",
        5,
    ],
)

# Goal: Grow Revenue by 20%
db.insert(
    "tasks",
    [
        ids["Grow Revenue by 20%"],
        "Review pipeline and follow up on open deals",
        5,
        2,
        None,  # daily Mon–Fri — pipeline hygiene needs consistent attention
        "2026-01-01",
        "2026-12-31",
        5,
    ],
)
db.insert(
    "tasks",
    [
        ids["Grow Revenue by 20%"],
        "Reach out to 2 new prospects",
        3,
        1,
        None,  # 3x a week — steady outreach without burning out the list
        "2026-01-01",
        "2026-12-31",
        4,
    ],
)
db.insert(
    "tasks",
    [
        ids["Grow Revenue by 20%"],
        "Log deal notes and update CRM",
        5,
        1,
        None,  # daily — keeping the record clean every day
        "2026-01-01",
        "2026-12-31",
        3,
    ],
)

# Goal: Reduce Onboarding Time
db.insert(
    "tasks",
    [
        ids["Reduce Onboarding Time"],
        "Review one onboarding session recording",
        3,
        1,
        None,  # 3x a week — enough coverage to spot patterns quickly
        "2026-03-01",
        "2026-09-30",
        3,
    ],
)
db.insert(
    "tasks",
    [
        ids["Reduce Onboarding Time"],
        "Update one section of the onboarding checklist",
        2,
        2,
        None,  # twice a week — incremental improvements add up fast
        "2026-03-01",
        "2026-09-30",
        2,
    ],
)
db.insert(
    "tasks",
    [
        ids["Reduce Onboarding Time"],
        "Check in with a new user about their onboarding experience",
        3,
        2,
        None,  # 3x a week — direct feedback loop with real users
        "2026-03-01",
        "2026-09-30",
        4,
    ],
)

# Goal: Increase Product NPS
db.insert(
    "tasks",
    [
        ids["Increase Product NPS"],
        "Read and tag NPS survey responses",
        4,
        1,
        None,  # 4x a week — staying on top of incoming feedback
        "2026-01-01",
        "2026-12-31",
        3,
    ],
)
db.insert(
    "tasks",
    [
        ids["Increase Product NPS"],
        "Share one product improvement idea with the team",
        2,
        1,
        None,  # twice a week — keeps the feedback loop active
        "2026-01-01",
        "2026-12-31",
        2,
    ],
)
db.insert(
    "tasks",
    [
        ids["Increase Product NPS"],
        "Follow up with a detractor from last month",
        2,
        2,
        None,  # twice a week — turning detractors around takes persistence
        "2026-01-01",
        "2026-12-31",
        4,
    ],
)

print("Seed complete.")
print(f"  {len(db.select('users', 'all'))} user(s)")
print(f"  {len(db.select('goals', 'all'))} goal(s)")
print(f"  {len(db.select('tasks', 'all'))} task(s)")
