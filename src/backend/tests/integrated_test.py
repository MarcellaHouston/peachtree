import unittest
import sqlite3
from unittest.mock import patch
from datetime import date
import json

import app as app_module
from sql_db import Database

# Grab the Flask app instance for use with the test client
flask_app = app_module.app


def make_real_db():
    """
    Create a real Database instance backed by an in-memory SQLite connection.

    Database.__init__ hardcodes "db.sqlite3" as the file path, so we
    temporarily patch sqlite3.connect to redirect any path to :memory:.
    create=True drops and recreates all tables from schema.json, giving
    each test a clean slate.
    """
    # Open the in-memory connection ourselves so we control its lifetime
    real_conn = sqlite3.connect(":memory:", check_same_thread=False)
    # Patch sqlite3.connect so that when Database.__init__ calls
    # sql.connect("db.sqlite3", ...) it gets our in-memory connection instead
    with patch("sqlite3.connect", return_value=real_conn):
        db = Database(create=True)
    return db


# ---------------------------------------------------------------------------
# Shared base class for integration tests
# ---------------------------------------------------------------------------


class _FakeLLMClient:
    """Stand-in for LLMClient that avoids any network/AWS calls in tests.
    Returns an empty task list with valid=True so /goals/create succeeds
    without inserting any tasks; tests that need tasks insert them directly
    via _insert_task."""
    class UseCase:
        GENERATE_TASKS = "GENERATE_TASKS"

    def __init__(self, *args, **kwargs):
        pass

    def query(self, *args, **kwargs):
        return [], True, 0


class IntegrationTestCase(unittest.TestCase):
    def setUp(self):
        flask_app.config["TESTING"] = True
        self.client = flask_app.test_client()

        # Build a fresh in-memory DB for this test, then swap it into the app.
        # Each test gets its own connection so tests are fully independent.
        self.real_db = make_real_db()
        self.db_patch = patch.object(app_module, "db", self.real_db)
        self.db_patch.start()

        # Replace LLMClient with a fake so /goals/create doesn't reach AWS.
        self.llm_patch = patch.object(app_module, "LLMClient", _FakeLLMClient)
        self.llm_patch.start()

    def tearDown(self):
        # Restore patches and close the in-memory connection
        self.llm_patch.stop()
        self.db_patch.stop()
        self.real_db.db.close()

    def post_json(self, url, data):
        return self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

    def _insert_task(self, goal_id, weekly_frequency=2, weight=1, impetus=3):
        self.real_db._run_param(
            """INSERT INTO tasks (goal_id, task, weekly_frequency, weight,
               start_date, end_date, impetus)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (goal_id, "Do the thing", weekly_frequency, weight,
             date.today().isoformat(), "2027-12-31", impetus)
        )
        self.real_db._commit()

    def create_goal(self, **overrides):
        """
        POST a valid goal to /goals/create and assert it was accepted (204).
        Keyword args are merged into the payload so individual tests can
        customise specific fields without repeating the full payload.
        """
        payload = {
            "goal": {
                "name": "Run 5k",
                "measurable": "completion",
                "end_date": "2027-12-31",
                "user_id": "alice",
                "difficulty": "medium",
                **overrides,
            }
        }
        resp = self.post_json("/goals/create", payload)
        self.assertEqual(resp.status_code, 204, resp.get_data(as_text=True))
        return payload["goal"]


# ---------------------------------------------------------------------------
# POST /goals/create  (integration)
# ---------------------------------------------------------------------------


class TestCreateGoalIntegration(IntegrationTestCase):
    def test_create_persists_to_db(self):
        # The core integration check: creating a goal via the API should
        # result in exactly one row in the real DB
        self.create_goal()
        rows = self.real_db.select("goals", "all")
        self.assertEqual(len(rows), 1)

    def test_created_goal_fields_stored_correctly(self):
        # Verify that every field in the request ends up in the right column.
        # Row columns: (id, name, description, measurable, start_date, end_date, user)
        self.create_goal(
            name="Meditate",
            user_id="bob",
            measurable="count",
            start_date="2026-01-01",
            end_date="2026-12-31",
        )
        rows = self.real_db.select("goals", "all")
        row = rows[0]
        self.assertEqual(row[1], "Meditate")
        self.assertEqual(row[3], "count")
        self.assertEqual(row[4], "2026-01-01")
        self.assertEqual(row[5], "2026-12-31")
        self.assertEqual(row[6], "bob")
        self.assertEqual(row[7], "2026-01-01")  # active_date == start_date on create

    def test_default_start_date_stored_as_today(self):
        # start_date is optional in the API; the app should default it to
        # today and that value should reach the DB
        self.create_goal()
        rows = self.real_db.select("goals", "all")
        self.assertEqual(rows[0][4], date.today().isoformat())

    def test_multiple_goals_all_persisted(self):
        # Creating two goals should result in two rows, not one overwriting the other
        self.create_goal(name="Goal A")
        self.create_goal(name="Goal B")
        rows = self.real_db.select("goals", "all")
        self.assertEqual(len(rows), 2)

    def test_description_optional(self):
        # description is not required; when omitted it should be stored as NULL
        self.create_goal()
        rows = self.real_db.select("goals", "all")
        self.assertIsNone(rows[0][2])

    def test_description_stored_when_provided(self):
        self.create_goal(description="Daily mindfulness")
        rows = self.real_db.select("goals", "all")
        self.assertEqual(rows[0][2], "Daily mindfulness")


# ---------------------------------------------------------------------------
# POST /goals  (integration)
# ---------------------------------------------------------------------------


class TestGetGoalsIntegration(IntegrationTestCase):
    def test_get_goals_empty_db(self):
        # With nothing in the DB the endpoint should return an empty list
        body = self.post_json("/goals", {}).get_json()
        self.assertEqual(body["goals"], [])

    def test_get_goals_returns_inserted_goal(self):
        # A goal that was just created should appear when queried
        self.create_goal(
            name="Yoga", start_date=date.today().isoformat(), end_date="2027-12-31"
        )
        body = self.post_json(
            "/goals",
            {
                "start_date": date.today().isoformat(),
                "end_date": "2027-12-31",
            },
        ).get_json()
        self.assertEqual(len(body["goals"]), 1)
        self.assertEqual(body["goals"][0]["name"], "Yoga")

    def test_get_goals_date_filter_excludes_old_goal(self):
        # A goal whose end_date is before the filter's start_date should be excluded.
        # This confirms the real date-filtering logic works end-to-end, not just in isolation.
        self.create_goal(start_date="2020-01-01", end_date="2020-12-31")
        body = self.post_json("/goals", {"start_date": "2025-01-01"}).get_json()
        self.assertEqual(body["goals"], [])

    def test_get_goals_returns_multiple(self):
        # All goals in the matching date range should be returned
        self.create_goal(
            name="A", start_date=date.today().isoformat(), end_date="2027-01-01"
        )
        self.create_goal(
            name="B", start_date=date.today().isoformat(), end_date="2027-01-01"
        )
        body = self.post_json(
            "/goals",
            {
                "start_date": date.today().isoformat(),
                "end_date": "2027-12-31",
            },
        ).get_json()
        names = [g["name"] for g in body["goals"]]
        self.assertIn("A", names)
        self.assertIn("B", names)

    def test_get_goals_response_shape(self):
        # Check that every expected key is present in each returned goal object
        self.create_goal(start_date=date.today().isoformat())
        body = self.post_json(
            "/goals",
            {
                "start_date": date.today().isoformat(),
                "end_date": "2027-12-31",
            },
        ).get_json()
        g = body["goals"][0]
        for key in (
            "id",
            "name",
            "description",
            "measurable",
            "start_date",
            "end_date",
            "user_id",
            "active_date",
            "difficulty",
            "category",
            "days_of_week",
            "isPaused",
        ):
            self.assertIn(key, g)

    def test_get_goals_with_user_id_includes_schedule(self):
        self.real_db._run_param(
            "INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?)",
            ("alice", "pw", json.dumps({"monday": 3}))
        )
        self.real_db._commit()
        body = self.post_json("/goals", {"user_id": "alice"}).get_json()
        self.assertIn("new_week", body)
        self.assertIn("schedule", body)
        self.assertIn("goals", body)

    def test_get_goals_without_user_id_omits_schedule(self):
        body = self.post_json("/goals", {}).get_json()
        self.assertNotIn("new_week", body)
        self.assertNotIn("schedule", body)

    def test_is_paused_false_for_active_goal(self):
        self.create_goal(start_date=date.today().isoformat())
        body = self.post_json("/goals", {"start_date": date.today().isoformat(), "end_date": "2027-12-31"}).get_json()
        self.assertFalse(body["goals"][0]["isPaused"])

    def test_is_paused_true_after_snooze(self):
        self.create_goal(start_date=date.today().isoformat(), end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        self.post_json("/goals/snooze", {"id": goal_id, "weeks": 4})
        body = self.post_json("/goals", {"start_date": date.today().isoformat(), "end_date": "2027-12-31"}).get_json()
        self.assertTrue(body["goals"][0]["isPaused"])


# ---------------------------------------------------------------------------
# POST /goals/update  (integration)
# ---------------------------------------------------------------------------


class TestUpdateGoalIntegration(IntegrationTestCase):
    def _inserted_id(self):
        """Insert one goal and return its auto-assigned DB id."""
        self.create_goal()
        rows = self.real_db.select("goals", "all")
        return rows[0][0]

    def test_update_changes_name_in_db(self):
        # After updating via the API, querying the DB directly should show the new value
        goal_id = self._inserted_id()
        self.post_json(
            "/goals/update",
            {
                "goal": {
                    "id": goal_id,
                    "name": "Run 10k",
                    "measurable": "completion",
                    "end_date": "2027-12-31",
                    "user_id": "alice",
                    "difficulty": "medium",
                }
            },
        )
        rows = self.real_db.select("goals", "all")
        self.assertEqual(rows[0][1], "Run 10k")

    def test_update_returns_204(self):
        goal_id = self._inserted_id()
        resp = self.post_json(
            "/goals/update",
            {
                "goal": {
                    "id": goal_id,
                    "name": "Updated",
                    "measurable": "scalar",
                    "end_date": "2027-06-01",
                    "user_id": "alice",
                    "difficulty": "medium",
                }
            },
        )
        self.assertEqual(resp.status_code, 204)

    def test_update_only_affects_target_row(self):
        # With two goals in the DB, updating one should leave the other unchanged
        self.create_goal(name="Goal One")
        self.create_goal(name="Goal Two")
        rows = self.real_db.select("goals", "all")
        first_id = rows[0][0]

        self.post_json(
            "/goals/update",
            {
                "goal": {
                    "id": first_id,
                    "name": "Goal One Modified",
                    "measurable": "completion",
                    "end_date": "2027-12-31",
                    "user_id": "alice",
                    "difficulty": "medium",
                }
            },
        )

        rows = self.real_db.select("goals", "all")
        names = {row[0]: row[1] for row in rows}
        self.assertEqual(names[first_id], "Goal One Modified")
        other_names = [n for id_, n in names.items() if id_ != first_id]
        self.assertEqual(other_names, ["Goal Two"])

    def test_update_nonexistent_id_still_204(self):
        # app.py doesn't verify the row existed before updating.
        # This test documents that behaviour: a no-op update returns 204 silently.
        # This is only detectable through integration testing — the mock in test.py
        # would pass regardless of whether the DB row actually existed.
        resp = self.post_json(
            "/goals/update",
            {
                "goal": {
                    "id": 9999,
                    "name": "Ghost",
                    "measurable": "count",
                    "end_date": "2027-01-01",
                    "user_id": "nobody",
                    "difficulty": "low",
                }
            },
        )
        self.assertEqual(resp.status_code, 204)


# ---------------------------------------------------------------------------
# POST /goals/snooze  (integration)
# ---------------------------------------------------------------------------


class TestSnoozeGoalIntegration(IntegrationTestCase):
    def _create_and_get_id(self, **overrides):
        self.create_goal(**overrides)
        rows = self.real_db.select("goals", "all")
        return rows[-1][0]  # last inserted row

    def _expected_snooze_date(self, weeks):
        # Compute expected active_date: today + N weeks, snapped to nearest past Sunday
        from datetime import timedelta
        shifted = date.today() + timedelta(weeks=weeks)
        days_since_sunday = (shifted.weekday() + 1) % 7
        return (shifted - timedelta(days=days_since_sunday)).isoformat()

    def test_snooze_pushes_active_date_forward(self):
        goal_id = self._create_and_get_id(start_date="2026-01-01", end_date="2027-12-31")
        resp = self.post_json("/goals/snooze", {"id": goal_id, "weeks": 2})
        self.assertEqual(resp.status_code, 204)
        rows = self.real_db.select("goals", "all")
        self.assertEqual(rows[0][7], self._expected_snooze_date(2))

    def test_snooze_does_not_change_start_date(self):
        goal_id = self._create_and_get_id(start_date="2026-01-01", end_date="2027-12-31")
        self.post_json("/goals/snooze", {"id": goal_id, "weeks": 3})
        rows = self.real_db.select("goals", "all")
        self.assertEqual(rows[0][4], "2026-01-01")  # start_date unchanged

    def test_snooze_nonexistent_goal_returns_204(self):
        resp = self.post_json("/goals/snooze", {"id": 9999, "weeks": 1})
        self.assertEqual(resp.status_code, 204)

    def test_snooze_missing_fields_returns_400(self):
        resp = self.post_json("/goals/snooze", {"id": 1})
        self.assertEqual(resp.status_code, 400)

    def test_snooze_shifts_from_today_not_active_date(self):
        # active_date is set far in the past — snooze should still be based on today
        goal_id = self._create_and_get_id(
            start_date="2020-01-01", end_date="2027-12-31", active_date="2020-01-01"
        )
        self.post_json("/goals/snooze", {"id": goal_id, "weeks": 1})
        rows = self.real_db.select("goals", "all")
        self.assertEqual(rows[0][7], self._expected_snooze_date(1))

    def test_snooze_removes_tasks_from_week_schedule(self):
        # Insert user with a week_schedule that includes the goal's tasks
        self.real_db._run_param(
            "INSERT INTO users (username, password, week_availability, week_schedule) VALUES (?, ?, ?, ?)",
            ("alice", "pw", json.dumps({"monday": 5}), None)
        )
        self.real_db._commit()
        goal_id = self._create_and_get_id(end_date="2027-12-31")
        self._insert_task(goal_id)
        task_id = self.real_db._run("SELECT task_id FROM tasks").fetchone()[0]

        # Manually set a week_schedule that includes this task
        schedule = {"curr_week_start": "2026-03-22", "monday": [{"task_id": task_id, "completed": False}],
                    "tuesday": [], "wednesday": [], "thursday": [], "friday": [], "saturday": [], "sunday": []}
        self.real_db._run_param(
            "UPDATE users SET week_schedule = ? WHERE username = ?",
            (json.dumps(schedule), "alice")
        )
        self.real_db._commit()

        self.post_json("/goals/snooze", {"id": goal_id, "weeks": 2})

        row = self.real_db._run_param(
            "SELECT week_schedule FROM users WHERE username = ?", ("alice",)
        ).fetchone()
        saved = json.loads(row[0])
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            self.assertNotIn(task_id, [e["task_id"] for e in saved.get(day, [])], f"task_id still in {day} after snooze")

    def test_snooze_leaves_other_goals_tasks_in_schedule(self):
        # Snoozing goal A should not touch goal B's tasks in the schedule
        self.real_db._run_param(
            "INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?)",
            ("alice", "pw", json.dumps({"monday": 5}))
        )
        self.real_db._commit()

        goal_a = self._create_and_get_id(name="Goal A", end_date="2027-12-31")
        goal_b = self._create_and_get_id(name="Goal B", end_date="2027-12-31")
        self._insert_task(goal_a)
        self._insert_task(goal_b)
        rows = self.real_db._run("SELECT task_id FROM tasks ORDER BY task_id").fetchall()
        task_a, task_b = rows[0][0], rows[1][0]

        schedule = {"curr_week_start": "2026-03-22",
                    "monday": [{"task_id": task_a, "completed": False}, {"task_id": task_b, "completed": False}],
                    "tuesday": [], "wednesday": [], "thursday": [], "friday": [], "saturday": [], "sunday": []}
        self.real_db._run_param(
            "UPDATE users SET week_schedule = ? WHERE username = ?",
            (json.dumps(schedule), "alice")
        )
        self.real_db._commit()

        self.post_json("/goals/snooze", {"id": goal_a, "weeks": 2})

        row = self.real_db._run_param(
            "SELECT week_schedule FROM users WHERE username = ?", ("alice",)
        ).fetchone()
        saved = json.loads(row[0])
        monday_task_ids = [e["task_id"] for e in saved["monday"]]
        self.assertNotIn(task_a, monday_task_ids)
        self.assertIn(task_b, monday_task_ids)

    def test_snooze_goal_with_no_tasks_does_not_error(self):
        goal_id = self._create_and_get_id(end_date="2027-12-31")
        resp = self.post_json("/goals/snooze", {"id": goal_id, "weeks": 1})
        self.assertEqual(resp.status_code, 204)
        rows = self.real_db.select("goals", "all")
        self.assertEqual(rows[0][7], self._expected_snooze_date(1))


# ---------------------------------------------------------------------------
# POST /schedule/weekly  (integration)
# ---------------------------------------------------------------------------


class TestWeeklySchedule(IntegrationTestCase):
    def _insert_user(self, username, week_availability=None):
        avail = json.dumps(week_availability or {"monday": 3, "wednesday": 2, "friday": 4})
        self.real_db._run_param(
            "INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?)",
            (username, "pw", avail)
        )
        self.real_db._commit()

    def test_new_week_assigns_tasks(self):
        self._insert_user("alice")
        self.create_goal(user="alice", start_date=date.today().isoformat(), end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        self._insert_task(goal_id, weekly_frequency=2)

        resp = self.post_json("/schedule/weekly", {"user_id": "alice"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["new_week"])
        schedule = body["schedule"]
        # 2 occurrences should be assigned across Mon/Wed/Fri
        all_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        total = sum(len(v) for k, v in schedule.items() if k != "curr_week_start")
        self.assertEqual(total, 2)
        self.assertIn("curr_week_start", schedule)
        # Every task entry across all days should have completed=False
        for day in all_days:
            for entry in schedule.get(day, []):
                self.assertFalse(entry["completed"])

    def test_same_week_returns_cached_schedule(self):
        self._insert_user("alice")
        self.create_goal(user="alice", start_date=date.today().isoformat(), end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        self._insert_task(goal_id)

        # First call — new week
        self.post_json("/schedule/weekly", {"user_id": "alice"})
        # Second call — same week
        resp = self.post_json("/schedule/weekly", {"user_id": "alice"})
        body = resp.get_json()
        self.assertFalse(body["new_week"])

    def test_no_availability_returns_empty_schedule(self):
        self.real_db._run_param(
            "INSERT INTO users (username, password) VALUES (?, ?)", ("bob", "pw")
        )
        self.real_db._commit()
        resp = self.post_json("/schedule/weekly", {"user_id": "bob"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body["schedule"], {})

    def test_missing_user_id_returns_400(self):
        resp = self.post_json("/schedule/weekly", {})
        self.assertEqual(resp.status_code, 400)

    def test_unknown_user_returns_empty(self):
        resp = self.post_json("/schedule/weekly", {"user_id": "nobody"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["schedule"], {})


# ---------------------------------------------------------------------------
# POST /daily_goal_digest  (integration)
# ---------------------------------------------------------------------------


class TestDailyGoalDigest(IntegrationTestCase):
    def _setup_user_with_task(self, username="alice"):
        # Insert user, goal, and task, then manually set today's day in week_schedule
        from datetime import date
        today_name = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"][
            date.today().weekday()
        ]
        self.real_db._run_param(
            "INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?)",
            (username, "pw", json.dumps({"monday": 3, "wednesday": 2, "friday": 4}))
        )
        self.real_db._commit()

        self.create_goal(user=username, start_date=date.today().isoformat(), end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]

        self.real_db._run_param(
            """INSERT INTO tasks (goal_id, task, weekly_frequency, weight,
               start_date, end_date, impetus) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (goal_id, "Go for a run", 3, 1, date.today().isoformat(), "2027-12-31", 4)
        )
        self.real_db._commit()
        task_id = self.real_db._run("SELECT task_id FROM tasks").fetchone()[0]

        # Write a week_schedule that places this task on today.
        # curr_week_start must match the real current Sunday so check_new_week
        # sees the same week and returns the cached schedule without wiping it.
        from datetime import timedelta
        days_since_sunday = (date.today().weekday() + 1) % 7
        curr_sunday = (date.today() - timedelta(days=days_since_sunday)).isoformat()
        all_days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        schedule = json.dumps({
            "curr_week_start": curr_sunday,
            today_name: [{"task_id": task_id, "completed": False}],
            **{d: [] for d in all_days if d != today_name},
        })
        self.real_db._run_param(
            "UPDATE users SET week_schedule = ? WHERE username = ?", (schedule, username)
        )
        self.real_db._commit()
        return task_id

    def test_returns_todays_tasks_with_goal_name(self):
        task_id = self._setup_user_with_task()
        resp = self.post_json("/daily_goal_digest", {"user_id": "alice"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(len(body["tasks"]), 1)
        t = body["tasks"][0]
        self.assertEqual(t["task_id"], task_id)
        self.assertEqual(t["task"], "Go for a run")
        self.assertEqual(t["goal_name"], "Run 5k")

    def test_response_shape(self):
        self._setup_user_with_task()
        body = self.post_json("/daily_goal_digest", {"user_id": "alice"}).get_json()
        t = body["tasks"][0]
        self.assertIn("task_id", t)
        self.assertIn("task", t)
        self.assertIn("goal_name", t)
        self.assertIn("completed", t)
        self.assertEqual(len(t), 4)

    def test_day_field_matches_today(self):
        from datetime import date
        today_name = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"][
            date.today().weekday()
        ]
        self._setup_user_with_task()
        body = self.post_json("/daily_goal_digest", {"user_id": "alice"}).get_json()
        self.assertEqual(body["day"], today_name)

    def test_no_schedule_returns_empty(self):
        self.real_db._run_param(
            "INSERT INTO users (username, password) VALUES (?, ?)", ("bob", "pw")
        )
        self.real_db._commit()
        resp = self.post_json("/daily_goal_digest", {"user_id": "bob"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["tasks"], [])

    def test_missing_user_id_returns_400(self):
        resp = self.post_json("/daily_goal_digest", {})
        self.assertEqual(resp.status_code, 400)


# ---------------------------------------------------------------------------
# POST /goals/delete  (integration)
# ---------------------------------------------------------------------------


class TestDeleteGoalIntegration(IntegrationTestCase):
    def _inserted_id(self):
        self.create_goal()
        rows = self.real_db.select("goals", "all")
        return rows[0][0]

    def test_delete_removes_goal(self):
        goal_id = self._inserted_id()
        resp = self.post_json("/goals/delete", {"id": goal_id})
        self.assertEqual(resp.status_code, 204)
        rows = self.real_db.select("goals", "all")
        self.assertEqual(len(rows), 0)

    def test_delete_cascades_to_tasks(self):
        goal_id = self._inserted_id()
        self.real_db._run_param(
            """INSERT INTO tasks (goal_id, task, weekly_frequency, weight,
               start_date, end_date, impetus) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (goal_id, "Do the thing", 2, 1, date.today().isoformat(), "2027-12-31", 3)
        )
        self.real_db._commit()
        self.assertEqual(len(self.real_db._run("SELECT * FROM tasks").fetchall()), 1)

        self.post_json("/goals/delete", {"id": goal_id})
        self.assertEqual(len(self.real_db._run("SELECT * FROM tasks").fetchall()), 0)

    def test_delete_missing_id_returns_400(self):
        resp = self.post_json("/goals/delete", {})
        self.assertEqual(resp.status_code, 400)

    def test_delete_nonexistent_id_returns_204(self):
        resp = self.post_json("/goals/delete", {"id": 9999})
        self.assertEqual(resp.status_code, 204)


# ---------------------------------------------------------------------------
# POST /tasks/complete  (integration)
# ---------------------------------------------------------------------------


class TestGoalCompleteIntegration(IntegrationTestCase):
    def _setup(self):
        # Insert user + goal + task, set a week_schedule with the task on today
        today_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][
            date.today().weekday()
        ]
        self.real_db._run_param(
            "INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?)",
            ("alice", "pw", json.dumps({"monday": 5}))
        )
        self.real_db._commit()
        self.create_goal(end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        self._insert_task(goal_id)
        task_id = self.real_db._run("SELECT task_id FROM tasks").fetchone()[0]
        all_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        schedule = json.dumps({
            "curr_week_start": "2026-03-22",
            today_name: [{"task_id": task_id, "completed": False}],
            **{d: [] for d in all_days if d != today_name},
        })
        self.real_db._run_param(
            "UPDATE users SET week_schedule = ? WHERE username = ?", (schedule, "alice")
        )
        self.real_db._commit()
        return task_id

    def _get_completed(self):
        today_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][
            date.today().weekday()
        ]
        row = self.real_db._run_param(
            "SELECT week_schedule FROM users WHERE username = ?", ("alice",)
        ).fetchone()
        schedule = json.loads(row[0])
        return {e["task_id"]: e["completed"] for e in schedule[today_name]}

    def test_mark_task_done(self):
        task_id = self._setup()
        resp = self.post_json("/tasks/complete", {"user_id": "alice", "task_id": task_id, "status": True})
        self.assertEqual(resp.status_code, 204)
        self.assertTrue(self._get_completed()[task_id])

    def test_mark_task_undone(self):
        task_id = self._setup()
        self.post_json("/tasks/complete", {"user_id": "alice", "task_id": task_id, "status": True})
        self.post_json("/tasks/complete", {"user_id": "alice", "task_id": task_id, "status": False})
        self.assertFalse(self._get_completed()[task_id])

    def test_missing_user_id_returns_400(self):
        resp = self.post_json("/tasks/complete", {"task_id": 1, "status": True})
        self.assertEqual(resp.status_code, 400)

    def test_missing_task_id_returns_400(self):
        resp = self.post_json("/tasks/complete", {"user_id": "alice", "status": True})
        self.assertEqual(resp.status_code, 400)

    def test_missing_status_returns_400(self):
        resp = self.post_json("/tasks/complete", {"user_id": "alice", "task_id": 1})
        self.assertEqual(resp.status_code, 400)

    def test_completed_initialized_false_on_assign(self):
        self.real_db._run_param(
            "INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?)",
            ("alice", "pw", json.dumps({"monday": 5, "wednesday": 5}))
        )
        self.real_db._commit()
        self.create_goal(end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        self._insert_task(goal_id, weekly_frequency=2)
        resp = self.post_json("/schedule/weekly", {"user_id": "alice"})
        schedule = resp.get_json()["schedule"]
        all_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in all_days:
            for entry in schedule.get(day, []):
                self.assertFalse(entry["completed"])


# ---------------------------------------------------------------------------
# Goal completion history (integration)
# ---------------------------------------------------------------------------


class TestGoalCompletion(IntegrationTestCase):
    _ALL_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    def _today_name(self):
        return self._ALL_DAYS[date.today().weekday()]

    def _completion(self, goal_id):
        row = self.real_db._run_param(
            "SELECT completion FROM goals WHERE id = ?", (goal_id,)
        ).fetchone()
        return json.loads(row[0])

    def _insert_user(self, username="alice", availability=None):
        avail = json.dumps(availability or {self._today_name(): 5})
        self.real_db._run_param(
            "INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?)",
            (username, "pw", avail),
        )
        self.real_db._commit()

    def test_new_goal_completion_defaults_zero(self):
        # A freshly created goal (with the fake LLM yielding no tasks) should
        # have a completion object with zero counters and zero percent.
        self.create_goal()
        body = self.post_json("/goals", {}).get_json()
        self.assertEqual(
            body["goals"][0]["completion"],
            {"completed_tasks": 0, "all_tasks": 0, "percent_completed": 0},
        )

    def test_all_tasks_incremented_on_weekly_assign(self):
        # Scheduling a task with weekly_frequency=2 over 2 available days should
        # bump the parent goal's all_tasks by 2 (one per scheduled instance).
        self._insert_user(availability={"monday": 5, "wednesday": 5})
        self.create_goal(end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        self._insert_task(goal_id, weekly_frequency=2)
        self.post_json("/schedule/weekly", {"user_id": "alice"})
        c = self._completion(goal_id)
        self.assertEqual(c["all_tasks"], 2)
        self.assertEqual(c["completed_tasks"], 0)
        self.assertEqual(c["percent_completed"], 0)

    def test_completed_tasks_increments_on_complete(self):
        # Schedule one task on today via /schedule/weekly, mark it complete,
        # and verify the goal counters reflect 1/1 = 100%.
        self._insert_user()
        self.create_goal(end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        self._insert_task(goal_id, weekly_frequency=1)
        self.post_json("/schedule/weekly", {"user_id": "alice"})
        task_id = self.real_db._run("SELECT task_id FROM tasks").fetchone()[0]
        self.post_json(
            "/tasks/complete",
            {"user_id": "alice", "task_id": task_id, "status": True},
        )
        c = self._completion(goal_id)
        self.assertEqual(c["completed_tasks"], 1)
        self.assertEqual(c["all_tasks"], 1)
        self.assertEqual(c["percent_completed"], 100)

    def test_completed_tasks_decrements_on_undo(self):
        # Marking a task done then undone should leave completed_tasks at 0.
        self._insert_user()
        self.create_goal(end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        self._insert_task(goal_id, weekly_frequency=1)
        self.post_json("/schedule/weekly", {"user_id": "alice"})
        task_id = self.real_db._run("SELECT task_id FROM tasks").fetchone()[0]
        self.post_json("/tasks/complete", {"user_id": "alice", "task_id": task_id, "status": True})
        self.post_json("/tasks/complete", {"user_id": "alice", "task_id": task_id, "status": False})
        c = self._completion(goal_id)
        self.assertEqual(c["completed_tasks"], 0)
        self.assertEqual(c["percent_completed"], 0)

    def test_percent_computed_correctly(self):
        # Schedule 4 separate tasks (1 instance each) on today, mark 1 complete,
        # and verify percent_completed == 25.
        self._insert_user()
        self.create_goal(end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        for _ in range(4):
            self._insert_task(goal_id, weekly_frequency=1)
        self.post_json("/schedule/weekly", {"user_id": "alice"})
        first_task_id = self.real_db._run(
            "SELECT task_id FROM tasks ORDER BY task_id"
        ).fetchone()[0]
        self.post_json(
            "/tasks/complete",
            {"user_id": "alice", "task_id": first_task_id, "status": True},
        )
        c = self._completion(goal_id)
        self.assertEqual(c["all_tasks"], 4)
        self.assertEqual(c["completed_tasks"], 1)
        self.assertEqual(c["percent_completed"], 25)

    def test_snooze_decrements_counts(self):
        # Pre-seed a schedule with 2 instances of a goal's task (1 completed)
        # and a corresponding completion of {1, 2, 50}. Snoozing should remove
        # both instances and roll the counters back to {0, 0, 0}.
        self._insert_user(availability={"monday": 5})
        self.create_goal(end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        self._insert_task(goal_id)
        task_id = self.real_db._run("SELECT task_id FROM tasks").fetchone()[0]
        schedule = {
            "curr_week_start": "2026-03-22",
            "monday": [
                {"task_id": task_id, "completed": True},
                {"task_id": task_id, "completed": False},
            ],
            "tuesday": [], "wednesday": [], "thursday": [],
            "friday": [], "saturday": [], "sunday": [],
        }
        self.real_db._run_param(
            "UPDATE users SET week_schedule = ? WHERE username = ?",
            (json.dumps(schedule), "alice"),
        )
        self.real_db._run_param(
            "UPDATE goals SET completion = ? WHERE id = ?",
            (json.dumps({"completed_tasks": 1, "all_tasks": 2, "percent_completed": 50}), goal_id),
        )
        self.real_db._commit()

        self.post_json("/goals/snooze", {"id": goal_id, "weeks": 2})

        c = self._completion(goal_id)
        self.assertEqual(c, {"completed_tasks": 0, "all_tasks": 0, "percent_completed": 0})

    def test_new_week_adds_to_history_cumulatively(self):
        # Schedule once, then rewind curr_week_start in the DB to simulate the
        # next week rolling over, and schedule again. all_tasks should double.
        self._insert_user(availability={"monday": 5, "wednesday": 5})
        self.create_goal(end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        self._insert_task(goal_id, weekly_frequency=2)

        self.post_json("/schedule/weekly", {"user_id": "alice"})
        first = self._completion(goal_id)["all_tasks"]
        self.assertEqual(first, 2)

        # Rewind curr_week_start so check_new_week believes a new week began
        row = self.real_db._run_param(
            "SELECT week_schedule FROM users WHERE username = ?", ("alice",)
        ).fetchone()
        sched = json.loads(row[0])
        sched["curr_week_start"] = "1999-01-03"
        self.real_db._run_param(
            "UPDATE users SET week_schedule = ? WHERE username = ?",
            (json.dumps(sched), "alice"),
        )
        self.real_db._commit()

        self.post_json("/schedule/weekly", {"user_id": "alice"})
        second = self._completion(goal_id)["all_tasks"]
        self.assertEqual(second, 4)

    def test_same_week_rebuild_does_not_double_count(self):
        # When create_goal triggers assign_weekly_tasks mid-week, the existing
        # goals' instances are already counted in all_tasks. Re-running
        # assign_weekly_tasks in the same week must not double-count them.
        # A new goal added during the same-week rebuild should still be counted.
        self._insert_user(availability={"monday": 5, "wednesday": 5})
        self.create_goal(name="Goal A", end_date="2027-12-31")
        goal_a = self.real_db.select("goals", "all")[0][0]
        self._insert_task(goal_a, weekly_frequency=2)

        # First scheduling — goal A picks up its 2 instances
        self.real_db.assign_weekly_tasks("alice", self.real_db.this_sunday())
        self.assertEqual(self._completion(goal_a)["all_tasks"], 2)

        # User creates a second goal mid-week; create_goal would re-run
        # assign_weekly_tasks. Simulate that here.
        self.create_goal(name="Goal B", end_date="2027-12-31")
        goal_b = self.real_db.select("goals", "all")[1][0]
        self._insert_task(goal_b, weekly_frequency=1)

        self.real_db.assign_weekly_tasks("alice", self.real_db.this_sunday())

        # Goal A must NOT have grown — its 2 instances were already counted
        self.assertEqual(self._completion(goal_a)["all_tasks"], 2)
        # Goal B should be counted normally
        self.assertEqual(self._completion(goal_b)["all_tasks"], 1)

    def test_same_week_rebuild_preserves_completed_progress(self):
        # User completes a task, then a mid-week rebuild happens. The rebuild
        # resets the schedule entries to completed=False, but the cumulative
        # completed_tasks counter must be preserved (the user's historical
        # progress shouldn't vanish on a re-assign).
        self._insert_user()
        self.create_goal(end_date="2027-12-31")
        goal_id = self.real_db.select("goals", "all")[0][0]
        self._insert_task(goal_id, weekly_frequency=1)
        self.real_db.assign_weekly_tasks("alice", self.real_db.this_sunday())
        task_id = self.real_db._run("SELECT task_id FROM tasks").fetchone()[0]
        self.post_json(
            "/tasks/complete",
            {"user_id": "alice", "task_id": task_id, "status": True},
        )
        self.assertEqual(self._completion(goal_id)["completed_tasks"], 1)

        # Simulate a mid-week rebuild
        self.real_db.assign_weekly_tasks("alice", self.real_db.this_sunday())

        c = self._completion(goal_id)
        self.assertEqual(c["all_tasks"], 1)
        self.assertEqual(c["completed_tasks"], 1)

    def test_multiple_goals_tracked_independently(self):
        # Completing a task from goal A must not touch goal B's counters.
        self._insert_user()
        self.create_goal(name="Goal A", end_date="2027-12-31")
        self.create_goal(name="Goal B", end_date="2027-12-31")
        rows = self.real_db.select("goals", "all")
        goal_a, goal_b = rows[0][0], rows[1][0]
        self._insert_task(goal_a, weekly_frequency=1)
        self._insert_task(goal_b, weekly_frequency=1)

        self.post_json("/schedule/weekly", {"user_id": "alice"})

        # Find which task belongs to goal A and complete it
        task_a = self.real_db._run_param(
            "SELECT task_id FROM tasks WHERE goal_id = ?", (goal_a,)
        ).fetchone()[0]
        self.post_json(
            "/tasks/complete",
            {"user_id": "alice", "task_id": task_a, "status": True},
        )

        ca = self._completion(goal_a)
        cb = self._completion(goal_b)
        self.assertEqual(ca["completed_tasks"], 1)
        self.assertEqual(cb["completed_tasks"], 0)


if __name__ == "__main__":
    unittest.main()