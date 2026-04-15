import pytest
from glicko import Glicko

def test_new_user_first_task():
    """
    A new user (1500, 350) completes one hard task.
    In Glicko-2, RD might stay high or slightly increase because 
    volatility is added before one single match can significantly lower it.
    """
    tasks = [{"task_rating": 2000, "task_RD": 30.0, "task_score": 1}]
    engine = Glicko(1500, 350, 0.06, tasks)
    new_r, new_rd, new_vol = engine.perform_glicko()
    
    # Completing a task should increase rating
    assert new_r > 1500
    # For a new user, the RD shouldn't explode up in value
    assert new_rd < 400 

def test_established_user_success():
    """
    An established user (1500, 50) completes a task.
    RD should remain low or decrease further.
    """
    tasks = [{"task_rating": 1600, "task_RD": 30.0, "task_score": 1}]
    engine = Glicko(1500, 50, 0.06, tasks)
    new_r, new_rd, new_vol = engine.perform_glicko()
    
    assert new_r > 1500
    assert new_rd < 55 # Ensuring no massive inflation in RD value

def test_high_volume_productivity_spike():
    """
    User completes 5 tasks in one update period.
    Multiple data points should significantly lower the RD (uncertainty).
    """
    # 5 successful tasks of varying difficulty
    tasks = [
        {"task_rating": 1200, "task_RD": 30.0, "task_score": 1},
        {"task_rating": 1500, "task_RD": 30.0, "task_score": 1},
        {"task_rating": 1800, "task_RD": 30.0, "task_score": 1},
        {"task_rating": 1400, "task_RD": 30.0, "task_score": 1},
        {"task_rating": 1600, "task_RD": 30.0, "task_score": 1},
    ]
    
    initial_rd = 150
    engine = Glicko(1500, initial_rd, 0.06, tasks)
    new_r, new_rd, new_vol = engine.perform_glicko()
    
    # There should be a significant rating jump
    assert new_r > 1600
    # Uncertainty should drop noticeably with 5 data points
    assert new_rd < initial_rd

def test_failed_streak_decreases_rating():
    """
    User fails multiple tasks. Rating should drop.
    """
    tasks = [
        {"task_rating": 1500, "task_RD": 30.0, "task_score": 0},
        {"task_rating": 1500, "task_RD": 30.0, "task_score": 0}
    ]
    engine = Glicko(1500, 100, 0.06, tasks)
    new_r, new_rd, new_vol = engine.perform_glicko()
    
    assert new_r < 1500
    assert new_rd < 110