"""
Seed the SQLite database with sample data for the "Reach staff" user.

Run from the src/backend directory:
    python seed.py
"""

import json
from sql_db import Database

db = Database(create=False)

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

print("Seed complete.")
print(f"  {len(db.select('users', 'all'))} user(s)")
