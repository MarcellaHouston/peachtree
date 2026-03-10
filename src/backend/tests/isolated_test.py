import unittest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
import json

import app as app_module

# Grab the Flask app instance for use with the test client
flask_app = app_module.app


# ---------------------------------------------------------------------------
# parse_date
# ---------------------------------------------------------------------------


class TestParseDate(unittest.TestCase):
    # Falsy inputs should short-circuit and return None
    def test_none_returns_none(self):
        self.assertIsNone(app_module.parse_date(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(app_module.parse_date(""))

    # A well-formed ISO string should be parsed into a date object
    def test_valid_string(self):
        self.assertEqual(app_module.parse_date("2025-01-15"), date(2025, 1, 15))

    # If a date object is passed in it should be returned unchanged
    def test_date_passthrough(self):
        d = date(2025, 6, 1)
        self.assertEqual(app_module.parse_date(d), d)


# ---------------------------------------------------------------------------
# validate_goal
# ---------------------------------------------------------------------------


class TestValidateGoal(unittest.TestCase):
    # Baseline valid goal — all tests mutate a copy of this
    def _valid(self):
        return {
            "name": "Run 5k",
            "measurable": "completion",
            "end_date": "2025-12-31",
            "user": "alice",
        }

    def test_valid_goal_no_errors(self):
        self.assertEqual(app_module.validate_goal(self._valid()), [])

    # Each required field should produce exactly one error when absent
    def test_missing_name(self):
        g = self._valid()
        del g["name"]
        self.assertIn("name is required", app_module.validate_goal(g))

    def test_missing_measurable(self):
        g = self._valid()
        del g["measurable"]
        self.assertIn("measurable is required", app_module.validate_goal(g))

    # A value outside ALLOWED_MEASURABLE should be rejected with a descriptive message
    def test_invalid_measurable(self):
        g = self._valid()
        g["measurable"] = "vibes"
        errors = app_module.validate_goal(g)
        self.assertTrue(any("measurable must be one of" in e for e in errors))

    def test_missing_end_date(self):
        g = self._valid()
        del g["end_date"]
        self.assertIn("end_date is required", app_module.validate_goal(g))

    def test_missing_user(self):
        g = self._valid()
        del g["user"]
        self.assertIn("user is required", app_module.validate_goal(g))

    # Every value in ALLOWED_MEASURABLE should pass validation
    def test_all_measurable_types_valid(self):
        for m in ("completion", "scalar", "count", "range"):
            g = self._valid()
            g["measurable"] = m
            self.assertEqual(app_module.validate_goal(g), [])


# ---------------------------------------------------------------------------
# Shared base class for endpoint tests
# ---------------------------------------------------------------------------


class AppTestCase(unittest.TestCase):
    def setUp(self):
        flask_app.config["TESTING"] = True
        self.client = flask_app.test_client()

        # Replace app.db with a MagicMock so no real SQLite calls happen.
        # patch.object swaps out the 'db' attribute on the imported app module
        # for the duration of each test, then restores it in tearDown.
        self.mock_db = MagicMock()
        self.db_patch = patch.object(app_module, "db", self.mock_db)
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()

    def post_json(self, url, data):
        # Helper to POST JSON and return the response
        return self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )


# ---------------------------------------------------------------------------
# POST /goals
# ---------------------------------------------------------------------------


class TestGetGoals(AppTestCase):
    # Build a DB row tuple matching the column order expected by app.py:
    # (id, name, description, measurable, start_date, end_date, user)
    # Default dates are within the last 7 days so they survive the default filter.
    def _row(
        self,
        id=1,
        name="Run 5k",
        desc="fitness",
        measurable="completion",
        start=None,
        end=None,
        user="alice",
    ):
        start = start or (date.today() - timedelta(days=3)).isoformat()
        end = end or date.today().isoformat()
        return (id, name, desc, measurable, start, end, user)

    def test_returns_goals(self):
        self.mock_db.select.return_value = [self._row()]
        resp = self.post_json("/goals", {})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(len(body["goals"]), 1)
        self.assertEqual(body["goals"][0]["name"], "Run 5k")

    def test_empty_db(self):
        self.mock_db.select.return_value = []
        body = self.post_json("/goals", {}).get_json()
        self.assertEqual(body["goals"], [])

    # A goal whose end_date is before the requested start_date should be excluded
    def test_filters_goal_ending_before_start(self):
        self.mock_db.select.return_value = [
            self._row(start="2023-06-01", end="2024-01-01")
        ]
        body = self.post_json("/goals", {"start_date": "2025-01-01"}).get_json()
        self.assertEqual(body["goals"], [])

    # A goal whose start_date is after the requested end_date should be excluded
    def test_filters_goal_starting_after_end(self):
        self.mock_db.select.return_value = [
            self._row(start="2026-01-01", end="2026-12-31")
        ]
        body = self.post_json("/goals", {"end_date": "2025-12-31"}).get_json()
        self.assertEqual(body["goals"], [])

    # A goal that overlaps the filter window should be included
    def test_includes_overlapping_goal(self):
        self.mock_db.select.return_value = [
            self._row(start="2025-06-01", end="2025-09-01")
        ]
        body = self.post_json(
            "/goals", {"start_date": "2025-07-01", "end_date": "2025-08-01"}
        ).get_json()
        self.assertEqual(len(body["goals"]), 1)

    # Verify each tuple position maps to the correct JSON key
    def test_goal_fields_mapped_correctly(self):
        self.mock_db.select.return_value = [self._row()]
        body = self.post_json("/goals", {}).get_json()
        g = body["goals"][0]
        self.assertEqual(g["id"], 1)
        self.assertEqual(g["description"], "fitness")
        self.assertEqual(g["measurable"], "completion")
        self.assertEqual(g["user"], "alice")


# ---------------------------------------------------------------------------
# POST /goals/create
# ---------------------------------------------------------------------------


class TestCreateGoal(AppTestCase):
    # Minimal valid payload — tests add/remove fields as needed
    def _payload(self):
        return {
            "goal": {
                "name": "Read books",
                "measurable": "count",
                "end_date": "2025-12-31",
                "user": "bob",
            }
        }

    # Happy path: 204 and exactly one insert call
    def test_create_success(self):
        resp = self.post_json("/goals/create", self._payload())
        self.assertEqual(resp.status_code, 204)
        self.mock_db.insert.assert_called_once()

    def test_insert_called_with_goals_table(self):
        self.post_json("/goals/create", self._payload())
        table = self.mock_db.insert.call_args[0][0]
        self.assertEqual(table, "goals")

    # When start_date is omitted, the app should default it to today
    def test_default_start_date_is_today(self):
        self.post_json("/goals/create", self._payload())
        args = self.mock_db.insert.call_args[0][1]
        self.assertEqual(args[3], date.today().isoformat())  # start_date is at index 3

    # When start_date is provided, it should be used as-is (normalized to ISO)
    def test_provided_start_date_used(self):
        p = self._payload()
        p["goal"]["start_date"] = "2025-03-01"
        self.post_json("/goals/create", p)
        args = self.mock_db.insert.call_args[0][1]
        self.assertEqual(args[3], "2025-03-01")

    # Body missing the top-level "goal" key should be a 400
    def test_missing_goal_key_returns_400(self):
        resp = self.post_json("/goals/create", {"not_goal": {}})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_empty_body_returns_400(self):
        resp = self.post_json("/goals/create", {})
        self.assertEqual(resp.status_code, 400)

    # Field-level validation failures should surface as an "errors" list
    def test_validation_errors_returned(self):
        p = self._payload()
        del p["goal"]["name"]
        resp = self.post_json("/goals/create", p)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("errors", resp.get_json())

    def test_invalid_measurable_rejected(self):
        p = self._payload()
        p["goal"]["measurable"] = "vibes"
        resp = self.post_json("/goals/create", p)
        self.assertEqual(resp.status_code, 400)

    # No DB write should happen when validation fails
    def test_no_db_insert_on_validation_failure(self):
        p = self._payload()
        del p["goal"]["user"]
        self.post_json("/goals/create", p)
        self.mock_db.insert.assert_not_called()


# ---------------------------------------------------------------------------
# POST /goals/update
# ---------------------------------------------------------------------------


class TestUpdateGoal(AppTestCase):
    # Valid payload includes an id so the app knows which row to update
    def _payload(self):
        return {
            "goal": {
                "id": 1,
                "name": "Run 10k",
                "measurable": "completion",
                "end_date": "2025-12-31",
                "user": "alice",
            }
        }

    # Happy path: 204 and exactly one update call
    def test_update_success(self):
        resp = self.post_json("/goals/update", self._payload())
        self.assertEqual(resp.status_code, 204)
        self.mock_db.update.assert_called_once()

    # The row id should be passed as the second positional argument to db.update
    def test_update_passes_correct_id(self):
        self.post_json("/goals/update", self._payload())
        _, row_id, _ = self.mock_db.update.call_args[0]
        self.assertEqual(row_id, 1)

    # "id" must be removed from the updates dict before calling db.update
    # to avoid trying to overwrite the primary key
    def test_id_stripped_from_updates(self):
        self.post_json("/goals/update", self._payload())
        _, _, updates = self.mock_db.update.call_args[0]
        self.assertNotIn("id", updates)

    # Body missing the top-level "goal" key should be a 400
    def test_missing_goal_key_returns_400(self):
        resp = self.post_json("/goals/update", {})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    # Missing "id" in the goal dict should be a 400 (can't update without a target row)
    def test_missing_id_returns_400(self):
        p = self._payload()
        del p["goal"]["id"]
        resp = self.post_json("/goals/update", p)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    # Field-level validation failures should surface as an "errors" list
    def test_validation_errors_returned(self):
        p = self._payload()
        del p["goal"]["user"]
        resp = self.post_json("/goals/update", p)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("errors", resp.get_json())

    # No DB write should happen when validation fails
    def test_no_db_update_on_validation_failure(self):
        p = self._payload()
        del p["goal"]["name"]
        self.post_json("/goals/update", p)
        self.mock_db.update.assert_not_called()

    # Dates in the update payload should be normalized to ISO format strings
    def test_dates_normalized(self):
        p = self._payload()
        p["goal"]["start_date"] = "2025-01-15"
        self.post_json("/goals/update", p)
        _, _, updates = self.mock_db.update.call_args[0]
        self.assertEqual(updates["start_date"], "2025-01-15")
        self.assertEqual(updates["end_date"], "2025-12-31")


if __name__ == "__main__":
    unittest.main()
