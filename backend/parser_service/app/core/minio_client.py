"""
Асинхронный клиент для работы с MinIO (S3-совместимое хранилище).

Предоставляет методы скачивания файлов, загрузки изображений и генерации presigned URL.
При первом обращении к бакету проверяет его существование и создаёт при необходимости.
"""

import io
from contextlib import asynccontextmanager
import aiobotocore.session
from botocore.config import Config
from botocore.exceptions import ClientError
from app.config import settings
from app.core.exceptions import StorageError, FileNotFoundError
from app.core.validator import validate
import logging
import os
import asyncio

logger = logging.getLogger(__name__)


class MinIOClient:
    """Реальный клиент MinIO."""

    def __init__(self):
        self.endpoint = settings.minio_endpoint
        self.access_key = settings.minio_access_key
        self.secret_key = settings.minio_secret_key
        self.secure = settings.minio_secure
        self.bucket = settings.minio_bucket
        self.image_bucket = settings.minio_image_bucket
        self._session = aiobotocore.session.get_session()
        self._buckets_checked = False
        self._timeout = settings.minio_timeout

        self._client_config = Config(
            connect_timeout=self._timeout,
            read_timeout=self._timeout,
            max_pool_connections=10,
            region_name="us-east-1",
        )
        logger.debug("MinIO client initialized")

    async def _ensure_bucket(self, bucket_name: str) -> None:
        """
        Проверяет существование бакета, создаёт его, если отсутствует.

        Args:
            bucket_name: Имя бакета.

        Raises:
            StorageError: При ошибке доступа к MinIO.
        """
        async with self._client() as client:
            try:
                await client.head_bucket(Bucket=bucket_name)
                logger.debug("Bucket %s exists", bucket_name)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code == "NoSuchBucket":
                    logger.info("Bucket %s not found, creating...", bucket_name)
                    await client.create_bucket(Bucket=bucket_name)
                    logger.info("Bucket %s created", bucket_name)
                else:
                    logger.error(
                        "Error checking bucket %s: %s",
                        bucket_name,
                        e,
                        exc_info=True,
                    )
                    raise StorageError(f"check bucket {bucket_name}") from e
            except Exception as e:
                logger.error(
                    "Unexpected error checking bucket %s: %s",
                    bucket_name,
                    e,
                    exc_info=True,
                )
                raise StorageError(f"check bucket {bucket_name}") from e

    @asynccontextmanager
    async def _client(self):
        """
        Контекстный менеджер, возвращающий клиента aiobotocore для S3.
        """
        async with self._session.create_client(
            "s3",
            endpoint_url=f"http{'s' if self.secure else ''}://{self.endpoint}",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            use_ssl=self.secure,
            config=self._client_config,
        ) as client:
            yield client

    async def download_file(self, file_key: str) -> bytes:
        """
        Скачивает файл из основного бакета.

        Args:
            file_key: Ключ (путь) файла в бакете.

        Returns:
            Содержимое файла в байтах.

        Raises:
            FileNotFoundError: Если файл не найден.
            StorageError: При других ошибках MinIO.
        """
        logger.debug("Downloading %s from bucket %s", file_key, self.bucket)
        try:
            async with self._client() as client:
                resp = await client.get_object(Bucket=self.bucket, Key=file_key)
                async with resp["Body"] as stream:
                    data = await stream.read()
                logger.info(
                    "Downloaded %s, size=%d bytes",
                    file_key,
                    len(data),
                )
                return data
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                logger.error("File %s not found in MinIO", file_key, exc_info=True)
                raise FileNotFoundError(file_key) from e
            logger.error(
                "ClientError downloading %s: %s",
                file_key,
                e,
                exc_info=True,
            )
            raise StorageError(f"download {file_key}") from e
        except Exception as e:
            if "not found" in str(e).lower():
                logger.error("File %s not found", file_key, exc_info=True)
                raise FileNotFoundError(file_key) from e
            logger.error(
                "Failed to download %s: %s",
                file_key,
                e,
                exc_info=True,
            )
            raise StorageError(f"download {file_key}") from e

    async def download_and_validate(self, file_key: str) -> bytes:
        """
        Скачивает файл и выполняет полную валидацию (размер, MIME, безопасность).
        Возвращает содержимое файла.
        """
        from app.core.exceptions import StorageError, UnsupportedFormatError, FileTooLargeError

        logger.debug("Fetching file: %s", file_key)
        try:
            file_bytes = await self.download_file(file_key)
        except Exception as e:
            logger.error("Download failed for %s", file_key, exc_info=True)
            raise StorageError(f"download {file_key}") from e

        original_filename = os.path.basename(file_key)
        try:
            mime = await validate(file_bytes, original_filename)
            logger.debug("Validation passed for %s, MIME=%s", file_key, mime)
        except Exception as e:
            logger.error(
                "Validation failed for %s: %s",
                file_key,
                str(e),
                exc_info=True,
            )
            raise

        if mime != "application/pdf":
            logger.warning("Unsupported MIME type %s for file %s", mime, file_key)
            raise UnsupportedFormatError(mime)

        return file_bytes

    async def upload_image(
        self,
        image_data: bytes,
        task_id: int,
        page_num: int,
        ext: str = ".png",
        custom_key: str = None,
    ) -> str:
        """
        Загружает изображение в бакет для изображений.

        Args:
            image_data: Байты изображения.
            task_id: ID задачи (используется в имени ключа).
            page_num: Номер страницы.
            ext: Расширение файла (по умолчанию ".png").
            custom_key: Пользовательский ключ (если передан, используется вместо автоматического).

        Returns:
            Ключ (путь) загруженного объекта.

        Raises:
            StorageError: При ошибке загрузки.
        """
        key = (
            custom_key
            if custom_key
            else f"task_{task_id}/page_{page_num}_{task_id}_{page_num}_{abs(hash(image_data))}{ext}"
        )
        await self._ensure_bucket(self.image_bucket)
        try:
            async with self._client() as client:
                await client.put_object(
                    Bucket=self.image_bucket,
                    Key=key,
                    Body=io.BytesIO(image_data),
                    ContentType="image/png",
                )
            logger.info(
                "Image uploaded to %s/%s, size=%d bytes",
                self.image_bucket,
                key,
                len(image_data),
            )
            return key
        except Exception as e:
            logger.error(
                "Failed to upload image %s: %s",
                key,
                e,
                exc_info=True,
            )
            raise StorageError(f"upload image {key}") from e

    async def get_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        Генерирует подписанный URL для временного доступа к файлу.

        Args:
            file_key: Ключ файла в бакете.
            expires_in: Время жизни ссылки в секундах (по умолчанию 3600).

        Returns:
            Строка с presigned URL.

        Raises:
            StorageError: При ошибке генерации.
        """
        async with self._client() as client:
            try:
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": file_key},
                    ExpiresIn=expires_in,
                )
                logger.debug("Presigned URL generated for %s", file_key)
                return url
            except Exception as e:
                logger.error(
                    "Failed to generate presigned URL for %s: %s",
                    file_key,
                    e,
                    exc_info=True,
                )
                raise StorageError(f"generate presigned URL for {file_key}") from e


class MockMinIOClient:
    """Мок-клиент для тестирования и разработки без реального MinIO."""

    def __init__(self):
        self.delay = settings.mock_minio_delay
        self.mock_file_data = None
        if settings.mock_minio_file_data_path and os.path.exists(settings.mock_minio_file_data_path):
            with open(settings.mock_minio_file_data_path, "rb") as f:
                self.mock_file_data = f.read()
        else:
            # Минимальный валидный PDF-заглушка
            self.mock_file_data = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000015 00000 n\n0000000062 00000 n\n0000000115 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"
        self.uploaded_images = {}

    async def _maybe_delay(self):
        if self.delay > 0:
            await asyncio.sleep(self.delay)

    async def download_file(self, file_key: str) -> bytes:
        await self._maybe_delay()
        logger.debug("[MOCK] Downloading %s", file_key)
        if file_key == "missing.pdf":
            logger.warning("[MOCK] File not found: %s", file_key)
            raise FileNotFoundError(file_key)
        return self.mock_file_data

    async def download_and_validate(self, file_key: str) -> bytes:
        """Мок-валидация: просто возвращает данные, пропуская реальную проверку."""
        await self._maybe_delay()
        logger.debug("[MOCK] Download and validate %s", file_key)
        return await self.download_file(file_key)

    async def upload_image(
        self,
        image_data: bytes,
        task_id: int,
        page_num: int,
        ext: str = ".png",
        custom_key: str = None,
    ) -> str:
        await self._maybe_delay()
        key = (
            custom_key
            if custom_key
            else f"mock_task_{task_id}/page_{page_num}_{abs(hash(image_data))}{ext}"
        )
        self.uploaded_images[key] = image_data
        logger.debug("[MOCK] Uploaded image to %s", key)
        return key

    async def get_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        await self._maybe_delay()
        logger.debug("[MOCK] Presigned URL for %s", file_key)
        return f"http://mock-minio/presigned/{file_key}?expires={expires_in}"

    async def _ensure_bucket(self, bucket_name: str):
        logger.debug("[MOCK] Ensuring bucket %s exists", bucket_name)


# Выбор клиента на основе флага
if settings.use_mock_minio:
    minio_client = MockMinIOClient()
    logger.info("Using MockMinIOClient")
else:
    minio_client = MinIOClient()
    logger.info("Using real MinIOClient")