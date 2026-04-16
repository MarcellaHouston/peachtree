from flask import Flask, request, jsonify
from datetime import datetime, timedelta, date
import glicko
from sql_db import Database
from bedrock.llm import LLMClient
import transcription.aws as aws
import chromaDB.chroma_db as chroma
import os
import uuid
import json
from werkzeug.security import generate_password_hash, check_password_hash

import logging

CHECK = True
# Set up logging to output to stdout/stderr
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Single shared database connection for all requests.
# Set create=True only once to wipe and rebuild tables from schema.json.
db = Database(create=False)

ALLOWED_MEASURABLE = {"completion", "scalar", "count", "range"}


def parse_date(s):
    # Convert a "YYYY-MM-DD" string to a date object.
    # Returns None if the input is empty or already a date.
    if not s:
        return None
    if isinstance(s, str):
        return datetime.strptime(s, "%Y-%m-%d").date()
    return s


def validate_goal(goal):
    # Check that all required goal fields are present and valid.
    # Returns a list of error strings (empty list = no errors).
    errors = []

    if not goal.get("name"):
        errors.append("name is required")

    if not goal.get("measurable"):
        errors.append("measurable is required")
    elif goal.get("measurable") not in ALLOWED_MEASURABLE:
        errors.append(f"measurable must be one of {list(ALLOWED_MEASURABLE)}")

    if not goal.get("end_date"):
        errors.append("end_date is required")

    if not goal.get("user_id"):
        errors.append("user_id is required")

    if not goal.get("difficulty"):
        errors.append("difficulty is required")

    return errors


# Helper function that should be called in every endpoint
def check_auth(headers: dict) -> bool:
    # Makes sure user's authentication key matches their stored token
    user_id = headers.get("User-ID") or headers.get("User-Id")
    auth = headers.get("Authorization")
    if not CHECK:
        return True
    if not user_id or not auth:
        logger.info("user: " + str(type(user_id)) + " auth: " + str(type(auth)))
        return False
    token = db.get_user_token(int(user_id))
    # logger.info("Auth OK")
    return auth == token


# Helper function that converts user's Glicko rating to a value between 1-100
def convert_glicko(user_id: str) -> int:
    # Get user's Glicko rating from user db
    user_rating = db.get_glicko_rating(user_id)
    # Convert rating to an integer between 1 and 100
    scaled_rating = int(user_rating / 31.5)
    return max(1, min(100, scaled_rating))


@app.cli.command("run-glicko")
def run_glicko():
    from glicko_run import daily_glicko_update

    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"STARTING: Daily Glicko Update at {start_time}\n")
    try:
        daily_glicko_update()
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"SUCCESS: Daily Glicko Update at {end_time}")
    except Exception as e:
        print(f"FAILURE: Daily Glicko Update at {start_time}\nREASON: {e}")


@app.cli.command("assign-weekly-tasks")
def assign_weekly_tasks():
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    this_sunday = db.this_sunday()
    print(f"STARTING: Weekly Task Assignment at {start_time}\n")

    users = db.select("users", "all")
    failures = []
    for user in users:
        username = user[1]
        try:
            schedule = db.assign_weekly_tasks(username, this_sunday)
            task_count = sum(
                len(schedule.get(day, []))
                for day in [
                    "sunday",
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                ]
            )
            print(f"ASSIGNED: {username} ({task_count} tasks)")
            print(json.dumps(schedule, indent=2))
        except Exception as e:
            failures.append((username, e))
            print(f"FAILED: {username}\nREASON: {e}")

    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if failures:
        print(f"FAILURE: Weekly Task Assignment at {end_time}")
        print(f"FAILED USERS: {len(failures)} of {len(users)}")
    else:
        print(f"SUCCESS: Weekly Task Assignment at {end_time}")


@app.route("/")
def hello():
    return "Hello"


# ---- AUTH ROUTES ----


@app.route("/login", methods=["POST"])
def login():
    logger.info("🔐 /login reached.")
    # Frontend should provide username and password
    data = request.get_json()
    username = data.get("username").strip()
    password = data.get("password").strip()

    # Demo mode if no username provided
    if not username:
        return jsonify({"error": "Missing username field in request"}), 400
    if not password:
        return jsonify({"error": "Missing password field in request"}), 400

    # Get user's stored password and id from database
    # stored_user = db.get_login_data(username)
    stored_user = db.get_user_login(username)

    # Check if password is valid
    if check_password_hash(stored_user["password"], password):
        # Generate new token and update it in database
        new_uuid = uuid.uuid4()
        new_token = "Bearer " + str(new_uuid)
        to_update = {"token": new_token}
        db.update("users", stored_user["User-ID"], to_update)
        return (
            jsonify(
                {
                    "User-ID": stored_user["User-ID"],
                    "user_id": username,
                    "Authorization": new_token,
                }
            ),
            200,
        )
    else:
        # Password didn't match, return failure
        return jsonify({"error": "Invalid credentials"}), 401


@app.route("/signup", methods=["POST"])
def signup():
    logger.info("📝 /signup reached.")
    data = request.get_json()
    username = data.get("username").strip()
    password = data.get("password").strip()

    # Make sure username and password is provided
    if not username:
        return jsonify({"error": "Missing username field in request body"}), 400
    if not password:
        return jsonify({"error": "Missing password field in request body"}), 400

    # Check for duplicate username
    if db.check_for_username(username):
        return jsonify({"error": "Username already exists"}), 409

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Generate token
    new_uuid = uuid.uuid4()
    new_token = "Bearer " + str(new_uuid)

    try:
        # Insert new user into database (id will auto-generate in .insert)
        db.insert(
            "users",
            [
                username,
                hashed_password,
                new_token,
                1500,
                350.0,
                0.06,
                "{}",
                '{"monday": 5, "tuesday": 5, "wednesday": 5, "thursday": 5, "friday": 5, "saturday": 5, "sunday": 5}',
            ],
        )
        # Get id from new user (it's auto-generated when user is created)
        new_user_id = db.get_user_id(username)
        if new_user_id == -1:
            return jsonify({"error": "Username doesn't exist"}), 400
        # Return the user_id, username, and token just like login
        return (
            jsonify(
                {
                    "User-ID": new_user_id,
                    "user_id": username,
                    "Authorization": new_token,
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"error": f"{e}"}), 400


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------


@app.route("/goals", methods=["POST"])
def get_goals():
    # Return all goals that overlap the requested date range.
    # If no dates are provided, defaults to goals active in the past 7 days.
    # If user_id is provided, also runs the weekly schedule check.
    logger.info("🎯 /goals reached.")
    data = request.get_json(silent=True) or {}

    # Check authentication
    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id in request"}), 400

    start_date = parse_date(data.get("start_date"))
    end_date = parse_date(data.get("end_date"))

    if not start_date and not end_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

    rows = db.select("goals", "all")
    results = []
    for row in rows:
        # Only return goals belonging to the requesting user
        if row[6] != user_id:
            continue

        active_date = row[7]
        goal = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "measurable": row[3],
            "start_date": row[4],
            "end_date": row[5],
            "user_id": row[6],
            "active_date": active_date,
            "difficulty": row[8],
            "category": row[9],
            "days_of_week": row[10],
            "completion": (
                json.loads(row[11])
                if row[11]
                else {
                    "completed_tasks": 0,
                    "all_tasks": 0,
                    "percent_completed": 0,
                }
            ),
            "isPaused": parse_date(active_date) > date.today(),
        }

        g_start = parse_date(goal.get("start_date"))
        g_end = parse_date(goal.get("end_date"))

        # Exclude goals whose date range doesn't overlap with the filter window
        if start_date and g_end and g_end < start_date:
            continue
        if end_date and g_start and g_start > end_date:
            continue

        results.append(goal)

    new_week, schedule = db.check_new_week(user_id)
    response = {"goals": results, "new_week": new_week, "schedule": schedule}

    return jsonify(response)


@app.route("/goals/create", methods=["POST"])
def create_goal():
    logger.info("🌱 /goals/create reached.")

    # Create a new goal. Required fields: name, measurable, end_date, user.
    # start_date defaults to today; active_date is set equal to start_date.
    data = request.get_json()
    if not data or "goal" not in data:
        return jsonify({"error": "Missing 'goal' in request body"}), 400

    # Check authentication
    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    goal = data["goal"]
    logger.info(
        "🌱 Create goal received: %s | days_of_week=%s",
        goal.get("name"),
        goal.get("days_of_week"),
    )

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

    dow = goal.get("days_of_week")
    if dow and dow[-1] == ",":
        goal["days_of_week"] = dow[:-1]

    goal_id = db.insert(
        "goals",
        [
            goal["name"],
            goal.get("description"),
            goal["measurable"],
            goal["start_date"],
            goal["end_date"],
            goal["user_id"],
            goal["active_date"],
            goal["difficulty"],
            goal.get("category"),
            goal.get("days_of_week"),
            json.dumps({"completed_tasks": 0, "all_tasks": 0, "percent_completed": 0}),
        ],
    )

    llm_payload = {
        "goal_name": goal["name"],
        "start_date": goal["start_date"],
        "end_date": goal["end_date"],
        "difficulty": goal["difficulty"],
        "days_of_week": goal.get("days_of_week"),
        "user_skill": convert_glicko(goal["user_id"]),
    }

    llm_model = LLMClient(LLMClient.UseCase.GENERATE_TASKS, user_id=goal["user_id"])
    tasks, valid, retries = llm_model.query(content=json.dumps(llm_payload))

    logger.info("Starting task adds")
    if valid:
        logger.info("is valid!")
        for task in tasks:
            task_id = db.insert(
                "tasks",
                [
                    goal_id,
                    task["task"],
                    task["weekly_frequency"],
                    task["weight"],
                    task["days_of_week"],
                    task["start_date"],
                    task["end_date"],
                    task["impetus"],
                    task["difficulty_score"],
                ],
            )
            logger.info(
                "🧩 Generated task_id=%s for goal '%s': %s | days_of_week=%s",
                task_id,
                goal["name"],
                task["task"],
                task.get("days_of_week"),
            )
        if tasks:
            schedule = db.assign_weekly_tasks(
                user_id=goal["user_id"], this_sunday=db.this_sunday()
            )
            logger.info("generate new schedule")
            logger.info(str(schedule))
    else:
        logger.info("Error with LLM")
        return (
            jsonify({"error": "LLM failed to generate tasks", "retries": retries}),
            500,
        )
    return "", 204


@app.route("/goals/update", methods=["POST"])
def update_goal():
    logger.info("✏️ /goals/update reached.")

    # Update an existing goal by id. All required fields must still be provided
    # (same validation as create). Only the fields passed in will be changed.
    data = request.get_json()
    if not data or "goal" not in data:
        return jsonify({"error": "Missing 'goal' in request body"}), 400

    goal = data["goal"]
    goal_id = goal.get("id")

    if not goal_id:
        return jsonify({"error": "Missing goal id for update"}), 400

    # Check authentication
    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    errors = validate_goal(goal)
    if errors:
        return jsonify({"errors": errors}), 400

    updates = goal.copy()
    updates.pop("id", None)

    if "start_date" in updates:
        updates["start_date"] = parse_date(updates["start_date"]).isoformat()
    if "end_date" in updates:
        updates["end_date"] = parse_date(updates["end_date"]).isoformat()
    if "user_id" in updates:
        updates["user_id"] = updates.pop("user_id")

    db.update("goals", goal_id, updates)

    return "", 204


@app.route("/goals/snooze", methods=["POST"])
def snooze_goal():
    logger.info("😴 /goals/snooze reached.")

    # Defer a goal by pushing its active_date forward by N weeks (snapped to Sunday).
    # The goal stays in the system but won't appear as active until that date.
    data = request.get_json()

    # Check authentication
    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    goal_id = data.get("id")
    weeks = data.get("weeks")
    if not goal_id or not weeks:
        return jsonify({"error": "Missing id or weeks"}), 400
    db.snooze(goal_id, weeks)
    return "", 204


@app.route("/goals/delete", methods=["POST"])
def delete_goal():
    logger.info("🗑️ /goals/delete reached.")
    # Delete a goal by id. Associated tasks are removed automatically via cascade.
    data = request.get_json(silent=True) or {}

    # Check authentication
    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    goal_id = data.get("id")
    if goal_id is None:
        return jsonify({"error": "Missing 'id' in request body"}), 400
    db.delete("goals", goal_id)
    return "", 204


@app.route("/tasks/complete", methods=["POST"])
def complete_task():
    logger.info("✅ /tasks/complete reached.")
    # Mark a task as done or not-done in the user's current week_schedule.
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    status = data.get("status")

    if not user_id or task_id is None or status is None:
        return jsonify({"error": "Missing user_id, task_id, or status"}), 400

    # Check authentication
    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    db.set_task_status(user_id, task_id, status)
    return "", 204


# ---------------------------------------------------------------------------
# Weekly schedule
# ---------------------------------------------------------------------------


@app.route("/schedule/weekly", methods=["POST"])
def weekly_schedule():
    logger.info("📅 /schedule/weekly reached.")
    # not currently in use,1 get goals() call check_new_week
    # Called by the frontend on app startup.
    # Checks if the user has entered a new week (new Sunday). If so, reassigns
    # all active tasks to days based on the user's availability (round-robin).
    # Returns: { new_week: bool, schedule: { curr_week_start, monday: [...], ... } }

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    # Check authentication
    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    new_week, schedule = db.check_new_week(user_id)
    return jsonify({"new_week": new_week, "schedule": schedule})


@app.route("/daily_goal_digest", methods=["POST"])
def daily_goal_digest():
    logger.info("☀️ /daily_goal_digest reached.")
    # Called on startup after /schedule/weekly.
    # Returns today's tasks for the user, each paired with its goal name.
    # Response: { day: "monday", tasks: [{ task_id, task, goal_name, impetus, ... }] }
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    today_name = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ][(date.today().weekday()) % 7]
    db.check_new_week(user_id)
    tasks = db.get_daily_tasks(user_id)
    return jsonify({"day": today_name, "tasks": tasks})


# ---------------------------------------------------------------------------
# Weekly Recap + Goal Guidance + Recieving Suggestions
# ---------------------------------------------------------------------------

"""
Suggestions JSON SCHEMA: Generate a JSON object with exactly two entries: "suggested_changes" and "changes_summary". "suggested_changes" should map to a list of proposed changes, while "changes_summary" summarizes the intent of the proposed changes.
"suggested_changes" (list) A list of proposed changes, with each object containing "goal_id", any number of ["name","end_date","difficulty","days_of_week"], and "summary". This should always be at least 2 changes, but no more than 5.
- "goal_id" (int) The goal you are changing, gotten from the goals provided in the context.
- "name" (string, optional) Included if you wish to change the name to reflect changes. This is the title for the goal.
- "end_date" (datestring, optional) Included if you wish to change the end date of a goal. This is in YYYY-MM-DD format.
- "difficulty" (string, optional) Included if you wish to change the difficulty of a task. Unless in non-standard cases with big changes in difficulty, usually this should be left unchanged. Must be one of "easy", "average", "hard".
- "days_of_week" (string, optional) Included if you wish to modify which days the goal may be (but not necessarily end up being) performed. Comma-delimited list of days, no spaces, and lowercase (e.g., "monday,wednesday,friday").
- "summary" (string) A summary of this proposed change. This will be what the user sees and uses to accept or decline the change. Should be "git commit or changelog -esque" grammar with infinitive verbs, e.g. "Add Sunday as a day to go to the gym, and push end date back by a week". This should be within approximately 20 words. This MUST reflect the objective change to the goal, not the change to task implied nor the intent behind the change. This will be conveyed through "changes_summary".
"changes_summary" (string) A conclusion that summarizes all the changes proposed and the intent and theme behind suggesting so; this must fit within approximately 40 words. You should speak in second person, i.e. refer to the user as "you". For example, this could be "You might want to spend more days at the gym to improve your gains".
"""


@app.route("/receive_suggestions", methods=["POST"])
def receive_suggestions():
    logger.info("📥 /receive_suggestions reached.")
    ALLOWED_FIELDS = {"name", "end_date", "difficulty", "days_of_week"}
    VALID_DIFFICULTIES = {"easy", "average", "hard"}

    if not request.headers.get("User-ID") and not request.headers.get("User-Id"):
        return jsonify({"error": "Missing User-ID in header"}), 401

    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "Expected JSON object body"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id in request"}), 400

    accepted_changes = data.get("changes")
    if not isinstance(accepted_changes, list) or not accepted_changes:
        return jsonify({"error": "Expected a non-empty list of changes"}), 400

    for change in accepted_changes:
        goal_id = change.get("goal_id")
        if not goal_id:
            return jsonify({"error": "Each change must include goal_id"}), 400

        updates = {k: v for k, v in change.items() if k in ALLOWED_FIELDS}
        if not updates:
            continue

        if "end_date" in updates:
            updates["end_date"] = parse_date(updates["end_date"]).isoformat()
        if "difficulty" in updates and updates["difficulty"] not in VALID_DIFFICULTIES:
            return (
                jsonify({"error": f"Invalid difficulty: {updates['difficulty']}"}),
                400,
            )

        db.update("goals", goal_id, updates)

    db.assign_weekly_tasks(user_id, db.this_sunday())
    return "", 204


@app.route("/weekly_recap", methods=["POST"])
def get_weekly_recap_suggestions():
    logger.info("📊 /weekly_recap reached.")
    if not request.headers.get("User-ID") and not request.headers.get("User-Id"):
        return jsonify({"error": "Missing User-ID in header"}), 401

    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "Expected JSON object body"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id in request"}), 400

    # Read the old week's schedule before any reassignment happens
    schedule = db.get_week_schedule(user_id)

    # Compute task-level completion rate from the schedule's day buckets
    day_names = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]
    total_tasks = 0
    completed_tasks = 0
    for day in day_names:
        for entry in schedule.get(day, []):
            total_tasks += 1
            if entry.get("completed"):
                completed_tasks += 1
    completion_rate = (
        round((completed_tasks / total_tasks) * 100, 1) if total_tasks else 0
    )

    # Gather active goals for this user
    rows = db.select("goals", "all")
    today = date.today()
    goals = []
    for row in rows:
        if row[6] != user_id:
            continue
        g_end = parse_date(row[5])
        if g_end and g_end < today:
            continue
        goals.append(
            {
                "id": row[0],
                "name": row[1],
                "end_date": row[5],
                "difficulty": row[8],
                "days_of_week": row[10],
                "completion": (
                    json.loads(row[11])
                    if row[11]
                    else {
                        "completed_tasks": 0,
                        "all_tasks": 0,
                        "percent_completed": 0,
                    }
                ),
            }
        )

    if not goals:
        return jsonify({"error": "No active goals found"}), 400

    llm_payload = {
        "completion_rate": completion_rate,
        "schedule": schedule,
        "goals": goals,
    }

    llm_model = LLMClient(
        use_case=LLMClient.UseCase.GENERATE_WEEKLY_SUGGESTIONS, user_id=user_id
    )
    suggestions, valid, _ = llm_model.query(content=json.dumps(llm_payload))
    logger.info("weekly_recap LLM output: %s", suggestions)

    if not valid:
        return jsonify({"error": "Failed to generate suggestions"}), 500

    return jsonify(suggestions)


@app.route("/goal_guidance", methods=["POST"])
def get_goal_guidance():
    logger.info("🧭 /goal_guidance reached.")
    user_id = request.headers.get("User-ID") or request.headers.get("User-Id")
    username = request.headers.get("Username")
    goal_id = request.headers.get("Goal-ID") or request.headers.get("Goal-Id")
    file_type = request.headers.get("File-Type", ".m4a")

    if not user_id:
        return jsonify({"error": "Missing User-ID in header"}), 401
    if not username:
        return jsonify({"error": "Missing Username in header"}), 401
    if not goal_id:
        return jsonify({"error": "Missing Goal-ID in header"}), 400

    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    audio_file = request.data
    if not audio_file:
        return jsonify({"error": "Missing audio file"}), 400

    # Transcribe the audio file (same pattern as eod_summary)
    temp_filename = f"temp_{user_id}_{uuid.uuid4()}{file_type}"
    temp_path = os.path.join("/tmp", temp_filename)

    transcription = ""
    try:
        with open(temp_path, "wb") as f:
            f.write(audio_file)
        aws.upload_to_s3(temp_path)
        transcription = aws.transcription_service(temp_path, clean_up=True)
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception as e:
        logger.info(e)
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if not transcription:
        return jsonify({"error": "Transcription failed"}), 400

    # Step 1: Extract semantics from transcription
    extract_model = LLMClient(
        use_case=LLMClient.UseCase.EXTRACT_SEMANTICS, user_id=username
    )
    tasks = db.get_daily_tasks(username)
    daily_tasks = [
        f"Task: {t['task']}, Overarching Goal: {t['goal_name']}.\n" for t in tasks
    ]
    extract_model.context("User's Daily Tasks:\n" + " ".join(daily_tasks))
    semantics, semantics_valid, _ = extract_model.query(content=transcription)
    logger.info("goal_guidance extract_semantics LLM output: %s", semantics)

    if not semantics_valid:
        return jsonify({"error": "Failed to extract semantics"}), 500

    # Step 2: Fetch goal info and tasks for context
    goal_id = int(goal_id)
    rows = db.select("goals", "all")
    goal = None
    for row in rows:
        if row[0] == goal_id and row[6] == username:
            goal = {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "end_date": row[5],
                "difficulty": row[8],
                "days_of_week": row[10],
                "completion": (
                    json.loads(row[11])
                    if row[11]
                    else {
                        "completed_tasks": 0,
                        "all_tasks": 0,
                        "percent_completed": 0,
                    }
                ),
            }
            break

    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    # Step 3: Generate guidance suggestions with RAG
    guidance_model = LLMClient(
        use_case=LLMClient.UseCase.GENERATE_GUIDANCE_SUGGESTIONS, user_id=username
    )
    guidance_model.context(
        f"Goal: {goal['name']}\n"
        f"Description: {goal['description']}\n"
        f"End Date: {goal['end_date']}\n"
        f"Difficulty: {goal['difficulty']}\n"
        f"Days of Week: {goal['days_of_week']}\n"
        f"Completion: {goal['completion']['percent_completed']}% "
        f"({goal['completion']['completed_tasks']}/{goal['completion']['all_tasks']} tasks)\n"
    )

    suggestions, valid, _ = guidance_model.query(
        content=json.dumps(
            {
                "goal_name": goal["name"],
                "semantics": semantics,
            }
        )
    )
    logger.info("goal_guidance suggestions LLM output: %s", suggestions)

    if not valid:
        return jsonify({"error": "Failed to generate guidance suggestions"}), 500

    return jsonify(suggestions)


@app.route("/extract_goal", methods=["POST"])
def extract_goal():
    logger.info("🔎 /extract_goal reached.")
    user_id = request.headers.get("User-ID") or request.headers.get("User-Id")
    username = request.headers.get("Username")
    file_type = request.headers.get("File-Type", ".m4a")

    if not user_id:
        return jsonify({"error": "Missing User-ID in header"}), 401
    if not username:
        return jsonify({"error": "Missing Username in header"}), 401

    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    audio_file = request.data
    if not audio_file:
        return jsonify({"error": "Missing audio file"}), 400

    # Transcribe the audio file
    temp_filename = f"temp_{user_id}_{uuid.uuid4()}{file_type}"
    temp_path = os.path.join("/tmp", temp_filename)

    transcription = ""
    try:
        with open(temp_path, "wb") as f:
            f.write(audio_file)
        aws.upload_to_s3(temp_path)
        transcription = aws.transcription_service(temp_path, clean_up=True)
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception as e:
        logger.info(e)
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if not transcription:
        return jsonify({"error": "Transcription failed"}), 400

    llm = LLMClient(use_case=LLMClient.UseCase.EXTRACT_GOAL_CONTENT, user_id=username)
    result, valid, _ = llm.query(content=transcription)
    logger.info("extract_goal LLM output: %s", result)

    if not valid:
        return jsonify({"error": "Failed to extract goal content"}), 500

    return jsonify(result)


# ---------------------------------------------------------------------------
# End of day summary
# ---------------------------------------------------------------------------


@app.route("/stt/eod_summary", methods=["POST"])
def eod_summary():
    logger.info("🌙 /stt/eod_summary reached.")
    """Given a transcription from a user's STT, return a LLM-generated summary"""
    # Grab metadata from user
    logger.info("🌙 Reached the EOD Summary endpoint")
    username = request.headers.get("Username")
    file_type = request.headers.get("File-Type", ".m4a")

    audio_file = request.data
    if not username:
        return jsonify({"error": "Missing Username in header"}), 401

    # Check authentication
    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    if not file_type:
        return jsonify({"error": "Missing File Type in header"}), 402

    if not audio_file:
        return jsonify({"error": "Missing Audio File"}), 403
    # Create temporary audio filename and path for transcription
    temp_filename = f"temp_{username}_{uuid.uuid4()}{file_type}"
    temp_path = os.path.join("/tmp", temp_filename)

    # Transcribe the audio file
    transcription = ""
    try:
        with open(temp_path, "wb") as f:
            f.write(audio_file)

        # Upload to s3 and then transcribe
        aws.upload_to_s3(temp_path)
        transcription = aws.transcription_service(temp_path, clean_up=True)
        # Cleanup local file
        if os.path.exists(temp_path):
            os.remove(temp_path)

    except Exception as e:
        logger.info(e)
        return jsonify({"error": str(e)}), 500
    finally:
        # Final cleanup if something goes wrong
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if not transcription:
        return jsonify({"error": "Transcription failed"}), 400

    # Setup LLM with eod_summary instructions
    llm_model = LLMClient(
        use_case=LLMClient.UseCase.SUMMARIZE_TRANSCRIPTION, user_id=username
    )

    # Get user's daily tasks
    tasks = db.get_daily_tasks(username)

    # Add daily tasks to the LLM's context
    daily_tasks = [
        f"Task: {t['task']}, Overarching Goal: {t['goal_name']}.\n" for t in tasks
    ]
    formatted_tasks = "Today's Tasks:\n" + " ".join(daily_tasks)
    llm_model.context(formatted_tasks)

    # Query the LLM with the transcription, which returns the summary
    summary = llm_model.query(content=transcription)
    logger.info(summary[0])
    logger.info(transcription)
    return jsonify({"summary": summary[0], "transcription": transcription})


# Save convo to chromadb
@app.route("/stt/save_convo", methods=["POST"])
def save_convo():
    logger.info("💬 /stt/save_convo reached.")
    data = request.get_json()
    userid = data.get("user_id")
    transcription = data.get("transcription")
    logger.info("Transcription: " + transcription)

    if not userid or not transcription:
        return jsonify({"error": "Missing information"})

    # Check authentication
    if not check_auth(dict(request.headers)):
        return jsonify({"error": "User isn't authenticated"}), 401

    # Initialize LLMClient
    llm_client = LLMClient(use_case=LLMClient.UseCase.GENERATE_TALKING_POINTS)
    logger.info("Initialized LLM Client for talking points")
    # Query the LLM to get the entries for our conversation
    json_convo_args, valid, _ = llm_client.query(transcription)
    logger.info(str(json_convo_args))
    logger.info("Validity: " + str(valid))
    if not valid:
        return jsonify({"error": "LLM was unable to get valid entries"}), 400

    # Store convo in chromadb with what the LLM returned
    logger.info(f"Storing the following convo in chromadb for user:")
    for arg in json_convo_args:
        logger.info(arg.get("verbose_summary"))
        chroma.store_talking_point(
            user_id=userid,
            document=arg.get("document"),
            verbose_summary=arg.get("verbose_summary"),
            static_trait=bool(arg.get("static_trait")),
            end_timestamp=int(arg.get("end_timestamp")),
        )
    logger.info("done with chroma store")

    return "", 204


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5010)
