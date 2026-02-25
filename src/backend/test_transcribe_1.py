import aws

print("Expected English Transcription is: Here's the first test for transcription API.")
aws.upload_to_s3("test_audios/test_audio1.mp3")
aws.transcription_service("test_audios/test_audio1.mp3")
