import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi import HTTPException
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file - try multiple locations
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Also try loading from current directory (for local development)
    load_dotenv()

# Get credentials from environment (set by docker-compose or .env file)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Create S3 client at module level (same as Login service)
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def upload_file_to_s3(file, object_name=None):
    """
    Uploads a file to S3.

    :param file: A FastAPI UploadFile object or a file-like object.
    :param object_name: The name for the object in S3. If None, it's derived from file.filename.
    """
    fileobj_to_upload = None
    
    # Handle FastAPI UploadFile by checking for 'filename' and 'file' attributes
    if hasattr(file, 'filename') and hasattr(file, 'file'):
        if object_name is None:
            object_name = file.filename
        fileobj_to_upload = file.file
    # Handle raw file-like objects (e.g., BytesIO)
    else:
        if object_name is None:
            raise ValueError("object_name must be provided for raw file-like objects")
        fileobj_to_upload = file

    try:
        # Ensure the file object is at the beginning
        fileobj_to_upload.seek(0)
        # Upload file (ACL disabled on bucket, so we'll use proxy endpoint for access)
        s3_client.upload_fileobj(fileobj_to_upload, S3_BUCKET_NAME, object_name)
        # Return URL that will use proxy endpoint
        return f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{object_name}"
    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not available")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {error_code} - {error_message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {str(e)}")

def delete_file_from_s3(object_name):
    """
    Deletes a file from S3.

    :param object_name: The name/key of the object in S3 to delete.
    """
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=object_name)
    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete from S3: {e}")

def get_file_from_s3(object_name):
    """
    Downloads a file from S3 and returns the file-like object (stream).
    :param object_name: The name of the object in S3.
    :return: Streaming body of the file.
    """
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=object_name)
        return response["Body"]
    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not available")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        if error_code == 'NoSuchKey':
            raise HTTPException(status_code=404, detail="File not found in S3")
        raise HTTPException(status_code=500, detail=f"Failed to fetch from S3: {error_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch from S3: {str(e)}")

def get_presigned_url(object_name, expiration=3600):
    """
    Generates a presigned URL for accessing an S3 object.
    :param object_name: The name/key of the object in S3.
    :param expiration: Time in seconds for the presigned URL to remain valid (default: 1 hour).
    :return: Presigned URL string.
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': object_name},
            ExpiresIn=expiration
        )
        return url
    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {str(e)}")

