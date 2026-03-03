import transcription.aws

# Make sure you are running tests from src/backend

expected = "Early to bed and early to rise makes a man healthy, wealthy, and wise. Benjamin Franklin."
print(f"Expected English Transcription is: {expected}")
transcription.aws.upload_to_s3("transcription/tests/test_audios/test_audio2.m4a")
transcription.aws.transcription_service("transcription/tests/test_audios/test_audio2.m4a", clean_up=True)
