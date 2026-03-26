import sqlite3 as sql
import json
import os

_ALL_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

_HERE = os.path.dirname(os.path.abspath(__file__))


class Database:
    def __init__(self, *, create=False) -> None:
        # Connect to the SQLite file and enable foreign key enforcement
        self.db = sql.connect("db.sqlite3", check_same_thread=False)
        self.db.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.db.cursor()
        self.schema = self._generate_schema("schema.json")

        # If create=True, wipe and rebuild all tables from schema.json.
        # Only pass create=True once on first setup — it drops existing data.
        if create:
            for table in self.schema:
                cols = self.schema[table]
                colstring = ", ".join([f"{key} {cols[key]}" for key in cols])
                self._run(f"DROP TABLE IF EXISTS {table};")
                self._run(f"CREATE TABLE {table} ({colstring});")

    def insert(self, table: str, args: list):
        # Insert a new row into the given table. args must be ordered to match
        # the schema columns (excluding id, which is auto-assigned).
        assert table in self.schema
        placeholders = ", ".join(["?"] * len(args))
        cols = ", ".join([
            k for k, v in self.schema[table].items()
            if "PRIMARY KEY" not in v and not k.upper().startswith("FOREIGN KEY")
        ])
        print(cols)
        self._run_param(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", args)
        self._commit()

    def update(self, table: str, row_id: int, updates: dict) -> bool:
        # Update specific columns on a row identified by its id.
        # Pass only the fields you want to change — others are left alone.
        assert table in self.schema

        # Never allow the primary key to be changed via this method
        updates = {k: v for k, v in updates.items() if k != "id"}
        if not updates:
            return False

        fields = []
        values = []

        for col, val in updates.items():
            fields.append(f"{col} = ?")
            values.append(val)

        values.append(row_id)

        # Build the SET clause dynamically from whichever fields were passed in
        sql = f"""
            UPDATE {table}
            SET {", ".join(fields)}
            WHERE id = ?
        """

        self._run_param(sql, tuple(values))
        self._commit()

        return True

    def snooze(self, goal_id: int, weeks: int) -> bool:
        # Push a goal's active_date forward by N weeks from today, then snap back
        # to the nearest past Sunday. Also removes the goal's tasks from the
        # user's current week_schedule so they no longer appear on the calendar.
        from datetime import date, timedelta
        row = self._run_param("SELECT user_id FROM goals WHERE id = ?", (goal_id,)).fetchone()
        if row is None:
            return False
        user_id = row[0]

        # Shift from TODAY (not stale active_date), snap to nearest past Sunday
        # weekday() returns 0=Mon ... 6=Sun, so (weekday+1)%7 gives days since last Sunday
        shifted = date.today() + timedelta(weeks=weeks)
        days_since_sunday = (shifted.weekday() + 1) % 7
        new_active_date = (shifted - timedelta(days=days_since_sunday)).isoformat()
        self.update("goals", goal_id, {"active_date": new_active_date})

        # Remove this goal's tasks from the user's current week_schedule
        task_ids = {
            r[0] for r in self._run_param(
                "SELECT task_id FROM tasks WHERE goal_id = ?", (goal_id,)
            ).fetchall()
        }
        if task_ids:
            sched_row = self._run_param(
                "SELECT week_schedule FROM users WHERE username = ?", (user_id,)
            ).fetchone()
            if sched_row and sched_row[0]:
                schedule = json.loads(sched_row[0])
                for day in _ALL_DAYS:
                    if day in schedule:
                        schedule[day] = [e for e in schedule[day] if e["task_id"] not in task_ids]
                self._run_param(
                    "UPDATE users SET week_schedule = ? WHERE username = ?",
                    (json.dumps(schedule), user_id)
                )
                self._commit()

        return True

    def assign_weekly_tasks(self, user_id: str, this_sunday: str) -> dict:
        # Distribute the user's active tasks across their available days for the week.
        # Uses a simple round-robin: tasks sorted by impetus (urgency) get first pick
        # of days, and each task is spread evenly across its weekly_frequency slots.
        # Saves the resulting schedule to the user's week_schedule column and updates
        # each task's days_of_week column.
        from datetime import date
        today = date.today().isoformat()

        # Load the user's availability — a dict of full day name → hours, e.g. {"monday": 3, "wednesday": 2}
        row = self._run_param(
            "SELECT week_availability FROM users WHERE username = ?", (user_id,)
        ).fetchone()
        if not row or not row[0]:
            return {}
        avail = json.loads(row[0])
        avail_days = [k for k in avail if k in _ALL_DAYS]  # ordered available days
        if not avail_days:
            return {}

        # Fetch all tasks for active goals (active_date passed, end_date not yet reached),
        # sorted highest impetus first so urgent tasks get the best day slots
        tasks = self._run_param("""
            SELECT t.task_id, t.weekly_frequency, t.impetus
            FROM tasks t
            JOIN goals g ON t.goal_id = g.id
            WHERE g.user_id = ? AND g.active_date <= ? AND g.end_date >= ?
            ORDER BY t.impetus DESC
        """, (user_id, today, today)).fetchall()

        # Start with empty buckets for every day of the week
        buckets = {day: [] for day in _ALL_DAYS}
        n = len(avail_days)

        for task_id, freq, _ in tasks:
            freq = min(freq, n)           # can't schedule more times than available days
            step = max(1, n // freq)      # space out slots evenly across available days
            chosen = [avail_days[(i * step) % n] for i in range(freq)]
            for day in chosen:
                buckets[day].append({"task_id": task_id, "completed": False})
            # Persist which days this task is assigned to
            self._run_param(
                "UPDATE tasks SET days_of_week = ? WHERE task_id = ?",
                (json.dumps(chosen), task_id)
            )

        # Store the full schedule on the user row so the frontend can read it back.
        schedule = {
            "curr_week_start": this_sunday,
            **buckets,
        }
        self._run_param(
            "UPDATE users SET week_schedule = ? WHERE username = ?",
            (json.dumps(schedule), user_id)
        )
        self._commit()
        return schedule

    def check_new_week(self, user_id: str) -> tuple:
        # Called on app startup. Compares the most recent Sunday to the Sunday
        # stored in the user's week_schedule. If they differ it's a new week —
        # reassign tasks and return (True, new_schedule). If same week, return
        # the cached schedule without touching anything: (False, cached_schedule).
        from datetime import date, timedelta
        today = date.today()
        # (weekday()+1)%7 gives days elapsed since last Sunday (0 if today is Sunday)
        days_since_sunday = (today.weekday() + 1) % 7
        this_sunday = (today - timedelta(days=days_since_sunday)).isoformat()

        row = self._run_param(
            "SELECT week_schedule FROM users WHERE username = ?", (user_id,)
        ).fetchone()
        if not row:
            return False, {}

        stored = json.loads(row[0]) if row[0] else {}
        if stored.get("curr_week_start") == this_sunday:
            return False, stored  # already scheduled for this week

        # New week — rebuild the schedule
        schedule = self.assign_weekly_tasks(user_id, this_sunday)
        return True, schedule

    def get_daily_tasks(self, user_id: str) -> list:
        # Get today's task list from the stored week_schedule, then fetch full
        # task details + the parent goal name for each one.
        from datetime import date
        today_name = _ALL_DAYS[(date.today().weekday() + 1) % 7]  # e.g. "monday"

        row = self._run_param(
            "SELECT week_schedule FROM users WHERE username = ?", (user_id,)
        ).fetchone()
        if not row or not row[0]:
            return []

        schedule = json.loads(row[0])
        entries = schedule.get(today_name, [])
        if not entries:
            return []

        task_ids = [e["task_id"] for e in entries]
        done_by_id = {e["task_id"]: e["completed"] for e in entries}

        # Fetch task details alongside the goal name in one query
        placeholders = ", ".join(["?"] * len(task_ids))
        rows = self._run_param(f"""
            SELECT t.task_id, t.task, g.name AS goal_name
            FROM tasks t
            JOIN goals g ON t.goal_id = g.id
            WHERE t.task_id IN ({placeholders})
        """, task_ids).fetchall()

        return [
            {"task_id": r[0], "task": r[1], "goal_name": r[2], "completed": done_by_id.get(r[0], False)}
            for r in rows
        ]

    def set_task_status(self, user_id: str, task_id: int, status: bool) -> bool:
        # Mark a task as done or not-done in the user's current week_schedule.
        row = self._run_param(
            "SELECT week_schedule FROM users WHERE username = ?", (user_id,)
        ).fetchone()
        if not row or not row[0]:
            return False
        schedule = json.loads(row[0])
        from datetime import date
        today_name = _ALL_DAYS[(date.today().weekday() + 1) % 7]
        for entry in schedule.get(today_name, []):
            if entry["task_id"] == task_id:
                entry["completed"] = status
                break
        self._run_param(
            "UPDATE users SET week_schedule = ? WHERE username = ?",
            (json.dumps(schedule), user_id)
        )
        self._commit()
        return True

    def delete(self, table: str, id: int):
        # Remove a row by its id. Cascades to child rows where foreign keys are set up.
        assert table in self.schema
        self._run_param(f"DELETE FROM {table} WHERE id = ?", (id,))
        self._commit()

    def select(self, table: str, where: str):
        # Fetch rows from a table. Currently only supports "all" — returns every row.
        assert table in self.schema
        cursor = None
        match where:
            case "all":
                cursor = self._run(f"SELECT * FROM {table}")
            case _:
                cursor = self._run(f"SELECT * FROM {table}")
        return cursor.fetchall()

    def _run(self, s: str) -> sql.Cursor:
        print(s)
        return self.cursor.execute(s)

    def _run_param(self, s: str, params: list) -> sql.Cursor:
        print(s, params)
        return self.cursor.execute(s, params)

    def _commit(self) -> None:
        self.db.commit()

    def _generate_schema(self, filename: str) -> dict:
        # Load column definitions from schema.json. Each table maps column names
        # to their SQLite type strings (e.g. "TEXT NOT NULL").
        path = os.path.join(_HERE, filename)
        with open(path, "r", encoding="UTF-8") as f:
            schema = json.load(f)
            return schema


if __name__ == "__main__":
    db = Database(create=True)

    db.insert(
        "goals", ["run a 5k", "fitness", "completion", "testdate", "testdate2", "Rajt", "testdate"]
    )
    print(db.select("goals", "all"))
    db.update("goals", 1, {"name": "run a 10k", "user_id": "RajtRuns"})
    print(db.select("goals", "all"))

    # db.insert("tablename", ["", ""])
