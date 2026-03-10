import transcription.aws

'''
    - Make sure you're in a virtual environment
    - Set it up with $ python -m venv .venv
    - Activate it with $ source .venv/bin/activate
    - Make sure you are running tests from src/backend
    - "{python OR python3} -m transcription.tests.{TEST_FILE_NAME}
'''

transcription.aws.delete_file("test_audio3.m4a")

expected = "Ask not what your country can do for you, but what you can do for your country. John F. Kennedy."
print(f"Expected English Transcription is: {expected}")
transcription.aws.upload_to_s3("transcription/tests/test_audios/test_audio3.m4a")
ts = transcription.aws.transcription_service("transcription/tests/test_audios/test_audio3.m4a")
print(f"Returned English Transcription: {ts}")
