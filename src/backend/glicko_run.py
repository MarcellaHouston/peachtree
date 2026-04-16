# Daily update of user glicko ratings

from app import db
from glicko import Glicko
from datetime import date
import math
import json


def daily_glicko_update():
    # Get all users from database
    users = db.select("users")
    # Get the current day (in the form of "monday", "tuesday", etc.)
    today_name = date.today().strftime("%A").lower()
    for user in users:
        try:
            user_id = user[0]
            user_rating = user[4]
            user_RD = user[5]
            user_volatility = user[6]
            weekly_schedule = user[7]

            try:
                schedule_dict = json.loads(weekly_schedule)
            except (json.JSONDecodeError, TypeError):
                print("Skipping user, invalid JSON\n")
                continue

            # today_task_list should be a list of the user's tasks for today.
            # Each task should have a taskid and a completed field
            today_task_list = schedule_dict.get(today_name, [])

            glicko_task_data = []
            for task in today_task_list:
                # Get task data needed for Glicko calculation (impetus, difficulty_score,
                # and associated goal_id)
                task_data = db.get_glicko_task_data(task["task_id"])
                # If task doesn't exist (got deleted somehow), just move to the next task
                if not task_data:
                    continue
                # Calculate task rating and task rating deviation
                task_rating, task_RD = calculate_task_glicko(task_data["impetus"], task_data["difficulty_score"], task_data["goal_difficulty"])
                # Task score is a 1 if user "beat" (completed) the task, 0 if user "lost" (failed)
                task_score = 1 if task["completed"] else 0
                glicko_task_data.append({
                    "task_rating": task_rating,
                    "task_RD": task_RD,
                    "task_score": task_score
                })

            # Perform Glicko algorithm to update user rating, RD, and volatility
            # If user had no tasks today, algorithm still runs --> RD changes but rating and volatility don't
            glicko = Glicko(user_rating, user_RD, user_volatility, glicko_task_data)
            rating, RD, volatility = glicko.perform_glicko()

            # Update user's glicko data in database
            db.update_user_glicko(user_id, rating, RD, volatility)
        
        except Exception as e:
            print(f"Unexpected error {e}\n")
            continue


def calculate_task_glicko(impetus: int, difficulty: int, goal_diff: str) -> tuple:
    # Base task rating should range from 30 to 3000
    base_rating = difficulty * 30

    # Our algorithm - high impetus --> easy to start --> smaller effect on rating
    impetus_effect = (5 - impetus) * 25

    # If the goal that the task belongs to is easy, remove some of the task's difficulty
    # If the goal is medium, don't change the task rating
    # If the goal is hard, add a little bit to the task difficulty
    goal_diff_effect = 0
    if goal_diff == "easy":
        goal_diff_effect = -50
    elif goal_diff == "hard":
        goal_diff_effect = 50

    # make sure task rating is positive. Should be between 1 and 3150, inclusive
    task_rating = float(max(1, base_rating + impetus_effect + goal_diff_effect))

    # For the RD of our tasks, they should be treated as well-established "opponents"
    # This means the RD should be low, as tasks should perform how they are expected to
    task_RD = 30.0

    return task_rating, task_RD