from google.cloud import storage
from google.cloud.storage import Bucket, Blob
from google.oauth2 import service_account

from src.defaults import DEFAULT_ENV_FILE
from src.utils.dotenv_utils import FromFileConfigGenerator, load_config
from src.utils.gcs_utils import GCSClientGenerator, GCSConfig

BUCKET_NAME = 'bucket-optimusprime'


configs_getter = FromFileConfigGenerator(DEFAULT_ENV_FILE)
gcs_config = load_config(GCSConfig, configs_getter.get_config)
client_generator = GCSClientGenerator(gcs_config)
storage_client = client_generator.get_client()

bucket = storage_client.get_bucket(BUCKET_NAME)

# Note: Client.list_blobs requires at least package version 1.17.0.
blobs = storage_client.list_blobs(BUCKET_NAME)

def download_blob(bucket: Bucket, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # source_blob_name = "storage-object-name"

    # The path to which the file should be downloaded
    # destination_file_name = "local/path/to/file"

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(
        "Downloaded storage object {} from bucket {} to local file {}.".format(
            source_blob_name, bucket.name, destination_file_name
        )
    )

download_blob(bucket, 'datacore/1zxiD2kQoahdYQpSJ1xcNyC0PYky4-B-E_JjBdDUfTGw', 'test.pdf')

blob = bucket.get_blob("datacore/1zxiD2kQoahdYQpSJ1xcNyC0PYky4-B-E_JjBdDUfTGw")

total = len([blob for blob in blobs if blob == blob])
print(total)