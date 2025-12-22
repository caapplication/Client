"""
Script to fix ACL for existing client photos in S3
Makes them publicly readable
"""
import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
    print("Error: AWS credentials or S3_BUCKET_NAME not found in environment variables")
    sys.exit(1)

try:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    # List all objects in the clients/ prefix
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix='clients/')
    
    updated_count = 0
    for page in pages:
        if 'Contents' not in page:
            continue
        for obj in page['Contents']:
            object_name = obj['Key']
            try:
                # Set ACL to public-read
                s3_client.put_object_acl(
                    Bucket=S3_BUCKET_NAME,
                    Key=object_name,
                    ACL='public-read'
                )
                print(f"Updated ACL for: {object_name}")
                updated_count += 1
            except ClientError as e:
                print(f"Error updating {object_name}: {e}")
    
    print(f"\nSuccessfully updated ACL for {updated_count} objects")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

