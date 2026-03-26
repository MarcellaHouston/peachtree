from flask import Flask, request, jsonify
from datetime import datetime, timedelta, date
from sql_db import Database
from bedrock.llm import LLMClient
import transcription.aws as aws
import chromaDB.chroma_db as chroma
import os
import uuid
import json

import logging

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


@app.route("/")
def hello():
    return "Hello"


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------


@app.route("/goals", methods=["POST"])
def get_goals():
    # Return all goals that overlap the requested date range.
    # If no dates are provided, defaults to goals active in the past 7 days.
    # If user_id is provided, also runs the weekly schedule check.
    data = request.get_json(silent=True) or {}

    start_date = parse_date(data.get("start_date"))
    end_date = parse_date(data.get("end_date"))

    if not start_date and not end_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

    rows = db.select("goals", "all")
    results = []
    for row in rows:
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

    response = {"goals": results}

    user_id = data.get("user_id")
    if user_id:
        new_week, schedule = db.check_new_week(user_id)
        response["new_week"] = new_week
        response["schedule"] = schedule

    return jsonify(response)


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

    if goal.get("days_of_week")[-1] == ",":
        goal["days_of_week"] = goal["days_of_week"][:-1]

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
        ],
    )

    llm_payload = {
        "goal_name": goal["name"],
        "start_date": goal["start_date"],
        "end_date": goal["end_date"],
        "difficulty": goal["difficulty"],
        "days_of_week": goal.get("days_of_week"),
    }

    llm_model = LLMClient(LLMClient.UseCase.GENERATE_TASKS, user_id=goal["user_id"])
    tasks, valid, retries = llm_model.query(content=json.dumps(llm_payload))

    logger.info("Starting task adds")
    if valid:
        logger.info("is valid!")
        for task in tasks:
            logger.info(task["task"])
            db.insert(
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
                ],
            )
    else:
        logger.info("Error with LLM")
        return (
            jsonify({"error": "LLM failed to generate tasks", "retries": retries}),
            500,
        )
    return "", 204


@app.route("/goals/update", methods=["POST"])
def update_goal():
    # Update an existing goal by id. All required fields must still be provided
    # (same validation as create). Only the fields passed in will be changed.
    data = request.get_json()
    if not data or "goal" not in data:
        return jsonify({"error": "Missing 'goal' in request body"}), 400

    goal = data["goal"]
    goal_id = goal.get("id")

    if not goal_id:
        return jsonify({"error": "Missing goal id for update"}), 400

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
    # Defer a goal by pushing its active_date forward by N weeks (snapped to Sunday).
    # The goal stays in the system but won't appear as active until that date.
    data = request.get_json()
    goal_id = data.get("id")
    weeks = data.get("weeks")
    if not goal_id or not weeks:
        return jsonify({"error": "Missing id or weeks"}), 400
    db.snooze(goal_id, weeks)
    return "", 204


@app.route("/goals/delete", methods=["POST"])
def delete_goal():
    # Delete a goal by id. Associated tasks are removed automatically via cascade.
    data = request.get_json(silent=True) or {}
    goal_id = data.get("id")
    if goal_id is None:
        return jsonify({"error": "Missing 'id' in request body"}), 400
    db.delete("goals", goal_id)
    return "", 204


@app.route("/tasks/complete", methods=["POST"])
def complete_task():
    # Mark a task as done or not-done in the user's current week_schedule.
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    status = data.get("status")
    if not user_id or task_id is None or status is None:
        return jsonify({"error": "Missing user_id, task_id, or status"}), 400
    db.set_task_status(user_id, task_id, status)
    return "", 204


# ---------------------------------------------------------------------------
# Weekly schedule
# ---------------------------------------------------------------------------


@app.route("/schedule/weekly", methods=["POST"])
def weekly_schedule():
    # not currently in use,1 get goals() call check_new_week
    # Called by the frontend on app startup.
    # Checks if the user has entered a new week (new Sunday). If so, reassigns
    # all active tasks to days based on the user's availability (round-robin).
    # Returns: { new_week: bool, schedule: { curr_week_start, monday: [...], ... } }

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    new_week, schedule = db.check_new_week(user_id)
    return jsonify({"new_week": new_week, "schedule": schedule})


@app.route("/daily_goal_digest", methods=["POST"])
def daily_goal_digest():
    # Called on startup after /schedule/weekly.
    # Returns today's tasks for the user, each paired with its goal name.
    # Response: { day: "monday", tasks: [{ task_id, task, goal_name, impetus, ... }] }
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    today_name = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ][(date.today().weekday()) + 1 % 7]
    db.check_new_week(user_id)
    tasks = db.get_daily_tasks(user_id)
    return jsonify({"day": today_name, "tasks": tasks})


# ---------------------------------------------------------------------------
# End of day summary
# ---------------------------------------------------------------------------


@app.route("/stt/eod_summary", methods=["POST"])
def eod_summary():
    """Given a transcription from a user's STT, return a LLM-generated summary"""
    # Grab metadata from user
    logger.info("🚀 Reached the EOD Summary endpoint")
    userid = request.headers.get("User-ID")
    file_type = request.headers.get("File-Type", ".m4a")
    audio_file = request.data
    if not userid:
        return jsonify({"error": "Missing User-ID in header"}), 401

    if not file_type:
        return jsonify({"error": "Missing File Type in header"}), 402

    if not audio_file:
        return jsonify({"error": "Missing Audio File"}), 403
    # Create temporary audio filename and path for transcription
    temp_filename = f"temp_{userid}_{uuid.uuid4()}{file_type}"
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
        use_case=LLMClient.UseCase.SUMMARIZE_TRANSCRIPTION, user_id=userid
    )

    # Get user's daily tasks
    tasks = db.get_daily_tasks(userid)

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
    data = request.get_json()
    userid = data.get("user_id")
    transcription = data.get("transcription")
    logger.info("Transcription: " + transcription)

    if not userid or not transcription:
        return jsonify({"error": "Missing information"})

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
