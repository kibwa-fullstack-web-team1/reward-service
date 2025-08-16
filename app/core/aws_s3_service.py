import boto3
from botocore.exceptions import ClientError
import logging
from typing import Optional, List
from app.config.config import Config

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
        self.bucket_name = Config.S3_BUCKET_NAME

    def upload_file(self, file_content: bytes, object_name: str, content_type: str) -> Optional[str]:
        """
        S3 버킷에 파일을 업로드하고 URL을 반환합니다.
        :param file_content: 업로드할 파일의 바이너리 내용
        :param object_name: S3에 저장될 객체 이름 (경로 포함)
        :param content_type: 파일의 Content-Type (예: 'image/png')
        :return: 업로드된 파일의 S3 URL 또는 None
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_content,
                ContentType=content_type
            )
            file_url = f"https://{self.bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/{object_name}"
            logger.info(f"File uploaded successfully to {file_url}")
            return file_url
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during S3 upload: {e}")
            return None

    def delete_file(self, object_name: str) -> bool:
        """
        S3 버킷에서 특정 객체를 삭제합니다.
        :param object_name: 삭제할 객체의 이름 (경로 포함)
        :return: 삭제 성공 시 True, 실패 시 False
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(f"File {object_name} deleted successfully from S3.")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file {object_name} from S3: {e}")
            return False

    def delete_files(self, object_names: List[str]) -> bool:
        """
        S3 버킷에서 여러 객체를 한 번에 삭제합니다.
        :param object_names: 삭제할 객체 이름의 리스트
        :return: 삭제 성공 시 True, 실패 시 False
        """
        if not object_names:
            return True
        
        delete_keys = {'Objects': [{'Key': name} for name in object_names]}
        try:
            self.s3_client.delete_objects(Bucket=self.bucket_name, Delete=delete_keys)
            logger.info(f"Successfully deleted {len(object_names)} files from S3.")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete files from S3: {e}")
            return False