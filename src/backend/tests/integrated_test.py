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


class IntegrationTestCase(unittest.TestCase):
    def setUp(self):
        flask_app.config["TESTING"] = True
        self.client = flask_app.test_client()

        # Build a fresh in-memory DB for this test, then swap it into the app.
        # Each test gets its own connection so tests are fully independent.
        self.real_db = make_real_db()
        self.db_patch = patch.object(app_module, "db", self.real_db)
        self.db_patch.start()

    def tearDown(self):
        # Restore the original app.db and close the in-memory connection
        self.db_patch.stop()
        self.real_db.db.close()

    def post_json(self, url, data):
        return self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

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
                "user": "alice",
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
            user="bob",
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
            "user",
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
                    "user": "alice",
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
                    "user": "alice",
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
                    "user": "alice",
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
                    "user": "nobody",
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
        return rows[0][0]

    def test_snooze_pushes_active_date_forward(self):
        goal_id = self._create_and_get_id(start_date="2026-01-01", end_date="2027-12-31")
        resp = self.post_json("/goals/snooze", {"id": goal_id, "weeks": 2})
        self.assertEqual(resp.status_code, 204)
        rows = self.real_db.select("goals", "all")
        self.assertEqual(rows[0][7], "2026-01-11")  # 2026-01-01 + 2 weeks = Jan 15 (Thu) → back to Sun Jan 11

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

    def _insert_task(self, goal_id, weekly_frequency=2, weight=1, impetus=3):
        self.real_db._run_param(
            """INSERT INTO tasks (goal_id, task, weekly_frequency, weight,
               start_date, end_date, impetus)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (goal_id, "Do the thing", weekly_frequency, weight,
             date.today().isoformat(), "2027-12-31", impetus)
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
        total = sum(len(v) for k, v in schedule.items() if k != "curr_week_start")
        self.assertEqual(total, 2)
        self.assertIn("curr_week_start", schedule)

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
            (date.today().weekday() + 1) % 7
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

        # Write a week_schedule that places this task on today
        all_days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        schedule = json.dumps({
            "curr_week_start": "2026-03-15",
            today_name: [task_id],
            **{d: [] for d in all_days if d != today_name}
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
        self.assertEqual(len(t), 3)  # only these 3 fields

    def test_day_field_matches_today(self):
        from datetime import date
        today_name = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"][
            (date.today().weekday() + 1) % 7
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


if __name__ == "__main__":
    unittest.main()