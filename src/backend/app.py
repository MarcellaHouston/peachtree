from flask import Flask, request, jsonify
from datetime import datetime, timedelta, date

app = Flask(__name__)

# In-memory "DB"
# Replace with real endpoint once finished TODO
GOALS = []
NEXT_ID = 1

ALLOWED_MEASURABLE = {"completion", "scalar", "count", "range"}


def parse_date(s):
    if not s:
        return None
    if isinstance(s, str):
        return datetime.strptime(s, "%Y-%m-%d").date()
    return s


def validate_goal(goal, creating: bool):
    errors = []

    # Required fields
    if not goal.get("name"):
        errors.append("name is required")
    if not goal.get("measurable"):
        errors.append("measurable is required")
    elif goal.get("measurable") not in ALLOWED_MEASURABLE:
        errors.append(f"measurable must be one of {list(ALLOWED_MEASURABLE)}")

    if not goal.get("end_date"):
        errors.append("end_date is required")

    if goal.get("tasks") is None or not isinstance(goal.get("tasks"), list):
        errors.append("tasks must be an array")

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

    results = []

    # replace this with real db TODO
    for g in GOALS:
        g_start = parse_date(g.get("start_date"))
        g_end = parse_date(g.get("end_date"))

        # Overlap check
        if start_date and g_end and g_end < start_date:
            continue
        if end_date and g_start and g_start > end_date:
            continue

        results.append(g)

    return jsonify({"goals": results})


@app.route("/goals/update", methods=["POST"])
def update_goal():
    global NEXT_ID

    data = request.get_json()
    if not data or "goal" not in data:
        return jsonify({"error": "Missing 'goal' in request body"}), 400

    goal = data["goal"] 

    # Validation
    errors = validate_goal(goal, creating=not goal.get("id"))
    if errors:
        return jsonify({"errors": errors}), 400

    # Default start_date = today
    if not goal.get("start_date"):
        goal["start_date"] = date.today().isoformat()

    # Ensure dates are strings (YYYY-MM-DD)
    # TODO replace 
    goal["start_date"] = parse_date(goal["start_date"]).isoformat()
    goal["end_date"] = parse_date(goal["end_date"]).isoformat()

    goal_id = goal.get("id") # TODO replace 

    # Create new
    # TODO replace v
    if not goal_id:
        new_goal = goal.copy()
        new_goal["id"] = NEXT_ID
        NEXT_ID += 1

        GOALS.append(new_goal)
        return "", 204

    # Update existing
    for i, g in enumerate(GOALS):
        if g["id"] == goal_id:
            updated = g.copy()
            updated.update(goal)
            GOALS[i] = updated
            return "", 204

    # If not found, create with given id (optional behavior)
    new_goal = goal.copy()
    new_goal["id"] = goal_id
    GOALS.append(new_goal)
    # TODO replace ^
    return "", 204


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)