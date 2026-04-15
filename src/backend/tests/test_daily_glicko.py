import pytest
import json
from unittest.mock import MagicMock, patch
from glicko_run import daily_glicko_update

@pytest.fixture
def mock_db_users():
    """Returns a mock user list."""
    return [
        # User 0: Bob (Active today with 1 task)
        [1, "Bob", "bob14", "pass", 1500, 350, 0.06, 
         json.dumps({"monday": [{"task_id": 101, "completed": True}]})],
        
        # User 1: Jim (Inactive today - no tasks scheduled for Monday)
        [2, "Jim", "jimrulez", "pass", 1600, 50, 0.06, 
         json.dumps({"tuesday": [{"task_id": 102, "completed": True}]})]
    ]

@patch('glicko_run.db')
@patch('glicko_run.date')
def test_daily_update_active_vs_inactive(mock_date, mock_db, mock_db_users):
    # 1. Setup: Freeze time to a Monday
    mock_monday = MagicMock()
    mock_monday.strftime.return_value = "monday"
    mock_date.today.return_value = mock_monday
    
    # 2. Setup: Mock DB responses
    mock_db.select.return_value = mock_db_users
    # Mock the task difficulty data for Aidan's task
    mock_db.get_glicko_task_data.return_value = {
        "impetus": 3,
        "difficulty_score": 50,
        "goal_id": "hard"
    }

    # 3. Execute
    daily_glicko_update()

    # --- VERIFY BOB (Active User) ---
    bob_call = [call for call in mock_db.update_user_glicko.call_args_list if call.args[0] == 1][0]
    bob_new_rd = bob_call.args[2]
    assert bob_new_rd < 350, "Bob's RD should decrease after completing a task"

    # --- VERIFY JIM (Inactive User) ---
    # Jim had no tasks for Monday.
    jim_call = [call for call in mock_db.update_user_glicko.call_args_list if call.args[0] == 2][0]
    jim_new_rd = jim_call.args[2]
    assert jim_new_rd > 50, "Jim's RD should increase due to inactivity"
    assert jim_call.args[1] == 1600, "Jim's rating should remain unchanged"

@patch('glicko_run.db')
@patch('glicko_run.date')
def test_cron_skips_empty_schedules(mock_date, mock_db):
    """Test behavior when a user exists but has a totally empty schedule string."""
    mock_monday = MagicMock()
    mock_monday.strftime.return_value = "monday"
    mock_date.today.return_value = mock_monday
    
    # User with an empty schedule dictionary
    mock_db.select.return_value = [
        [3, "Ghost", "ghost.com", "pw", 1200, 100, 0.06, json.dumps({})]
    ]
    
    daily_glicko_update()
    
    # User should still be updated (RD inflation for being inactive)
    assert mock_db.update_user_glicko.called
    args = mock_db.update_user_glicko.call_args.args
    assert args[0] == 3
    assert args[2] > 100

@patch('glicko_run.db')
def test_cron_resilience_to_bad_json(mock_db):
    # User 1 has broken JSON, User 2 is valid
    mock_db.select.return_value = [
        [1, "Broken", "b@ex.com", "pw", 1500, 350, 0.06, "{invalid_json!!"], 
        [2, "Valid", "v@ex.com", "pw", 1500, 350, 0.06, json.dumps({"monday": []})]
    ]
    
    # We wrap in a try/except if your code doesn't handle it, 
    # but ideally, your code should catch this.
    try:
        daily_glicko_update()
    except json.JSONDecodeError:
        pytest.fail("Cron job crashed on invalid JSON! Add a try/except block in the loop.")

    # Check that the second user was still processed
    # (Checking if update_user_glicko was called for ID 2)
    assert any(call.args[0] == 2 for call in mock_db.update_user_glicko.call_args_list)

@patch('glicko_run.db')
@patch('glicko_run.date')
def test_heavy_productivity_day(mock_date, mock_db):
    # Setup 10 completed tasks for one day
    tasks = [{"task_id": i, "completed": True} for i in range(10)]
    mock_db.select.return_value = [
        [1, "Overachiever", "a@b.com", "pw", 1500, 100, 0.06, json.dumps({"monday": tasks})]
    ]
    mock_db.get_glicko_task_data.return_value = {"impetus": 3, "difficulty_score": 50, "goal_id": "medium"}
    
    mock_date.today.return_value.strftime.return_value = "monday"
    
    daily_glicko_update()
    
    args = mock_db.update_user_glicko.call_args.args
    new_rating = args[1]
    
    # Glicko-2 should dampen multiple wins against the same "rating period."
    # A jump of > 500 points in one day usually signals a scaling bug.
    assert 1500 < new_rating < 2000


@patch('glicko_run.db')
@patch('glicko_run.date')
def test_deleted_task_graceful_failure(mock_date, mock_db):
    mock_db.select.return_value = [
        [1, "User", "u@ex.com", "pw", 1500, 350, 0.06, json.dumps({"monday": [{"task_id": 999, "completed": True}]})]
    ]
    
    # Simulate database returning None for a deleted task
    mock_db.get_glicko_task_data.return_value = None
    
    mock_date.today.return_value.strftime.return_value = "monday"

    # If your code isn't ready for this, it will raise a TypeError
    daily_glicko_update() 
    
    # Verify it still updated the user (probably treated as an inactive day or skipped task)
    assert mock_db.update_user_glicko.called