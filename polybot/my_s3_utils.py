import boto3
import os

s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION'))

def upload_to_s3(chat_id, image_path):
    bucket = os.getenv('AWS_S3_BUCKET')
    key = f"{chat_id}/original/{os.path.basename(image_path)}"
    s3.upload_file(image_path, bucket, key)
    return key
