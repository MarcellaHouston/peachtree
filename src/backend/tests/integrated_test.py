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
        ):
            self.assertIn(key, g)


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
                }
            },
        )
        self.assertEqual(resp.status_code, 204)


if __name__ == "__main__":
    unittest.main()
