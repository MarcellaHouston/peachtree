import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from bedrock.LLM_manage import LLM

class TestSocialAccountabilityAgent:

    @pytest.fixture
    def mock_bedrock(self):
        """Mocks the Bedrock client to return a firm accountability response."""
        with patch("boto3.client") as mock_client:
            mock_response = {
                "output": {
                    "message": {
                        "content": [{"text": "I've logged your 5:00 AM gym commitment. I will check in at 6:30 AM for proof."}]
                    }
                }
            }
            mock_client.return_value.converse.return_value = mock_response
            yield mock_client

    # --- INSTRUCTIONS (SYSTEM PROMPT) LOGIC ---

    def test_system_instructions_passed_correctly(self, mock_bedrock):
        """Verifies the 'instructions' variable is correctly mapped to the system field."""
        social_rules = "You are a social referee. Be firm and demand proof for every goal."
        llm = LLM(instructions=social_rules)
        
        llm.query("I want to study for 2 hours.")
        
        _, kwargs = mock_bedrock.return_value.converse.call_args
        # The 'system' field should contain our social_rules
        assert kwargs['system'][0]['text'] == social_rules
        # Ensure it's using the budget-friendly model
        assert kwargs['modelId'] == "google.gemma-3-4b-it"

    # --- SOCIAL ACCOUNTABILITY SCENARIOS ---

    def test_gym_commitment_with_context(self, mock_bedrock):
        """Tests merging a user's previous 'failed' attempts with a new gym goal."""
        llm = LLM(instructions="Remind the user of their past slip-ups to keep them honest.")
        llm.add_to_context("Last Week: User missed 3 out of 5 planned gym sessions.")
        
        llm.query("I'm going to the gym now, I promise.")

        _, kwargs = mock_bedrock.return_value.converse.call_args
        actual_payload = kwargs['messages'][0]['content'][0]['text']
        
        assert "missed 3 out of 5" in actual_payload
        assert "going to the gym" in actual_payload

    def test_study_group_accountability(self, mock_bedrock):
        """Tests context retention for a social study group 'vow'."""
        llm = LLM(instructions="Track group study goals.")
        llm.add_to_context("Group Goal: Complete 50 practice problems by Friday.")
        
        # Turn 1: Check progress
        llm.query("We've done 10 problems so far.", flush=False)
        assert len(llm.context) == 2
        
        # Turn 2: Ask for a status update based on memory
        llm.query("How many do we have left to hit our target?")
        _, kwargs = mock_bedrock.return_value.converse.call_args
        
        print(kwargs['messages'][0]['content'][0]['text'])

        assert "50 practice problems" in kwargs['messages'][0]['content'][0]['text']
        assert "10 problems" in kwargs['messages'][0]['content'][0]['text']

    # --- EDGE CASES & ERRORS ---

    def test_empty_accountability_query(self, mock_bedrock):
        """Ensures the agent doesn't crash if a user pings the accountability bot without text."""
        llm = LLM()
        result = llm.query("")
        # Should return the mocked 'Coach' response safely
        assert "5:00 AM gym commitment" in result

    def test_aws_throttling_during_checkin(self, mock_bedrock):
        """Simulates an AWS error when a user is trying to submit proof of work."""
        error_response = {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate limit exceeded'}}
        mock_bedrock.return_value.converse.side_effect = ClientError(error_response, 'converse')

        llm = LLM()
        with pytest.raises(ClientError):
            llm.query("Here is my photo proof of the completed practice problems.")

    def test_coding_streak_emojis(self, mock_bedrock):
        """Ensures coding streak markers don't break the message structure."""
        llm = LLM()
        llm.query("Day 45: 💻 10 LeetCode problems done. No ☕ needed!")
        _, kwargs = mock_bedrock.return_value.converse.call_args
        assert "💻" in kwargs['messages'][0]['content'][0]['text']