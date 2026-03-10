import transcription.aws

'''
    - Make sure you're in a virtual environment
    - Set it up with $ python -m venv .venv
    - Activate it with $ source .venv/bin/activate
    - Make sure you are running tests from src/backend
    - "{python OR python3} -m transcription.tests.{TEST_FILE_NAME}
'''

print("Expected English Transcription is: Here's the first test for transcription API.")
transcription.aws.upload_to_s3("transcription/tests/test_audios/test_audio1.mp3")
ts = transcription.aws.transcription_service("transcription/tests/test_audios/test_audio1.mp3", clean_up=True)
print(f"Returned English Transcription: {ts}")
