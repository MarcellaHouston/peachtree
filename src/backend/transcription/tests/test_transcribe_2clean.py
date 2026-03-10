import transcription.aws

'''
    - Make sure you're in a virtual environment
    - Set it up with $ python -m venv .venv
    - Activate it with $ source .venv/bin/activate
    - Make sure you are running tests from src/backend
    - "{python OR python3} -m transcription.tests.{TEST_FILE_NAME}
'''

expected = "Early to bed and early to rise makes a man healthy, wealthy, and wise. Benjamin Franklin."
print(f"Expected English Transcription is: {expected}")
transcription.aws.upload_to_s3("transcription/tests/test_audios/test_audio2.m4a")
ts = transcription.aws.transcription_service("transcription/tests/test_audios/test_audio2.m4a", clean_up=True)
print(f"Returned English Transcription: {ts}")
