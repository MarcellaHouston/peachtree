import os
import sys
import pytest
from unittest.mock import MagicMock

# 1. Ensure the project root is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 2. Mock ChromaDB so it doesn't try to initialize local databases during AWS test
# Mock both potential naming conventions to be safe, matching the import in llm.py
mock_chroma = MagicMock()
sys.modules['backend.chromaDB'] = mock_chroma
sys.modules['backend.chromaDB.chroma_db'] = mock_chroma

# 3. Import modules
try:
    from backend.transcription import aws
    from backend.bedrock.llm import LLMClient
except ImportError as e:
    print(f"Import Error: {e}")
    print("TIP: Ensure you are running from the 'src' directory where the 'backend' folder lives.")
    raise

# --- TEST CONFIGURATION ---
TEST_AUDIO_FILE = os.path.join(os.path.dirname(__file__), 'sample_audio.m4a')


@pytest.mark.live_aws
def test_live_transcription_and_llm_summary():
    """
    Integration test that runs the exact logic of the EOD Summary route.
    It uploads to S3, runs Transcribe, and queries Bedrock.
    """
    if not os.path.exists(TEST_AUDIO_FILE):
        pytest.skip(f" Skipping test: Please place a real audio file at {TEST_AUDIO_FILE} to run the AWS integration test.")

    print("\n" + "="*50)
    print("🚀 STARTING LIVE AWS PIPELINE TEST")
    print("="*50)
    
    # ---------------------------------------------------------
    # PART 1: AWS S3 & TRANSCRIBE
    # ---------------------------------------------------------
    print(f"\n[1/3] Uploading {os.path.basename(TEST_AUDIO_FILE)} to AWS S3 bucket: {aws.BUCKET_NAME}...")
    try:
        aws.upload_to_s3(TEST_AUDIO_FILE)
        print(" Upload successful.")
    except Exception as e:
        pytest.fail(f"S3 Upload failed: {e}")

    print(f"\n[2/3] Starting AWS Transcribe job (This usually takes 30-90 seconds)...")
    try:
        # This function internally handles the while-loop polling and the cleanup
        transcription = aws.transcription_service(TEST_AUDIO_FILE, clean_up=True)
    except Exception as e:
        pytest.fail(f"AWS Transcribe failed: {e}")

    print("\n" + " "*20)
    print("RAW TRANSCRIPTION FROM AWS:")
    print("-" * 40)
    print(transcription)
    print("-" * 40)

    assert transcription is not None
    assert len(transcription) > 0, "Transcription returned an empty string."

    # ---------------------------------------------------------
    # PART 2: AWS BEDROCK LLM
    # ---------------------------------------------------------
    print("\n[3/3] Initializing Bedrock LLM Client...")
    llm_client = LLMClient(
        use_case=LLMClient.UseCase.SUMMARIZE_TRANSCRIPTION, 
        user_id="integration_test_user"
    )

    # Injecting fake tasks to mimic db.get_daily_tasks(userid) logic
    mock_tasks = [
        {"task": "Finish backend tests", "goal_name": "Launch MVP"},
        {"task": "Go for a 30 min run", "goal_name": "Health & Fitness"}
    ]
    daily_tasks_strings = [
        f"Task: {t['task']}, Overarching Goal: {t['goal_name']}." for t in mock_tasks
    ]
    formatted_tasks = "Today's Tasks:\n" + " ".join(daily_tasks_strings)
    
    print("\nInjecting Context into LLM:")
    print(formatted_tasks)
    llm_client.context(formatted_tasks)

    print("\nQuerying AWS Bedrock (Gemma)...")
    try:
        # Querying the LLM. In SUMMARIZE_TRANSCRIPTION mode, it returns the raw string directly.
        # However, the internal LLMClient logic for this use case returns (output, valid, retries)
        summary_result, is_valid, retries = llm_client.query(content=transcription)
    except Exception as e:
        pytest.fail(f"AWS Bedrock query failed: {e}")

    print("\n" + " "*20)
    print("FINAL SUMMARY FROM BEDROCK LLM:")
    print("-" * 40)
    print(summary_result)
    print("-" * 40)
    print(f"Metrics -> Valid format: {is_valid} | Retries needed: {retries}")
    
    assert is_valid is True, "LLM failed to return a valid response."
    assert summary_result is not None
    assert len(summary_result) > 0

    print("\n LIVE AWS INTEGRATION TEST COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    pytest.main(["-s", __file__])