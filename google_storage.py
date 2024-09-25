from google.cloud import storage
import os

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """
    Uploads a file to the Google Cloud Storage bucket.

    :param bucket_name: Name of your GCS bucket
    :param source_file_name: Path to the file to be uploaded
    :param destination_blob_name: Name for the uploaded file in GCS
    """
    # Initialize a GCS client
    storage_client = storage.Client()

    # Get the bucket object
    bucket = storage_client.bucket(bucket_name)

    # Create a new blob object in the bucket
    blob = bucket.blob(destination_blob_name)

    # Upload the file to the blob
    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name} in bucket {bucket_name}.")

# make sure that the GOOGLE_APPLICATION_CREDENTIALS environment variable is set
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
print (GOOGLE_APPLICATION_CREDENTIALS)

# Example usage:
bucket_name = "q-view"
source_file_name = "requirements.txt"
destination_blob_name = "requirements.txt"

upload_to_gcs(bucket_name, source_file_name, destination_blob_name)