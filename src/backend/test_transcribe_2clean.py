import aws

expected = "Early to bed and early to rise makes a man healthy, wealthy, and wise. Benjamin Franklin."
print(f"Expected English Transcription is: {expected}")
aws.upload_to_s3("test_audios/test_audio2.m4a")
aws.transcription_service("test_audios/test_audio2.m4a", clean_up=True)
