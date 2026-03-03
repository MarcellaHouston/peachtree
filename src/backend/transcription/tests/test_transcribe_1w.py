import transcription.aws

# Make sure you are running tests from src/backend

print("Expected English Transcription is: Here's the first test for transcription API.")
transcription.aws.upload_to_s3("transcription/tests/test_audios/test_audio1.wav")
transcription.aws.transcription_service("transcription/tests/test_audios/test_audio1.wav", clean_up=True)
