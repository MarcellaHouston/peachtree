from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return "Flask backend is running"

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/api/echo", methods=["POST"])
def echo():
    data = request.json
    return jsonify({"you_sent": data})


#Request body
#Key	    Type	Required	Description
#start_date	Date	no	        Start date to get goals from.
#end_date	Date	no	        End date to get goals from.
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

    for g in GOALS:
        g_start = parse_date(g.get("start_date"))
        g_end = parse_date(g.get("end_date"))

        # Check if goal was created in given time window
        if start_date and g_end and g_end < start_date:
            continue
        if end_date and g_start and g_start > end_date:
            continue

        results.append(g)

    return jsonify({"goals": results})

# Request body
#Key    Type	Required	Description
#goal	string	yes	        JSON object of goal to modify
@app.route("/goals/update", methods=["POST"])
def update_goal():

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)