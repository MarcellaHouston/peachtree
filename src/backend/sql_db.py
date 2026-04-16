import sqlite3 as sql
import json
import os
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

_ALL_DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def _parse_days(days) -> list:
    if not days:
        return []
    if isinstance(days, str):
        try:
            parsed = json.loads(days)
        except json.JSONDecodeError:
            parsed = days.split(",")
    else:
        parsed = days
    if isinstance(parsed, str):
        parsed = parsed.split(",")
    return [
        day.strip().lower()
        for day in parsed
        if isinstance(day, str) and day.strip().lower() in _ALL_DAYS
    ]

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
        cols = ", ".join(
            [
                k
                for k, v in self.schema[table].items()
                if "PRIMARY KEY" not in v and not k.upper().startswith("FOREIGN KEY")
            ]
        )
        # print(cols)
        self._run_param(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", args)
        self._commit()
        return self.cursor.lastrowid

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

    def adjust_goal_completion(
        self, goal_id: int, completed_delta: int, all_delta: int
    ) -> None:
        # Apply deltas to a goal's persistent completion counters and recompute %.
        # Counters are clamped at 0 so they never go negative even on stale undos.
        row = self._run_param(
            "SELECT completion FROM goals WHERE id = ?", (goal_id,)
        ).fetchone()
        if not row:
            return
        c = (
            json.loads(row[0])
            if row[0]
            else {"completed_tasks": 0, "all_tasks": 0, "percent_completed": 0}
        )
        c["completed_tasks"] = max(0, c["completed_tasks"] + completed_delta)
        c["all_tasks"] = max(0, c["all_tasks"] + all_delta)
        c["percent_completed"] = (
            round(c["completed_tasks"] / c["all_tasks"] * 100)
            if c["all_tasks"] > 0
            else 0
        )
        self._run_param(
            "UPDATE goals SET completion = ? WHERE id = ?",
            (json.dumps(c), goal_id),
        )
        self._commit()

    def snooze(self, goal_id: int, weeks: int) -> bool:
        # Push a goal's active_date forward by N weeks from today, then snap back
        # to the nearest past Sunday. Also removes the goal's tasks from the
        # user's current week_schedule so they no longer appear on the calendar.
        from datetime import date, timedelta

        row = self._run_param(
            "SELECT user_id FROM goals WHERE id = ?", (goal_id,)
        ).fetchone()
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
            r[0]
            for r in self._run_param(
                "SELECT task_id FROM tasks WHERE goal_id = ?", (goal_id,)
            ).fetchall()
        }
        if task_ids:
            sched_row = self._run_param(
                "SELECT week_schedule FROM users WHERE username = ?", (user_id,)
            ).fetchone()
            if sched_row and sched_row[0]:
                schedule = json.loads(sched_row[0])
                # Count how many of this goal's task instances we're removing,
                # and how many were already marked complete — these need to be
                # rolled back from the goal's cumulative completion counters.
                removed_total = 0
                removed_completed = 0
                for day in _ALL_DAYS:
                    if day in schedule:
                        kept = []
                        for e in schedule[day]:
                            if e["task_id"] in task_ids:
                                removed_total += 1
                                if e.get("completed"):
                                    removed_completed += 1
                            else:
                                kept.append(e)
                        schedule[day] = kept
                self._run_param(
                    "UPDATE users SET week_schedule = ? WHERE username = ?",
                    (json.dumps(schedule), user_id),
                )
                self._commit()
                if removed_total:
                    self.adjust_goal_completion(
                        goal_id, -removed_completed, -removed_total
                    )

        return True

    def assign_weekly_tasks(self, user_id: str, this_sunday: str) -> dict:
        # Distribute the user's active tasks across their available days for the week.
        # Uses a simple round-robin: tasks sorted by impetus (urgency) get first pick
        # of days, and each task is spread evenly across its weekly_frequency slots.
        # Saves the resulting schedule to the user's week_schedule column and updates
        # each task's days_of_week column.
        from datetime import date

        # if a schedule already exists for this week, subtract the number from total
        today = date.today().isoformat()
        logger.info(
            "📅 Assigning weekly tasks for user=%s week_start=%s",
            user_id,
            this_sunday,
        )

        # Load the user's availability — a dict of full day name → hours, e.g. {"monday": 3, "wednesday": 2}
        row = self._run_param(
            "SELECT week_availability FROM users WHERE username = ?", (user_id,)
        ).fetchone()
        if not row:
            logger.warning(
                "📅 Weekly task assignment skipped: no user row for username=%s",
                user_id,
            )
            return {}
        if not row[0]:
            logger.warning(
                "📅 Weekly task assignment skipped for user=%s: week_availability is empty",
                user_id,
            )
            return {}
        avail = json.loads(row[0])
        avail_days = [k for k in avail if k in _ALL_DAYS]  # ordered available days
        if not avail_days:
            logger.warning(
                "📅 Weekly task assignment skipped for user=%s: no valid availability days in %s",
                user_id,
                avail,
            )
            return {}
        logger.info(
            "📅 Weekly availability for user=%s: %s",
            user_id,
            ",".join(avail_days),
        )

        # If a schedule already exists for THIS same week (e.g. create_goal
        # triggered a mid-week rebuild), tally how many instances each goal
        # already contributed to cumulative all_tasks. After the rebuild we
        # apply only the *delta* so a same-week re-assignment doesn't
        # double-count. On a true new-week rollover (different curr_week_start)
        # the previous week's contribution is permanent history, so we leave
        # prev_all_counts empty and add the full new totals.
        # Note: we deliberately do NOT touch completed_tasks here — the user's
        # historical progress should be preserved across rebuilds.
        prev_row = self._run_param(
            "SELECT week_schedule FROM users WHERE username = ?", (user_id,)
        ).fetchone()
        prev_all_counts: dict = {}
        if prev_row and prev_row[0]:
            prev_sched = json.loads(prev_row[0])
            if prev_sched.get("curr_week_start") == this_sunday:
                prev_task_ids = set()
                for day in _ALL_DAYS:
                    for e in prev_sched.get(day, []):
                        prev_task_ids.add(e["task_id"])
                if prev_task_ids:
                    placeholders = ",".join(["?"] * len(prev_task_ids))
                    tid_to_gid = dict(
                        self._run_param(
                            f"SELECT task_id, goal_id FROM tasks WHERE task_id IN ({placeholders})",
                            list(prev_task_ids),
                        ).fetchall()
                    )
                    for day in _ALL_DAYS:
                        for e in prev_sched.get(day, []):
                            gid = tid_to_gid.get(e["task_id"])
                            if gid is not None:
                                prev_all_counts[gid] = prev_all_counts.get(gid, 0) + 1

        # Fetch all tasks for active goals (active_date passed, end_date not yet reached),
        # sorted highest impetus first so urgent tasks get the best day slots
        tasks = self._run_param(
            """
            SELECT t.task_id, t.weekly_frequency, t.impetus, t.goal_id, t.days_of_week, g.days_of_week
            FROM tasks t
            JOIN goals g ON t.goal_id = g.id
            WHERE g.user_id = ? AND g.active_date <= ? AND g.end_date >= ?
            ORDER BY t.impetus DESC
        """,
            (user_id, today, today),
        ).fetchall()
        logger.info(
            "📅 Found %d active task(s) for user=%s on %s",
            len(tasks),
            user_id,
            today,
        )

        # Start with empty buckets for every day of the week
        buckets = {day: [] for day in _ALL_DAYS}
        # Track how many instances each goal gets so we can bump its
        # cumulative all_tasks counter once at the end.
        goal_instance_counts: dict = {}

        for task_id, freq, _, goal_id, task_days_of_week, goal_days_of_week in tasks:
            # Prefer the generated task's own days. Fall back to the goal's allowed
            # days for older rows that do not have task-level days yet.
            task_days = _parse_days(task_days_of_week)
            goal_days = _parse_days(goal_days_of_week)
            allowed_days = task_days or goal_days
            if allowed_days:
                eligible_days = [d for d in avail_days if d in allowed_days]
            else:
                eligible_days = avail_days
            if not eligible_days:
                logger.info(
                    "📅 Skipping task_id=%s for user=%s: no overlap between availability=%s and allowed_days=%s",
                    task_id,
                    user_id,
                    avail_days,
                    allowed_days,
                )
                continue
            n = len(eligible_days)
            step = max(1, n // min(freq, n))  # space out slots evenly across eligible days
            chosen = [eligible_days[(i * step) % n] for i in range(freq)]
            logger.info(
                "📅 Scheduling task_id=%s for user=%s on %s",
                task_id,
                user_id,
                ",".join(chosen),
            )
            for day in chosen:
                buckets[day].append({"task_id": task_id, "completed": False})
            goal_instance_counts[goal_id] = goal_instance_counts.get(goal_id, 0) + len(
                chosen
            )
            # Persist which days this task is assigned to
            self._run_param(
                "UPDATE tasks SET days_of_week = ? WHERE task_id = ?",
                (json.dumps(chosen), task_id),
            )

        # Store the full schedule on the user row so the frontend can read it back.
        schedule = {
            "curr_week_start": this_sunday,
            **buckets,
        }
        self._run_param(
            "UPDATE users SET week_schedule = ? WHERE username = ?",
            (json.dumps(schedule), user_id),
        )
        self._commit()
        scheduled_count = sum(len(schedule[day]) for day in _ALL_DAYS)
        logger.info(
            "📅 Weekly task assignment saved for user=%s: %d scheduled task instance(s)",
            user_id,
            scheduled_count,
        )

        # Apply per-goal all_tasks deltas. For a same-week rebuild, prev_all_counts
        # holds what was already counted, so the delta is the difference. For a new
        # week (or first-ever schedule), prev_all_counts is empty and the delta
        # equals the full new total.
        for gid in set(goal_instance_counts) | set(prev_all_counts):
            delta = goal_instance_counts.get(gid, 0) - prev_all_counts.get(gid, 0)
            if delta != 0:
                self.adjust_goal_completion(gid, 0, delta)

        return schedule

    def this_sunday(self) -> str:
        today = date.today()
        # (weekday()+1)%7 gives days elapsed since last Sunday (0 if today is Sunday)
        days_since_sunday = (today.weekday() + 1) % 7
        this_sunday = (today - timedelta(days=days_since_sunday)).isoformat()
        return this_sunday

    def get_week_schedule(self, user_id: str) -> dict:
        # Return the stored week_schedule for a user without triggering reassignment.
        row = self._run_param(
            "SELECT week_schedule FROM users WHERE username = ?", (user_id,)
        ).fetchone()
        if not row or not row[0]:
            return {}
        return json.loads(row[0])

    def check_new_week(self, user_id: str) -> tuple:
        # Called on app startup. Compares the most recent Sunday to the Sunday
        # stored in the user's week_schedule. If they differ it's a new week —
        # reassign tasks and return (True, new_schedule). If same week, return
        # the cached schedule without touching anything: (False, cached_schedule).

        this_sunday = self.this_sunday()

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

        today_name = _ALL_DAYS[(date.today().weekday()) % 7]  # e.g. "monday"

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
        rows = self._run_param(
            f"""
            SELECT t.task_id, t.task, g.name AS goal_name
            FROM tasks t
            JOIN goals g ON t.goal_id = g.id
            WHERE t.task_id IN ({placeholders})
        """,
            task_ids,
        ).fetchall()

        return [
            {
                "task_id": r[0],
                "task": r[1],
                "goal_name": r[2],
                "completed": done_by_id.get(r[0], False),
            }
            for r in rows
        ]

    def set_task_status(self, user_id: str, task_id: int, status: bool) -> bool:
        # Mark a task as done or not-done in the user's current week_schedule.
        # Also bumps the parent goal's cumulative completion counter, but only
        # if the entry's status actually changed (so a no-op call is a no-op).
        row = self._run_param(
            "SELECT week_schedule FROM users WHERE username = ?", (user_id,)
        ).fetchone()
        if not row or not row[0]:
            return False
        schedule = json.loads(row[0])
        from datetime import date

        today_name = _ALL_DAYS[(date.today().weekday()) % 7]
        changed = False
        for entry in schedule.get(today_name, []):
            if entry["task_id"] == task_id:
                if entry.get("completed") != status:
                    entry["completed"] = status
                    changed = True
                break
        self._run_param(
            "UPDATE users SET week_schedule = ? WHERE username = ?",
            (json.dumps(schedule), user_id),
        )
        self._commit()

        if changed:
            goal_row = self._run_param(
                "SELECT goal_id FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if goal_row:
                self.adjust_goal_completion(goal_row[0], 1 if status else -1, 0)
        return True

    def get_user_token(self, user_id: int) -> str:
        # Get the token used for authorization for a user
        row = self._run_param(
            "SELECT token FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row:
            token = row[0]
            return token
        else:
            return ""

    def get_user_id(self, username: str) -> int:
        row = self._run_param(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row:
            return row[0]
        return -1

    def check_for_username(self, username: str) -> bool:
        row = self._run_param(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row:
            return True
        return False

    def get_user_login(self, username: str) -> dict:
        # Used for login primarily right now
        fetch_data = self._run_param(
            "SELECT id, password FROM users WHERE username = ?", (username,)
        ).fetchone()
        user_data = {"User-ID": "", "password": ""}
        if not fetch_data:
            return user_data
        user_data["User-ID"] = fetch_data[0]
        user_data["password"] = fetch_data[1]
        return user_data

    def get_glicko_task_data(self, taskid: int) -> dict:
        # Get data needed for Glicko algorithm from a task and its overarching goal
        fetch_data = self._run_param(
            "SELECT impetus, difficulty_score, goal_id FROM tasks WHERE task_id = ?",
            (taskid,),
        ).fetchone()
        task_data = {"impetus": 0, "difficulty_score": 0, "goal_difficulty": ""}
        if fetch_data is None:
            return None
        task_data["impetus"] = fetch_data[0]
        task_data["difficulty_score"] = fetch_data[1]
        goal_id = fetch_data[2]

        # Get difficulty of the overarching goal for this task
        goal_diff = self._run_param(
            "SELECT difficulty FROM goals WHERE id = ?", (goal_id,)
        ).fetchone()
        if goal_diff:
            task_data["goal_difficulty"] = goal_diff[0]
        return task_data

    def update_user_glicko(
        self, user_id: int, rating: int, RD: float, volatility: float
    ):
        self._run_param(
            "UPDATE users SET rating = ?, deviation = ?, volatility = ? WHERE id = ?",
            (rating, RD, volatility, user_id),
        )
        self._commit()

    def get_glicko_rating(self, user_id: str) -> int:
        fetch_data = self._run_param(
            "SELECT rating FROM users WHERE username = ?", (user_id,)
        ).fetchone()
        if not fetch_data:
            return 1500
        return fetch_data[0]

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
        # print(s)
        return self.cursor.execute(s)

    def _run_param(self, s: str, params: list) -> sql.Cursor:
        # print(s, params)
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
        "goals",
        [
            "run a 5k",
            "fitness",
            "completion",
            "testdate",
            "testdate2",
            "Rajt",
            "testdate",
        ],
    )
    print(db.select("goals", "all"))
    db.update("goals", 1, {"name": "run a 10k", "user_id": "RajtRuns"})
    print(db.select("goals", "all"))

    # db.insert("tablename", ["", ""])
