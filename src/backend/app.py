from flask import Flask, request, jsonify
from datetime import datetime, timedelta, date
from db import Database

app = Flask(__name__)

db = Database(create=False)  # set True only once if you want to recreate tables

ALLOWED_MEASURABLE = {"completion", "scalar", "count", "range"}

def parse_date(s):
    if not s:
        return None
    if isinstance(s, str):
        return datetime.strptime(s, "%Y-%m-%d").date()
    return s


def validate_goal(goal):
    errors = []

    if not goal.get("name"):
        errors.append("name is required")

    if not goal.get("measurable"):
        errors.append("measurable is required")
    elif goal.get("measurable") not in ALLOWED_MEASURABLE:
        errors.append(f"measurable must be one of {list(ALLOWED_MEASURABLE)}")

    if not goal.get("end_date"):
        errors.append("end_date is required")

    if not goal.get("user"):
        errors.append("user is required")

    return errors

@app.route("/goals", methods=["POST"])
def get_goals():
    data = request.get_json(silent=True) or {}

    start_date = parse_date(data.get("start_date"))
    end_date = parse_date(data.get("end_date"))

    # Default: past 7 days
    if not start_date and not end_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

    rows = db.select("goals", "all")
    results = []
    for row in rows:
        # Assuming select returns tuples in column order:
        goal = {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "measurable": row[3],
            "start_date": row[4],
            "end_date": row[5],
            "user": row[6],
        }

        g_start = parse_date(goal.get("start_date"))
        g_end = parse_date(goal.get("end_date"))

        # Date overlap filter
        if start_date and g_end and g_end < start_date:
            continue
        if end_date and g_start and g_start > end_date:
            continue

        results.append(goal)

    return jsonify({"goals": results})

@app.route("/goals/create", methods=["POST"])
def create_goal():
    data = request.get_json()
    if not data or "goal" not in data:
        return jsonify({"error": "Missing 'goal' in request body"}), 400

    goal = data["goal"]

    errors = validate_goal(goal)
    if errors:
        return jsonify({"errors": errors}), 400

    # Default start_date = today
    if not goal.get("start_date"):
        goal["start_date"] = date.today().isoformat()

    # Normalize dates
    goal["start_date"] = parse_date(goal["start_date"]).isoformat()
    goal["end_date"] = parse_date(goal["end_date"]).isoformat()

    # Insert into DB (order must match schema, excluding id)
    db.insert("goals", [
        goal["name"],
        goal.get("description"),
        goal["measurable"],
        goal["start_date"],
        goal["end_date"],
        goal["user"],
    ])

    return "", 204

@app.route("/goals/update", methods=["POST"])
def update_goal():
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

    # Normalize dates if present
    updates = goal.copy()
    updates.pop("id", None)

    if "start_date" in updates:
        updates["start_date"] = parse_date(updates["start_date"]).isoformat()
    if "end_date" in updates:
        updates["end_date"] = parse_date(updates["end_date"]).isoformat()

    db.update("goals", goal_id, updates)

    return "", 204


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)