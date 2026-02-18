import boto3
import time
import json
import requests

# initialize clients
s3_client = boto3.client('s3')
transcribe = boto3.client('transcribe', region_name='us-east-2')

# upload audio file to s3
s3_client.upload_file(
	Filename="test_audios/test_audio1.mp3",
	Bucket="boto3testbucket498peachtree",
	Key="test_audio1.mp3"
)

# get JSON response from our transcription client
job_name = f"MyTranscriptionJob-{int(time.time())}"
response = transcribe.start_transcription_job(
	TranscriptionJobName=job_name,
	Media={'MediaFileUri': 's3://boto3testbucket498peachtree/test_audio1.mp3'},
	MediaFormat='mp3',
	LanguageCode='en-US'
)

# Extract the job name from the response
job_name = f"MyTranscriptionJob-{int(time.time())}"

# Poll until the transcription is completed
while True:
    status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    job_status = status['TranscriptionJob']['TranscriptionJobStatus']
    print("Status:", job_status)

    if job_status in ['COMPLETED', 'FAILED']:
        break
    time.sleep(5)

# Once completed, fetch and print the English transcript
if job_status == 'COMPLETED':
    transcript_url = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
    transcript_json = requests.get(transcript_url).json()
    english_text = transcript_json['results']['transcripts'][0]['transcript']
    print("\nEnglish Transcript:\n")
    print(english_text)
else:
    print("Transcription failed.")