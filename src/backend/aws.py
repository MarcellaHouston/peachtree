# AWS Service libraries (transcription, uploading .mp3 files to AWS)
import os
import time
import boto3
import requests


# InvalidAudioFile error class
class InvalidAudioFile(Exception):
    pass


# allowed audio file formats, iPhones use m4a or wav, mp3 is used for testing
AUDIO_FORMATS = [".mp3", ".wav", ".m4a"]

# Our bucket name on AWS s3
BUCKET_NAME = "boto3testbucket498peachtree"


def upload_to_s3(filename: str) -> None:
    """uploads an audio file to our s3 bucket"""
    base = os.path.basename(filename)
    name, end = os.path.splitext(base)

    # if the file format isn't supported, raise an InvalidAudioFile error
    if end not in AUDIO_FORMATS:
        raise InvalidAudioFile("Invalid audio file: must be.mp3 or .wav")

    s3_client = boto3.client('s3')

    # Upload file to our client
    s3_client.upload_file(
        Filename=filename,
	    Bucket="boto3testbucket498peachtree",
	    Key=name
    )
    return


def delete_file(filename: str) -> None:
    """Delete designated files from our s3 instance"""
    s3_client = boto3.client('s3')
    s3_client.delete_object(Bucket=BUCKET_NAME, Key=filename)
    print(f"Deleted file {filename} from {BUCKET_NAME}")


def delete_job(job_name: str) -> None:
    """Delete designated transcription job from our account"""
    transcribe = boto3.client('transcribe')
    transcribe.delete_transcription_job(TranscriptionJobName=job_name)
    print(f"Deleted job: {job_name} from {BUCKET_NAME}")


def cleanup(s3_filename: str, job_name: str) -> None:
    """Clean up after job by deleting s3 file and transcription job"""
    delete_file(s3_filename)
    delete_job(job_name)
    print(f"Deleted {s3_filename} from s3 and {job_name} from AWS Transcribe")


def transcription_service(filename: str, clean_up=False) -> None:
    """Given an audio file, perform a transcription job on its message"""
    base = os.path.basename(filename)
    name, end = os.path.splitext(base)
    # If the filename isn't a .mp3 file, it cannot be in our
    if end not in AUDIO_FORMATS:
        raise InvalidAudioFile("File should be .mp3, .m4a, or .wav format")

    transcribe = boto3.client('transcribe', region_name='us-east-2')

    # get JSON response from our transcription client
    job_name = f"MyTranscriptionJob-{int(time.time())}"

    media_format = end.replace(".", "")
    response = transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': f's3://boto3testbucket498peachtree/{name}'},
        MediaFormat=media_format,
        LanguageCode='en-US'
    )

    # Wait until the transcription either completes or fails
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        job_status = status['TranscriptionJob']['TranscriptionJobStatus']
        print("Status:", job_status)

        if job_status in ['COMPLETED', 'FAILED']:
            break
        time.sleep(5)

    # Once completed, fetch and print the English transcript
    if job_status == 'COMPLETED':
        url = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        transcript_json = requests.get(url).json()
        text = transcript_json['results']['transcripts'][0]['transcript']
        print("\nEnglish Transcription is:\n")
        print(text)
    else:
        print("Transcription failed.")

    # if cleanup was passed in, cleanup by deleting job and audio file
    if clean_up:
        cleanup(name, job_name)
    return
