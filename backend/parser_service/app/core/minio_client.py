import io
from contextlib import asynccontextmanager
import aiobotocore.session
from botocore.config import Config
from botocore.exceptions import ClientError
from app.config import settings
from app.core.exceptions import StorageError, FileNotFoundError
import logging

logger = logging.getLogger(__name__)


class MinIOClient:
    """
    Асинхронный клиент для работы с MinIO (S3-совместимое хранилище).

    Предоставляет методы скачивания файлов, загрузки изображений и генерации presigned URL.
    При первом обращении к бакету проверяет его существование и создаёт при необходимости.
    """

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
            region_name="us-east-1"
        )
        logger.debug(f"MinIO client initialized ")

    async def _ensure_bucket(self, bucket_name: str):
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
                logger.debug(f"Bucket {bucket_name} exists")
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                if error_code == 'NoSuchBucket':
                    logger.info(f"Bucket {bucket_name} not found, creating...")
                    await client.create_bucket(Bucket=bucket_name)
                    logger.info(f"Bucket {bucket_name} created")
                else:
                    logger.error(f"Error checking bucket {bucket_name}: {e}", exc_info=True)
                    raise StorageError(f"check bucket {bucket_name}") from e
            except Exception as e:
                logger.error(f"Unexpected error checking bucket {bucket_name}: {e}", exc_info=True)
                raise StorageError(f"check bucket {bucket_name}") from e

    @asynccontextmanager
    async def _client(self):
        """
        Контекстный менеджер, возвращающий клиента aiobotocore для S3.
        """
        async with self._session.create_client(
            's3',
            endpoint_url=f"http{'s' if self.secure else ''}://{self.endpoint}",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            use_ssl=self.secure,
            config=self._client_config
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
        logger.debug(f"Downloading {file_key} from bucket {self.bucket}")
        try:
            async with self._client() as client:
                resp = await client.get_object(Bucket=self.bucket, Key=file_key)
                async with resp['Body'] as stream:
                    data = await stream.read()
                logger.info(f"Downloaded {file_key}, size={len(data)} bytes")
                return data
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'NoSuchKey':
                logger.error(f"File {file_key} not found in MinIO", exc_info=True)
                raise FileNotFoundError(file_key) from e
            logger.error(f"ClientError downloading {file_key}: {e}", exc_info=True)
            raise StorageError(f"download {file_key}") from e
        except Exception as e:
            if "not found" in str(e).lower():
                # Некоторые ошибки сетевого уровня могут содержать "not found"
                raise FileNotFoundError(file_key) from e
            logger.error(f"Failed to download {file_key}: {e}", exc_info=True)
            raise StorageError(f"download {file_key}") from e

    async def upload_image(self, image_data: bytes, task_id: int, page_num: int, ext: str = ".png", custom_key: str = None) -> str:
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
        key = custom_key if custom_key else f"task_{task_id}/page_{page_num}_{task_id}_{page_num}_{abs(hash(image_data))}{ext}"
        await self._ensure_bucket(self.image_bucket)
        try:
            async with self._client() as client:
                await client.put_object(
                    Bucket=self.image_bucket,
                    Key=key,
                    Body=io.BytesIO(image_data),
                    ContentType="image/png"
                )
            logger.info(f"Image uploaded to {self.image_bucket}/{key}, size={len(image_data)} bytes")
            return key
        except Exception as e:
            logger.error(f"Failed to upload image {key}: {e}", exc_info=True)
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
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': file_key},
                    ExpiresIn=expires_in
                )
                logger.debug(f"Presigned URL generated for {file_key}")
                return url
            except Exception as e:
                logger.error(f"Failed to generate presigned URL for {file_key}: {e}", exc_info=True)
                raise StorageError(f"generate presigned URL for {file_key}") from e


# Глобальный экземпляр клиента
minio_client = MinIOClient()