import aws

aws.delete_file("test_audio3.m4a")

expected = "Ask not what your country can do for you, but what you can do for your country. John F. Kennedy."
print(f"Expected English Transcription is: {expected}")
aws.upload_to_s3("test_audios/test_audio3.m4a")
aws.transcription_service("test_audios/test_audio3.m4a")
