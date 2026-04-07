(venv) rajt@Rajy:~/Reach/peachtree$ python3 -m pytest src/backend/tests/integrated_test.py::TestGoalCompleteIntegration src/backend/test
s/integrated_test.py::TestGoalCompletionHistory -v
========================================================= test session starts ==========================================================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0 -- /home/rajt/Reach/peachtree/venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/rajt/Reach/peachtree/src/backend
configfile: pytest.ini
plugins: anyio-4.12.1
collected 22 items                                                                                                                     

src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_completed_initialized_false_on_assign FAILED             [  4%]
src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_mark_task_done FAILED                                    [  9%]
src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_mark_task_undone FAILED                                  [ 13%]
src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_missing_status_returns_400 FAILED                        [ 18%]
src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_missing_task_id_returns_400 FAILED                       [ 22%]
src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_missing_user_id_returns_400 FAILED                       [ 27%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_assigned_tasks_count_toward_all_tasks PASSED               [ 31%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_completed_task_increments_completed_tasks FAILED           [ 36%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_completion_key_present_on_goal PASSED                      [ 40%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_completion_subkeys_all_present PASSED                      [ 45%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_get_completion_stats_empty_schedule PASSED                 [ 50%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_get_completion_stats_returns_correct_counts PASSED         [ 54%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_get_completion_stats_unknown_user_returns_empty PASSED     [ 59%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_multiple_goals_get_independent_live_stats PASSED           [ 63%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_new_goal_starts_at_zero PASSED                             [ 68%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_rollover_accumulates_across_multiple_weeks FAILED          [ 72%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_rollover_counts_appear_in_goals_api_after_week_change PASSED [ 77%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_rollover_persists_completions_to_goal_columns PASSED       [ 81%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_rollover_with_all_complete PASSED                          [ 86%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_rollover_with_none_complete PASSED                         [ 90%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_same_week_does_not_tally PASSED                            [ 95%]
src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_unmarking_task_decrements_completed_tasks FAILED           [100%]

=============================================================== FAILURES ===============================================================
________________________________ TestGoalCompleteIntegration.test_completed_initialized_false_on_assign ________________________________

self = <integrated_test.TestGoalCompleteIntegration testMethod=test_completed_initialized_false_on_assign>

    def test_completed_initialized_false_on_assign(self):
        self.real_db._run_param(
            "INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?)",
            ("alice", "pw", json.dumps({"monday": 5, "wednesday": 5}))
        )
        self.real_db._commit()
>       self.create_goal(end_date="2027-12-31")

src/backend/tests/integrated_test.py:736: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/backend/tests/integrated_test.py:84: in create_goal
    resp = self.post_json("/goals/create", payload)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/backend/tests/integrated_test.py:54: in post_json
    return self.client.post(
venv/lib/python3.12/site-packages/werkzeug/test.py:1167: in post
    return self.open(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/testing.py:235: in open
    response = super().open(
venv/lib/python3.12/site-packages/werkzeug/test.py:1116: in open
    response_parts = self.run_wsgi_app(request.environ, buffered=buffered)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/werkzeug/test.py:988: in run_wsgi_app
    rv = run_wsgi_app(self.application, environ, buffered=buffered)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/werkzeug/test.py:1264: in run_wsgi_app
    app_rv = app(environ, start_response)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:1536: in __call__
    return self.wsgi_app(environ, start_response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:1514: in wsgi_app
    response = self.handle_exception(e)
               ^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:1511: in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:919: in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:917: in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:902: in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    @app.route("/goals/create", methods=["POST"])
    def create_goal():
        # Create a new goal. Required fields: name, measurable, end_date, user.
        # start_date defaults to today; active_date is set equal to start_date.
        data = request.get_json()
        if not data or "goal" not in data:
            return jsonify({"error": "Missing 'goal' in request body"}), 400
    
        goal = data["goal"]
    
        errors = validate_goal(goal)
        if errors:
            return jsonify({"errors": errors}), 400
    
        if not goal.get("start_date"):
            goal["start_date"] = date.today().isoformat()
        else:
            goal["start_date"] = parse_date(goal["start_date"]).isoformat()
        goal["end_date"] = parse_date(goal["end_date"]).isoformat()
        # active_date starts equal to start_date and can be pushed forward via snooze
        goal["active_date"] = goal["start_date"]
    
>       if goal.get("days_of_week")[-1] == ",":
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: 'NoneType' object is not subscriptable

src/backend/app.py:159: TypeError
--------------------------------------------------------- Captured stdout call ---------------------------------------------------------
DROP TABLE IF EXISTS goals;
CREATE TABLE goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, measurable TEXT NOT NULL CHECK(measurable IN ('completion', 'scalar', 'count', 'range')), start_date TEXT DEFAULT CURRENT_DATE, end_date TEXT NOT NULL, user_id TEXT NOT NULL, active_date TEXT NOT NULL DEFAULT CURRENT_DATE, difficulty TEXT NOT NULL, category TEXT, days_of_week TEXT, completed_tasks INTEGER NOT NULL DEFAULT 0, total_tasks_assigned INTEGER NOT NULL DEFAULT 0);
DROP TABLE IF EXISTS tasks;
CREATE TABLE tasks (task_id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id INTEGER NOT NULL, task TEXT NOT NULL, weekly_frequency INTEGER NOT NULL, weight INTEGER NOT NULL, days_of_week TEXT, start_date TEXT NOT NULL, end_date TEXT NOT NULL, impetus INTEGER NOT NULL CHECK(impetus BETWEEN 1 AND 5), FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE);
DROP TABLE IF EXISTS users;
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, week_schedule TEXT CHECK(json_valid(week_schedule)), week_availability TEXT CHECK(json_valid(week_availability)));
INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?) ('alice', 'pw', '{"monday": 5, "wednesday": 5}')
___________________________________________ TestGoalCompleteIntegration.test_mark_task_done ____________________________________________

self = <integrated_test.TestGoalCompleteIntegration testMethod=test_mark_task_done>

    def test_mark_task_done(self):
>       task_id = self._setup()
                  ^^^^^^^^^^^^^

src/backend/tests/integrated_test.py:707: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/backend/tests/integrated_test.py:680: in _setup
    self.create_goal(end_date="2027-12-31")
src/backend/tests/integrated_test.py:84: in create_goal
    resp = self.post_json("/goals/create", payload)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/backend/tests/integrated_test.py:54: in post_json
    return self.client.post(
venv/lib/python3.12/site-packages/werkzeug/test.py:1167: in post
    return self.open(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/testing.py:235: in open
    response = super().open(
venv/lib/python3.12/site-packages/werkzeug/test.py:1116: in open
    response_parts = self.run_wsgi_app(request.environ, buffered=buffered)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/werkzeug/test.py:988: in run_wsgi_app
    rv = run_wsgi_app(self.application, environ, buffered=buffered)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/werkzeug/test.py:1264: in run_wsgi_app
    app_rv = app(environ, start_response)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:1536: in __call__
    return self.wsgi_app(environ, start_response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:1514: in wsgi_app
    response = self.handle_exception(e)
               ^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:1511: in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:919: in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:917: in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:902: in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    @app.route("/goals/create", methods=["POST"])
    def create_goal():
        # Create a new goal. Required fields: name, measurable, end_date, user.
        # start_date defaults to today; active_date is set equal to start_date.
        data = request.get_json()
        if not data or "goal" not in data:
            return jsonify({"error": "Missing 'goal' in request body"}), 400
    
        goal = data["goal"]
    
        errors = validate_goal(goal)
        if errors:
            return jsonify({"errors": errors}), 400
    
        if not goal.get("start_date"):
            goal["start_date"] = date.today().isoformat()
        else:
            goal["start_date"] = parse_date(goal["start_date"]).isoformat()
        goal["end_date"] = parse_date(goal["end_date"]).isoformat()
        # active_date starts equal to start_date and can be pushed forward via snooze
        goal["active_date"] = goal["start_date"]
    
>       if goal.get("days_of_week")[-1] == ",":
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: 'NoneType' object is not subscriptable

src/backend/app.py:159: TypeError
--------------------------------------------------------- Captured stdout call ---------------------------------------------------------
DROP TABLE IF EXISTS goals;
CREATE TABLE goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, measurable TEXT NOT NULL CHECK(measurable IN ('completion', 'scalar', 'count', 'range')), start_date TEXT DEFAULT CURRENT_DATE, end_date TEXT NOT NULL, user_id TEXT NOT NULL, active_date TEXT NOT NULL DEFAULT CURRENT_DATE, difficulty TEXT NOT NULL, category TEXT, days_of_week TEXT, completed_tasks INTEGER NOT NULL DEFAULT 0, total_tasks_assigned INTEGER NOT NULL DEFAULT 0);
DROP TABLE IF EXISTS tasks;
CREATE TABLE tasks (task_id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id INTEGER NOT NULL, task TEXT NOT NULL, weekly_frequency INTEGER NOT NULL, weight INTEGER NOT NULL, days_of_week TEXT, start_date TEXT NOT NULL, end_date TEXT NOT NULL, impetus INTEGER NOT NULL CHECK(impetus BETWEEN 1 AND 5), FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE);
DROP TABLE IF EXISTS users;
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, week_schedule TEXT CHECK(json_valid(week_schedule)), week_availability TEXT CHECK(json_valid(week_availability)));
INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?) ('alice', 'pw', '{"monday": 5}')
__________________________________________ TestGoalCompleteIntegration.test_mark_task_undone ___________________________________________

self = <integrated_test.TestGoalCompleteIntegration testMethod=test_mark_task_undone>

    def test_mark_task_undone(self):
>       task_id = self._setup()
                  ^^^^^^^^^^^^^

src/backend/tests/integrated_test.py:713: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/backend/tests/integrated_test.py:680: in _setup
    self.create_goal(end_date="2027-12-31")
src/backend/tests/integrated_test.py:84: in create_goal
    resp = self.post_json("/goals/create", payload)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/backend/tests/integrated_test.py:54: in post_json
    return self.client.post(
venv/lib/python3.12/site-packages/werkzeug/test.py:1167: in post
    return self.open(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/testing.py:235: in open
    response = super().open(
venv/lib/python3.12/site-packages/werkzeug/test.py:1116: in open
    response_parts = self.run_wsgi_app(request.environ, buffered=buffered)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/werkzeug/test.py:988: in run_wsgi_app
    rv = run_wsgi_app(self.application, environ, buffered=buffered)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/werkzeug/test.py:1264: in run_wsgi_app
    app_rv = app(environ, start_response)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:1536: in __call__
    return self.wsgi_app(environ, start_response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:1514: in wsgi_app
    response = self.handle_exception(e)
               ^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:1511: in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:919: in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:917: in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
venv/lib/python3.12/site-packages/flask/app.py:902: in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    @app.route("/goals/create", methods=["POST"])
    def create_goal():
        # Create a new goal. Required fields: name, measurable, end_date, user.
        # start_date defaults to today; active_date is set equal to start_date.
        data = request.get_json()
        if not data or "goal" not in data:
            return jsonify({"error": "Missing 'goal' in request body"}), 400
    
        goal = data["goal"]
    
        errors = validate_goal(goal)
        if errors:
            return jsonify({"errors": errors}), 400
    
        if not goal.get("start_date"):
            goal["start_date"] = date.today().isoformat()
        else:
            goal["start_date"] = parse_date(goal["start_date"]).isoformat()
        goal["end_date"] = parse_date(goal["end_date"]).isoformat()
        # active_date starts equal to start_date and can be pushed forward via snooze
        goal["active_date"] = goal["start_date"]
    
>       if goal.get("days_of_week")[-1] == ",":
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: 'NoneType' object is not subscriptable

src/backend/app.py:159: TypeError
--------------------------------------------------------- Captured stdout call ---------------------------------------------------------
DROP TABLE IF EXISTS goals;
CREATE TABLE goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, measurable TEXT NOT NULL CHECK(measurable IN ('completion', 'scalar', 'count', 'range')), start_date TEXT DEFAULT CURRENT_DATE, end_date TEXT NOT NULL, user_id TEXT NOT NULL, active_date TEXT NOT NULL DEFAULT CURRENT_DATE, difficulty TEXT NOT NULL, category TEXT, days_of_week TEXT, completed_tasks INTEGER NOT NULL DEFAULT 0, total_tasks_assigned INTEGER NOT NULL DEFAULT 0);
DROP TABLE IF EXISTS tasks;
CREATE TABLE tasks (task_id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id INTEGER NOT NULL, task TEXT NOT NULL, weekly_frequency INTEGER NOT NULL, weight INTEGER NOT NULL, days_of_week TEXT, start_date TEXT NOT NULL, end_date TEXT NOT NULL, impetus INTEGER NOT NULL CHECK(impetus BETWEEN 1 AND 5), FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE);
DROP TABLE IF EXISTS users;
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, week_schedule TEXT CHECK(json_valid(week_schedule)), week_availability TEXT CHECK(json_valid(week_availability)));
INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?) ('alice', 'pw', '{"monday": 5}')
_____________________________________ TestGoalCompleteIntegration.test_missing_status_returns_400 ______________________________________

self = <integrated_test.TestGoalCompleteIntegration testMethod=test_missing_status_returns_400>

    def test_missing_status_returns_400(self):
        resp = self.post_json("/goals/complete", {"user_id": "alice", "task_id": 1})
>       self.assertEqual(resp.status_code, 400)
E       AssertionError: 404 != 400

src/backend/tests/integrated_test.py:728: AssertionError
--------------------------------------------------------- Captured stdout call ---------------------------------------------------------
DROP TABLE IF EXISTS goals;
CREATE TABLE goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, measurable TEXT NOT NULL CHECK(measurable IN ('completion', 'scalar', 'count', 'range')), start_date TEXT DEFAULT CURRENT_DATE, end_date TEXT NOT NULL, user_id TEXT NOT NULL, active_date TEXT NOT NULL DEFAULT CURRENT_DATE, difficulty TEXT NOT NULL, category TEXT, days_of_week TEXT, completed_tasks INTEGER NOT NULL DEFAULT 0, total_tasks_assigned INTEGER NOT NULL DEFAULT 0);
DROP TABLE IF EXISTS tasks;
CREATE TABLE tasks (task_id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id INTEGER NOT NULL, task TEXT NOT NULL, weekly_frequency INTEGER NOT NULL, weight INTEGER NOT NULL, days_of_week TEXT, start_date TEXT NOT NULL, end_date TEXT NOT NULL, impetus INTEGER NOT NULL CHECK(impetus BETWEEN 1 AND 5), FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE);
DROP TABLE IF EXISTS users;
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, week_schedule TEXT CHECK(json_valid(week_schedule)), week_availability TEXT CHECK(json_valid(week_availability)));
_____________________________________ TestGoalCompleteIntegration.test_missing_task_id_returns_400 _____________________________________

self = <integrated_test.TestGoalCompleteIntegration testMethod=test_missing_task_id_returns_400>

    def test_missing_task_id_returns_400(self):
        resp = self.post_json("/goals/complete", {"user_id": "alice", "status": True})
>       self.assertEqual(resp.status_code, 400)
E       AssertionError: 404 != 400

src/backend/tests/integrated_test.py:724: AssertionError
--------------------------------------------------------- Captured stdout call ---------------------------------------------------------
DROP TABLE IF EXISTS goals;
CREATE TABLE goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, measurable TEXT NOT NULL CHECK(measurable IN ('completion', 'scalar', 'count', 'range')), start_date TEXT DEFAULT CURRENT_DATE, end_date TEXT NOT NULL, user_id TEXT NOT NULL, active_date TEXT NOT NULL DEFAULT CURRENT_DATE, difficulty TEXT NOT NULL, category TEXT, days_of_week TEXT, completed_tasks INTEGER NOT NULL DEFAULT 0, total_tasks_assigned INTEGER NOT NULL DEFAULT 0);
DROP TABLE IF EXISTS tasks;
CREATE TABLE tasks (task_id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id INTEGER NOT NULL, task TEXT NOT NULL, weekly_frequency INTEGER NOT NULL, weight INTEGER NOT NULL, days_of_week TEXT, start_date TEXT NOT NULL, end_date TEXT NOT NULL, impetus INTEGER NOT NULL CHECK(impetus BETWEEN 1 AND 5), FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE);
DROP TABLE IF EXISTS users;
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, week_schedule TEXT CHECK(json_valid(week_schedule)), week_availability TEXT CHECK(json_valid(week_availability)));
_____________________________________ TestGoalCompleteIntegration.test_missing_user_id_returns_400 _____________________________________

self = <integrated_test.TestGoalCompleteIntegration testMethod=test_missing_user_id_returns_400>

    def test_missing_user_id_returns_400(self):
        resp = self.post_json("/goals/complete", {"task_id": 1, "status": True})
>       self.assertEqual(resp.status_code, 400)
E       AssertionError: 404 != 400

src/backend/tests/integrated_test.py:720: AssertionError
--------------------------------------------------------- Captured stdout call ---------------------------------------------------------
DROP TABLE IF EXISTS goals;
CREATE TABLE goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, measurable TEXT NOT NULL CHECK(measurable IN ('completion', 'scalar', 'count', 'range')), start_date TEXT DEFAULT CURRENT_DATE, end_date TEXT NOT NULL, user_id TEXT NOT NULL, active_date TEXT NOT NULL DEFAULT CURRENT_DATE, difficulty TEXT NOT NULL, category TEXT, days_of_week TEXT, completed_tasks INTEGER NOT NULL DEFAULT 0, total_tasks_assigned INTEGER NOT NULL DEFAULT 0);
DROP TABLE IF EXISTS tasks;
CREATE TABLE tasks (task_id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id INTEGER NOT NULL, task TEXT NOT NULL, weekly_frequency INTEGER NOT NULL, weight INTEGER NOT NULL, days_of_week TEXT, start_date TEXT NOT NULL, end_date TEXT NOT NULL, impetus INTEGER NOT NULL CHECK(impetus BETWEEN 1 AND 5), FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE);
DROP TABLE IF EXISTS users;
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, week_schedule TEXT CHECK(json_valid(week_schedule)), week_availability TEXT CHECK(json_valid(week_availability)));
_______________________________ TestGoalCompletionHistory.test_completed_task_increments_completed_tasks _______________________________

self = <integrated_test.TestGoalCompletionHistory testMethod=test_completed_task_increments_completed_tasks>

    def test_completed_task_increments_completed_tasks(self):
        self._insert_user()
        goal_id = self._insert_goal()
        self._insert_task(goal_id)
        task_id = self.real_db._run("SELECT task_id FROM tasks").fetchone()[0]
    
        self._set_schedule("alice", self._today_schedule([{"task_id": task_id, "completed": False}]))
        self.post_json("/tasks/complete", {"user_id": "alice", "task_id": task_id, "status": True})
    
        goals = self._get_goals_api()
        c = goals[0]["completion"]
>       self.assertEqual(c["completed_tasks"], 1)
E       AssertionError: 0 != 1

src/backend/tests/integrated_test.py:871: AssertionError
--------------------------------------------------------- Captured stdout call ---------------------------------------------------------
DROP TABLE IF EXISTS goals;
CREATE TABLE goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, measurable TEXT NOT NULL CHECK(measurable IN ('completion', 'scalar', 'count', 'range')), start_date TEXT DEFAULT CURRENT_DATE, end_date TEXT NOT NULL, user_id TEXT NOT NULL, active_date TEXT NOT NULL DEFAULT CURRENT_DATE, difficulty TEXT NOT NULL, category TEXT, days_of_week TEXT, completed_tasks INTEGER NOT NULL DEFAULT 0, total_tasks_assigned INTEGER NOT NULL DEFAULT 0);
DROP TABLE IF EXISTS tasks;
CREATE TABLE tasks (task_id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id INTEGER NOT NULL, task TEXT NOT NULL, weekly_frequency INTEGER NOT NULL, weight INTEGER NOT NULL, days_of_week TEXT, start_date TEXT NOT NULL, end_date TEXT NOT NULL, impetus INTEGER NOT NULL CHECK(impetus BETWEEN 1 AND 5), FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE);
DROP TABLE IF EXISTS users;
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, week_schedule TEXT CHECK(json_valid(week_schedule)), week_availability TEXT CHECK(json_valid(week_availability)));
INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?) ('alice', 'pw', '{"monday": 5, "wednesday": 5}')
INSERT INTO goals
               (name, description, measurable, start_date, end_date,
                user_id, active_date, difficulty, category, days_of_week,
                completed_tasks, total_tasks_assigned)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ('Run 5k', None, 'completion', '2026-04-06', '2027-12-31', 'alice', '2026-04-06', 'medium', None, None, 0, 0)
SELECT id FROM goals ORDER BY id DESC LIMIT 1 ()
INSERT INTO tasks (goal_id, task, weekly_frequency, weight,
               start_date, end_date, impetus)
               VALUES (?, ?, ?, ?, ?, ?, ?) (1, 'Do the thing', 2, 1, '2026-04-06', '2027-12-31', 3)
SELECT task_id FROM tasks
UPDATE users SET week_schedule = ? WHERE username = ? ('{"curr_week_start": "2026-04-05", "tuesday": [{"task_id": 1, "completed": false}], "monday": [], "wednesday": [], "thursday": [], "friday": [], "saturday": [], "sunday": []}', 'alice')
SELECT week_schedule FROM users WHERE username = ? ('alice',)
UPDATE users SET week_schedule = ? WHERE username = ? ('{"curr_week_start": "2026-04-05", "tuesday": [{"task_id": 1, "completed": false}], "monday": [], "wednesday": [], "thursday": [], "friday": [], "saturday": [], "sunday": []}', 'alice')
SELECT week_schedule FROM users WHERE username = ? ('alice',)

            SELECT t.task_id, t.goal_id
            FROM tasks t
            JOIN goals g ON t.goal_id = g.id
            WHERE g.user_id = ?
             ('alice',)
SELECT * FROM goals
______________________________ TestGoalCompletionHistory.test_rollover_accumulates_across_multiple_weeks _______________________________

self = <integrated_test.TestGoalCompletionHistory testMethod=test_rollover_accumulates_across_multiple_weeks>

    def test_rollover_accumulates_across_multiple_weeks(self):
        self._insert_user()
        goal_id = self._insert_goal()
        self._insert_task(goal_id)
        task_id = self.real_db._run("SELECT task_id FROM tasks").fetchone()[0]
    
        # Week 1: 1 completed / 1 total
        self._set_schedule("alice", {
            "curr_week_start": "2026-01-04",
            "monday": [{"task_id": task_id, "completed": True}],
            "tuesday": [], "wednesday": [], "thursday": [], "friday": [], "saturday": [], "sunday": [],
        })
        self.real_db.check_new_week("alice")
    
        # Week 2: manually set a second old week and trigger another rollover
        row = self.real_db._run_param(
            "SELECT week_schedule FROM users WHERE username = ?", ("alice",)
        ).fetchone()
        sched = json.loads(row[0])
        sched["curr_week_start"] = "2026-01-11"
        sched["monday"] = [{"task_id": task_id, "completed": False}]
        self._set_schedule("alice", sched)
        self.real_db.check_new_week("alice")
    
        row = self._get_goal_row(goal_id)
        self.assertEqual(row[11], 1)   # cumulative: 1 + 0
>       self.assertEqual(row[12], 2)   # cumulative: 1 + 1
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AssertionError: 3 != 2

src/backend/tests/integrated_test.py:1004: AssertionError
--------------------------------------------------------- Captured stdout call ---------------------------------------------------------
DROP TABLE IF EXISTS goals;
CREATE TABLE goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, measurable TEXT NOT NULL CHECK(measurable IN ('completion', 'scalar', 'count', 'range')), start_date TEXT DEFAULT CURRENT_DATE, end_date TEXT NOT NULL, user_id TEXT NOT NULL, active_date TEXT NOT NULL DEFAULT CURRENT_DATE, difficulty TEXT NOT NULL, category TEXT, days_of_week TEXT, completed_tasks INTEGER NOT NULL DEFAULT 0, total_tasks_assigned INTEGER NOT NULL DEFAULT 0);
DROP TABLE IF EXISTS tasks;
CREATE TABLE tasks (task_id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id INTEGER NOT NULL, task TEXT NOT NULL, weekly_frequency INTEGER NOT NULL, weight INTEGER NOT NULL, days_of_week TEXT, start_date TEXT NOT NULL, end_date TEXT NOT NULL, impetus INTEGER NOT NULL CHECK(impetus BETWEEN 1 AND 5), FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE);
DROP TABLE IF EXISTS users;
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, week_schedule TEXT CHECK(json_valid(week_schedule)), week_availability TEXT CHECK(json_valid(week_availability)));
INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?) ('alice', 'pw', '{"monday": 5, "wednesday": 5}')
INSERT INTO goals
               (name, description, measurable, start_date, end_date,
                user_id, active_date, difficulty, category, days_of_week,
                completed_tasks, total_tasks_assigned)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ('Run 5k', None, 'completion', '2026-04-06', '2027-12-31', 'alice', '2026-04-06', 'medium', None, None, 0, 0)
SELECT id FROM goals ORDER BY id DESC LIMIT 1 ()
INSERT INTO tasks (goal_id, task, weekly_frequency, weight,
               start_date, end_date, impetus)
               VALUES (?, ?, ?, ?, ?, ?, ?) (1, 'Do the thing', 2, 1, '2026-04-06', '2027-12-31', 3)
SELECT task_id FROM tasks
UPDATE users SET week_schedule = ? WHERE username = ? ('{"curr_week_start": "2026-01-04", "monday": [{"task_id": 1, "completed": true}], "tuesday": [], "wednesday": [], "thursday": [], "friday": [], "saturday": [], "sunday": []}', 'alice')
SELECT week_schedule FROM users WHERE username = ? ('alice',)
SELECT task_id, goal_id FROM tasks ()
UPDATE goals SET completed_tasks = completed_tasks + ?, total_tasks_assigned = total_tasks_assigned + ? WHERE id = ? (1, 1, 1)
SELECT week_availability FROM users WHERE username = ? ('alice',)

            SELECT t.task_id, t.weekly_frequency, t.impetus
            FROM tasks t
            JOIN goals g ON t.goal_id = g.id
            WHERE g.user_id = ? AND g.active_date <= ? AND g.end_date >= ?
            ORDER BY t.impetus DESC
         ('alice', '2026-04-06', '2026-04-06')
UPDATE tasks SET days_of_week = ? WHERE task_id = ? ('["monday", "wednesday"]', 1)
UPDATE users SET week_schedule = ? WHERE username = ? ('{"curr_week_start": "2026-04-05", "monday": [{"task_id": 1, "completed": false}], "tuesday": [], "wednesday": [{"task_id": 1, "completed": false}], "thursday": [], "friday": [], "saturday": [], "sunday": []}', 'alice')
SELECT week_schedule FROM users WHERE username = ? ('alice',)
UPDATE users SET week_schedule = ? WHERE username = ? ('{"curr_week_start": "2026-01-11", "monday": [{"task_id": 1, "completed": false}], "tuesday": [], "wednesday": [{"task_id": 1, "completed": false}], "thursday": [], "friday": [], "saturday": [], "sunday": []}', 'alice')
SELECT week_schedule FROM users WHERE username = ? ('alice',)
SELECT task_id, goal_id FROM tasks ()
UPDATE goals SET completed_tasks = completed_tasks + ?, total_tasks_assigned = total_tasks_assigned + ? WHERE id = ? (0, 2, 1)
SELECT week_availability FROM users WHERE username = ? ('alice',)

            SELECT t.task_id, t.weekly_frequency, t.impetus
            FROM tasks t
            JOIN goals g ON t.goal_id = g.id
            WHERE g.user_id = ? AND g.active_date <= ? AND g.end_date >= ?
            ORDER BY t.impetus DESC
         ('alice', '2026-04-06', '2026-04-06')
UPDATE tasks SET days_of_week = ? WHERE task_id = ? ('["monday", "wednesday"]', 1)
UPDATE users SET week_schedule = ? WHERE username = ? ('{"curr_week_start": "2026-04-05", "monday": [{"task_id": 1, "completed": false}], "tuesday": [], "wednesday": [{"task_id": 1, "completed": false}], "thursday": [], "friday": [], "saturday": [], "sunday": []}', 'alice')
SELECT * FROM goals WHERE id = ? (1,)
_______________________________ TestGoalCompletionHistory.test_unmarking_task_decrements_completed_tasks _______________________________

self = <integrated_test.TestGoalCompletionHistory testMethod=test_unmarking_task_decrements_completed_tasks>

    def test_unmarking_task_decrements_completed_tasks(self):
        self._insert_user()
        goal_id = self._insert_goal()
        self._insert_task(goal_id)
        task_id = self.real_db._run("SELECT task_id FROM tasks").fetchone()[0]
    
        # Start with the task already marked complete in the schedule
        self._set_schedule("alice", self._today_schedule([{"task_id": task_id, "completed": True}]))
        self.post_json("/tasks/complete", {"user_id": "alice", "task_id": task_id, "status": False})
    
        goals = self._get_goals_api()
        c = goals[0]["completion"]
>       self.assertEqual(c["completed_tasks"], 0)
E       AssertionError: 1 != 0

src/backend/tests/integrated_test.py:887: AssertionError
--------------------------------------------------------- Captured stdout call ---------------------------------------------------------
DROP TABLE IF EXISTS goals;
CREATE TABLE goals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, measurable TEXT NOT NULL CHECK(measurable IN ('completion', 'scalar', 'count', 'range')), start_date TEXT DEFAULT CURRENT_DATE, end_date TEXT NOT NULL, user_id TEXT NOT NULL, active_date TEXT NOT NULL DEFAULT CURRENT_DATE, difficulty TEXT NOT NULL, category TEXT, days_of_week TEXT, completed_tasks INTEGER NOT NULL DEFAULT 0, total_tasks_assigned INTEGER NOT NULL DEFAULT 0);
DROP TABLE IF EXISTS tasks;
CREATE TABLE tasks (task_id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id INTEGER NOT NULL, task TEXT NOT NULL, weekly_frequency INTEGER NOT NULL, weight INTEGER NOT NULL, days_of_week TEXT, start_date TEXT NOT NULL, end_date TEXT NOT NULL, impetus INTEGER NOT NULL CHECK(impetus BETWEEN 1 AND 5), FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE);
DROP TABLE IF EXISTS users;
CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, week_schedule TEXT CHECK(json_valid(week_schedule)), week_availability TEXT CHECK(json_valid(week_availability)));
INSERT INTO users (username, password, week_availability) VALUES (?, ?, ?) ('alice', 'pw', '{"monday": 5, "wednesday": 5}')
INSERT INTO goals
               (name, description, measurable, start_date, end_date,
                user_id, active_date, difficulty, category, days_of_week,
                completed_tasks, total_tasks_assigned)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ('Run 5k', None, 'completion', '2026-04-06', '2027-12-31', 'alice', '2026-04-06', 'medium', None, None, 0, 0)
SELECT id FROM goals ORDER BY id DESC LIMIT 1 ()
INSERT INTO tasks (goal_id, task, weekly_frequency, weight,
               start_date, end_date, impetus)
               VALUES (?, ?, ?, ?, ?, ?, ?) (1, 'Do the thing', 2, 1, '2026-04-06', '2027-12-31', 3)
SELECT task_id FROM tasks
UPDATE users SET week_schedule = ? WHERE username = ? ('{"curr_week_start": "2026-04-05", "tuesday": [{"task_id": 1, "completed": true}], "monday": [], "wednesday": [], "thursday": [], "friday": [], "saturday": [], "sunday": []}', 'alice')
SELECT week_schedule FROM users WHERE username = ? ('alice',)
UPDATE users SET week_schedule = ? WHERE username = ? ('{"curr_week_start": "2026-04-05", "tuesday": [{"task_id": 1, "completed": true}], "monday": [], "wednesday": [], "thursday": [], "friday": [], "saturday": [], "sunday": []}', 'alice')
SELECT week_schedule FROM users WHERE username = ? ('alice',)

            SELECT t.task_id, t.goal_id
            FROM tasks t
            JOIN goals g ON t.goal_id = g.id
            WHERE g.user_id = ?
             ('alice',)
SELECT * FROM goals
======================================================= short test summary info ========================================================
FAILED src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_completed_initialized_false_on_assign - TypeError: 'NoneType' object is not subscriptable
FAILED src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_mark_task_done - TypeError: 'NoneType' object is not subscriptable
FAILED src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_mark_task_undone - TypeError: 'NoneType' object is not subscriptable
FAILED src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_missing_status_returns_400 - AssertionError: 404 != 400
FAILED src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_missing_task_id_returns_400 - AssertionError: 404 != 400
FAILED src/backend/tests/integrated_test.py::TestGoalCompleteIntegration::test_missing_user_id_returns_400 - AssertionError: 404 != 400
FAILED src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_completed_task_increments_completed_tasks - AssertionError: 0 != 1
FAILED src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_rollover_accumulates_across_multiple_weeks - AssertionError: 3 != 2
FAILED src/backend/tests/integrated_test.py::TestGoalCompletionHistory::test_unmarking_task_decrements_completed_tasks - AssertionError: 1 != 0
===================================================== 9 failed, 13 passed in 6.46s =====================================================
(venv) rajt@Rajy:~/Reach/peachtree$ ^C