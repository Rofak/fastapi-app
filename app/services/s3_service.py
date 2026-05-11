import aioboto3
from app.schemas.video_dubber_ai import S3UploadResponse
from app.core.config import settings


class S3Service:
    def __init__(self):
        self.session = aioboto3.Session()
        self.session = aioboto3.Session()
        self.bucket = settings.S3_BUCKET_NAME
        self.endpoint = settings.S3_ENDPOINT
        self.access_key = settings.S3_ACCESS_KEY_ID
        self.secret_key = settings.S3_SECRET_ACCESS_KEY
        self.base_url = settings.S3_BASE_URL

    async def upload_file_to_s3(self, file_path: str, filename: str, member_id: str):
        key = f"member_{member_id}/{filename}"
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="SIN"
        ) as s3:

            with open(file_path, "rb") as f:
                await s3.upload_fileobj(f, self.bucket, key, ExtraArgs={
                    "ContentType": "video/mp4",
                    "ContentDisposition": f'attachment; filename="{filename}"'
                })
        video_url = f"{self.base_url}:{self.bucket}/{key}"
        path = key
        return S3UploadResponse(video_url=video_url, path=path)
