"""AWS S3 service for document storage with presigned URLs."""
import uuid
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("s3_service")


class S3Service:
    """AWS S3 service for document storage with local fallback."""
    
    def __init__(self):
        self.use_local_storage = False
        self.local_storage_path = Path("./uploads")
        self.client = None
        
        # Check if AWS credentials are configured
        if (not settings.AWS_ACCESS_KEY_ID or 
            settings.AWS_ACCESS_KEY_ID == "your-access-key-id" or
            not settings.AWS_SECRET_ACCESS_KEY or
            settings.AWS_SECRET_ACCESS_KEY == "your-secret-access-key"):
            logger.warning("AWS credentials not configured, using local storage fallback")
            self.use_local_storage = True
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
        else:
            try:
                self.config = Config(
                    region_name=settings.S3_REGION,
                    signature_version='s3v4'
                )
                
                self.client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    config=self.config
                )
                logger.info("S3 client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}, using local storage")
                self.use_local_storage = True
                self.local_storage_path.mkdir(parents=True, exist_ok=True)
        
        self.bucket_name = settings.S3_BUCKET_NAME
        self.presigned_url_expiry = settings.S3_PRESIGNED_URL_EXPIRY
    
    def _generate_key(self, filename: str, user_id: str) -> str:
        """Generate a unique S3 key for a file."""
        ext = Path(filename).suffix
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        unique_id = str(uuid.uuid4())
        return f"documents/{user_id}/{date_prefix}/{unique_id}{ext}"
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        content_type: str
    ) -> Tuple[str, str]:
        """
        Upload a file to S3 or local storage.
        
        Args:
            file_content: File bytes
            filename: Original filename
            user_id: User ID for organization
            content_type: MIME type
            
        Returns:
            Tuple of (s3_key, s3_url)
        """
        s3_key = self._generate_key(filename, user_id)
        
        # Use local storage if configured or as fallback
        if self.use_local_storage:
            return await self._upload_local(file_content, s3_key, filename, user_id)
        
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'user_id': user_id,
                    'uploaded_at': datetime.utcnow().isoformat()
                }
            )
            
            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(
                "file_uploaded",
                s3_key=s3_key,
                bucket=self.bucket_name,
                size=len(file_content)
            )
            
            return s3_key, s3_url
            
        except (ClientError, NoCredentialsError) as e:
            logger.warning(f"S3 upload failed: {e}, falling back to local storage")
            self.use_local_storage = True
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
            return await self._upload_local(file_content, s3_key, filename, user_id)
    
    async def _upload_local(
        self,
        file_content: bytes,
        s3_key: str,
        filename: str,
        user_id: str
    ) -> Tuple[str, str]:
        """Upload file to local storage (fallback for testing)."""
        local_path = self.local_storage_path / s3_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(local_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(
            "file_uploaded_local",
            path=str(local_path),
            size=len(file_content)
        )
        
        return s3_key, f"local://{local_path}"
    
    def get_presigned_url(
        self,
        s3_key: str,
        expiration: Optional[int] = None,
        for_download: bool = True
    ) -> str:
        """
        Generate a presigned URL for file access.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration in seconds
            for_download: If True, sets content-disposition for download
            
        Returns:
            Presigned URL string
        """
        # For local storage, return a local file URL
        if self.use_local_storage:
            local_path = self.local_storage_path / s3_key
            return f"file://{local_path.absolute()}"
        
        expiration = expiration or self.presigned_url_expiry
        
        params = {
            'Bucket': self.bucket_name,
            'Key': s3_key,
        }
        
        if for_download:
            # Extract filename from key
            filename = Path(s3_key).name
            params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def get_presigned_upload_url(
        self,
        filename: str,
        user_id: str,
        content_type: str,
        expiration: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Generate a presigned URL for direct upload.
        
        Args:
            filename: Original filename
            user_id: User ID
            content_type: MIME type
            expiration: URL expiration in seconds
            
        Returns:
            Tuple of (presigned_url, s3_key)
        """
        expiration = expiration or self.presigned_url_expiry
        s3_key = self._generate_key(filename, user_id)
        
        try:
            url = self.client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                    'ContentType': content_type
                },
                ExpiresIn=expiration
            )
            return url, s3_key
        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL: {e}")
            raise
    
    async def download_file(self, s3_key: str) -> bytes:
        """
        Download a file from S3 or local storage.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            File content as bytes
        """
        # For local storage
        if self.use_local_storage:
            local_path = self.local_storage_path / s3_key
            if local_path.exists():
                with open(local_path, 'rb') as f:
                    return f.read()
            raise FileNotFoundError(f"File not found: {s3_key}")
        
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            raise
    
    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if successful
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info("file_deleted", s3_key=s3_key)
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            raise
    
    async def file_exists(self, s3_key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    async def ensure_bucket_exists(self) -> bool:
        """Ensure the S3 bucket exists, create if not."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if settings.S3_REGION == 'us-east-1':
                        self.client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                'LocationConstraint': settings.S3_REGION
                            }
                        )
                    logger.info(f"Created S3 bucket: {self.bucket_name}")
                    return True
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            raise


# Singleton instance
s3_service = S3Service()
