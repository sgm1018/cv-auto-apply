"""S3-compatible object storage client."""
import aioboto3

from cvapplier.core.config import get_settings
from cvapplier.core.logging import get_logger

log = get_logger(__name__)


class ObjectStorage:
    def __init__(self) -> None:
        s = get_settings()
        self._endpoint = s.s3_endpoint_url
        self._region = s.s3_region
        self._access_key = s.s3_access_key
        self._secret_key = s.s3_secret_key
        self.bucket = s.s3_bucket
        self._use_ssl = s.s3_use_ssl
        self._session = aioboto3.Session()

    def client(self):
        return self._session.client(
            "s3",
            endpoint_url=self._endpoint,
            region_name=self._region,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            use_ssl=self._use_ssl,
        )

    async def check_connection(self) -> bool:
        async with self.client() as s3:
            try:
                buckets = await s3.list_buckets()
                bucket_names = [b["Name"] for b in buckets.get("Buckets", [])]
                log.info("minio_connected", buckets=bucket_names, endpoint=self._endpoint)
                if self.bucket not in bucket_names:
                    await s3.create_bucket(Bucket=self.bucket)
                    log.info("minio_bucket_created", bucket=self.bucket)
                else:
                    log.info("minio_bucket_exists", bucket=self.bucket)
                return True
            except Exception as e:
                log.warning("minio_connection_failed", error=str(e), endpoint=self._endpoint)
                return False

    def build_key(self, *, user_id: str, file_id: str, suffix: str) -> str:
        return f"cvs/{user_id}/{file_id}{suffix}"

    async def put_bytes(self, *, key: str, data: bytes, content_type: str) -> None:
        async with self.client() as s3:
            await s3.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    async def get_bytes(self, *, key: str) -> bytes:
        async with self.client() as s3:
            obj = await s3.get_object(Bucket=self.bucket, Key=key)
            return await obj["Body"].read()

    async def delete(self, *, key: str) -> None:
        async with self.client() as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)
