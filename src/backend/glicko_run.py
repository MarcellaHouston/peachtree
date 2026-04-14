# Daily update of user glicko ratings

from app import db
from glicko import Glicko
from datetime import date
import math

# remove after testiing
import json

#### QUESTIONS TO ASK ####
# Do we need some form of sigmoid dampener within Glicko? MAYBE


def daily_glicko_update():
    users = db.select("users")
    today_name = date.today().strftime("%A").lower()
    for user in users:
        try:
            user_id = user[0]
            user_rating = user[4]
            user_RD = user[5]
            user_volatility = user[6]
            weekly_schedule = user[7]
            # FOR TESTING ONLY
            try:
                schedule_dict = json.loads(weekly_schedule)
                print(json.dumps(schedule_dict))
            except (json.JSONDecodeError, TypeError):
                print("Skipping user, invalid JSON\n")
                continue

            today_task_list = schedule_dict.get(today_name, [])
            # If user had no tasks today, thus not competing, most of the algorithm doesn't apply (only RD changes)
            if not today_task_list:
                scaled_RD = user_RD / 173.7178
                new_RD = math.sqrt(pow(scaled_RD, 2) + pow(user_volatility, 2))
                new_scaled_RD = new_RD * 173.7178
                db.update_user_glicko(user_id, user_rating, new_scaled_RD, user_volatility)
                continue

            glicko_task_data = []
            for task in today_task_list:
                # Calculate task ELO (either store rating in tasks table and
                # retrieve it using task_id from weekly_schedule, or calculate elo here without need to
                # store rating)
                # For now, have it set as a constant value to be passed in. 
                # Also, for now, have constant RD value for tasks
                task_rating = 1200
                task_RD = 50.0

                task_data = db.get_glicko_task_data(task["task_id"])
                task_rating, task_RD = calculate_task_glicko(task_data["impetus"], task_data["difficulty_score"], task_data["goal_id"])
                task_score = 1 if task["completed"] else 0
                glicko_task_data.append({
                    "task_rating": task_rating,
                    "task_RD": task_RD,
                    "task_score": task_score
                })

            # Perform Glicko algorithm to update user rating, RD, and volatility
            glicko = Glicko(user_rating, user_RD, user_volatility, glicko_task_data)
            rating, RD, volatility = glicko.perform_glicko()

            # Update user's glicko data in database
            db.update_user_glicko(user_id, rating, RD, volatility)
        
        except Exception as e:
            print("Unexpected error\n")
            continue


def calculate_task_glicko(impetus: int, difficulty: int, goal_diff: str) -> tuple:
    # Base task rating should range from 30 to 3000
    base_rating = difficulty * 30

    # Our algorithm - high impetus --> easy to start --> smaller effect on rating
    impetus_effect = (5 - impetus) * 25

    goal_diff_effect = 0
    if goal_diff == "easy":
        goal_diff_effect = -50
    elif goal_diff == "hard":
        goal_diff_effect = 50

    task_rating = float(max(0, base_rating + impetus_effect + goal_diff_effect))

    # For the RD of our tasks, they should be treated as well-established "opponents"
    # This means the RD should be low, as tasks should perform how they are expected to
    task_RD = 30.0

    return task_rating, task_RD