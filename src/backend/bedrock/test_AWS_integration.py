import pytest
from bedrock.LLM_manage import LLM
from botocore.exceptions import ClientError

# Run with: pytest -m integration -s
pytestmark = pytest.mark.integration

class TestBedrockSocialAccountability:

    @pytest.fixture(scope="class")
    def strict_helper(self):
        """
        Returns an LLM instance configured as a strict accountability helper/enforcer.
        """
        rules = (
            "You are a Social Accountability Helper. "
            "Your job is to cross-examine users on their goals. "
            "Inform them on how they're doing on their goals but be firm and tough on them if they're struggling."
        )
        return LLM(model_strength=1, instructions=rules)

    @pytest.fixture(scope="class")
    def gentle_helper(self):
        """
        Returns an LLM instance configured as a gentle accountability and goal helper
        """
        rules = (
            "You are a Social Accountability Helper. "
            "Your job is to provide gentle but honest feedback to users on their goals. "
            "Be encouraging but also make sure the users are aware of their progress."
        )
        return LLM(model_strength=2, instructions=rules)

    # --- TEST 1: The "Goldfish" Memory Check ---
    
    def test_context_manual_memory(self, strict_helper):
        """
        Verifies that the context correctly simulates memory 
        by sending previous goals back to the AI.
        """
        # Add a goal to the context
        strict_helper.add_to_context("Goal: I will complete 50 LeetCode problems by Friday.")
        
        # Check-in without flushing the context
        response_1 = strict_helper.query("I just finished 10 problems.", flush=False)
        print(f"\n[Strict Helper Turn 1]: {response_1}")
        
        # Ask a question that requires the previous context to answer
        # If the context's memory fails, the AI won't know the target was 50.
        response_2 = strict_helper.query("Based on my goal, how many do I have left?")
        print(f"\n[Strict Helper Turn 2]: {response_2}")
        
        assert "40" in response_2 or "forty" in response_2.lower()
        # Verify the context was flushed after the final query
        assert len(strict_helper.context) == 0

    # --- TEST 2: The "Strict" Persona Check ---

    def test_persona_diff(self, strict_helper, gentle_helper):
        """Checks if the 'instructions' variable changes how the AI responds"""
        strict_response = strict_helper.query("I'm done with my gym session for today.")
        gentle_response = gentle_helper.query("I'm done with my gym session for today.")
        
        # A gentle accountability helpers shouldn't respond in the same way as a strict helper
        assert strict_response != gentle_response

    # --- TEST 3: Multi-Goal Conflict With Flushing ---

    def test_switching_goals_with_flush(self, strict_helper):
        """Ensures that flushing correctly prevents 'Goal Bleed'."""
        # 1. Set a Fitness Goal and flush it
        strict_helper.add_to_context("Goal: 100 pushups.")
        strict_helper.query("I did 50.", flush=True)

        # 2. Set a Study Goal
        response = strict_helper.query("I'm studying Python now. What was my physical goal?")
        
        # Because we flushed, the AI should NOT remember the pushups.
        # It should say it doesn't know or ask for the goal again.
        assert "100" not in response
        assert "pushup" not in response.lower()

    # --- TEST 4: Multi-Goal Conflict W/O Flushing ---

    def test_switching_goals_without_flush(self, gentle_helper):
        """Ensures that not flushing correctly ensures that all previous goals are remembered"""
        # Set a study goal and do not flush
        gentle_helper.add_to_context("Goal: Study for 20 hours this week.")
        gentle_helper.query("I have studied for 12 hours so far this week.")

        # Set a social goal
        gentle_helper.add_to_context("Goal: Hang out with friends 3 different nights this week.")
        response = gentle_helper.query("I have hung out with friends for 3 nights this week. How many more nights do I need for my study goal?")

        # Since we didn't flush, the AI should remember that we need to study for 8 more hours
        assert "8" in response or "eight" in response.lower()

    # --- TEST 5: Edge Case - The 'Silent' User ---

    def test_empty_input_behavior(self, strict_helper):
        """Verifies the system handles empty strings without AWS crashing."""
        try:
            response = strict_helper.query("")
            assert isinstance(response, str)
            assert len(response) > 0
        except ClientError as e:
            pytest.fail(f"AWS rejected empty string: {e}")

    # --- TEST 6: Real-World Latency & Throttling ---

    def test_rapid_accountability_pings(self, strict_helper):
        """Simulates 3 quick 'check-ins' to ensure the connection is stable."""
        for i in range(3):
            res = strict_helper.query(f"Update {i}: I am still working on my task.")
            assert len(res) > 0
    
    # --- TEST 7: Additional Gentle Helper Testing
    
    def test_gentle_helper(self, gentle_helper):
        gentle_helper.add_to_context("My goal is to read 10 books this month.")
        gentle_helper.add_to_context("This week I have read 3 books.")
        assert "My goal is to read 10 books this month." in gentle_helper.context

        first_resp = gentle_helper.query("How am I doing on my goal?", flush=False)
        assert "3" in first_resp or "three" in first_resp.lower()
        assert "My goal is to read 10 books this month." in gentle_helper.context

        second_resp = gentle_helper.query("How much of my goal do I have left?", flush=False)
        assert "7" in second_resp or "seven" in second_resp.lower()
        assert "My goal is to read 10 books this month." in gentle_helper.context
    
        gentle_helper.add_to_context("It's been a month since I met my goal and I've read 5 more books.")
        third_resp = gentle_helper.query("Did I meet my goal?")
        assert "yes" not in third_resp.lower()
        