import boto3
from botocore.exceptions import NoCredentialsError, ClientError

s3 = boto3.client('s3')
response = s3.list_buckets()
print(response)



"""
try:
    s3 = boto3.client("s3")
    response = s3.list_buckets()

    print("Connected to S3 successfully!")
    print("Buckets:")

    for bucket in response["Buckets"]:
        print(" -", bucket["Name"])

except NoCredentialsError:
    print("No AWS credentials found.")

except ClientError as e:
    print("AWS error:", e)

except Exception as e:
    print("Unexpected error:", e)
"""