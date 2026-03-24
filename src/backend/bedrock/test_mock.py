import pytest
from unittest.mock import MagicMock, patch
from bedrock.llm import LLM

@pytest.fixture
def llm_instance():
    """Provides a fresh LLM instance for every test."""
    return LLM(model_strength=1)

@pytest.fixture
def mock_bedrock():
    """Mocks the boto3 client and the converse response."""
    with patch("boto3.client") as mock_client:
        mock_instance = MagicMock()
        # Standard successful response structure
        mock_instance.converse.return_value = {
            "output": {
                "message": {
                    "content": [{"text": "Success Summary"}]
                }
            }
        }
        mock_client.return_value = mock_instance
        yield mock_instance

# --- Core Case: Success Path ---
def test_query_success(llm_instance, mock_bedrock):
    llm_instance.client = mock_bedrock
    result = llm_instance.query("I finished my 50 problems.")
    
    assert result == "Success Summary"
    mock_bedrock.converse.assert_called_once()

# --- Edge Case: Empty/Whitespace Input ---
@pytest.mark.parametrize("bad_input", ["", "   ", "\n", None])
def test_query_empty_input(llm_instance, bad_input):
    result = llm_instance.query(bad_input)
    assert result == "How can Reach Help?"

# --- Edge Case: AWS API Error ---
def test_query_aws_exception(llm_instance, mock_bedrock):
    llm_instance.client = mock_bedrock
    mock_bedrock.converse.side_effect = Exception("ThrottlingException")
    
    result = llm_instance.query("Valid input")
    assert "Error: ThrottlingException" in result

# --- Core Case: Context Integration ---
def test_prompt_construction_with_context(llm_instance, mock_bedrock):
    llm_instance.client = mock_bedrock
    llm_instance.add_to_context("Goal: 50 Problems")
    llm_instance.add_to_context("Deadline: Friday")
    
    llm_instance.query("I did 10")
    
    # Capture what was actually sent to Bedrock
    args, kwargs = mock_bedrock.converse.call_args
    sent_messages = kwargs['messages']
    sent_text = sent_messages[0]['content'][0]['text']
    
    # Verify the context was injected into the string
    assert "Context: Goal: 50 Problems\nDeadline: Friday" in sent_text
    assert "Query: I did 10" in sent_text

# --- Logic Case: Flush vs. No Flush ---
def test_flush_logic_clears_data(llm_instance, mock_bedrock):
    llm_instance.client = mock_bedrock
    llm_instance.add_to_context("Temporary Data")
    
    # With flush=True
    llm_instance.query("Clear me", flush=True)
    assert len(llm_instance.context) == 0
    assert len(llm_instance.previous_conversation) == 0

def test_no_flush_retains_history(llm_instance, mock_bedrock):
    llm_instance.client = mock_bedrock
    
    # With flush=False
    llm_instance.query("Keep me", flush=False)
    assert len(llm_instance.previous_conversation) == 2 # Human + AI response
    assert "Human Query: Keep me" in llm_instance.previous_conversation[0]

# --- Model Strength Mapping ---
def test_model_strength_mapping(llm_instance):
    # Test mapping for strength 3
    strong_llm = LLM(model_strength=3)
    assert strong_llm.model_id == "google.gemma-3-27b-it"
    
    # Test fallback for invalid strength
    weird_llm = LLM(model_strength=99)
    assert weird_llm.model_id == "google.gemma-3-4b-it"

# --- Unexpected API Structure ---
def test_malformed_bedrock_response(llm_instance, mock_bedrock):
    llm_instance.client = mock_bedrock
    # Force a response that will cause the index error inside the LLM class
    mock_bedrock.converse.return_value = {"output": {"message": {"content": []}}}
    
    # Run the query
    result = llm_instance.query("Valid input")
    
    # ASSERTION: Check that the error message was caught and returned
    assert "Error" in result
    assert "index out of range" in result

# --- Emojis and Abnormal Characters ---
def test_unicode_and_emojis(llm_instance, mock_bedrock):
    llm_instance.client = mock_bedrock
    emoji_input = "I finished my 🎯 goals and felt 🔥!"
    llm_instance.add_to_context("Goal: 🚀 to the moon")
    
    result = llm_instance.query(emoji_input)
    assert result == "Success Summary"