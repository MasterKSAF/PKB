"""
Асинхронный клиент MinIO на базе aiobotocore.

Предоставляет методы для скачивания файлов из основного бакета,
загрузки изображений в отдельный бакет и генерации временных ссылок.
"""
import io
import uuid
from contextlib import asynccontextmanager
from typing import BinaryIO
import aiobotocore.session
from app.config import settings
from app.core.exceptions import StorageError


class MinIOClient:
    """
    Клиент для работы с S3-совместимым хранилищем (MinIO).

    Использует два бакета:
    - `bucket` – для хранения исходных документов
    - `image_bucket` – для хранения извлечённых изображений
    """

    def __init__(self):
        self.endpoint = settings.minio_endpoint
        self.access_key = settings.minio_access_key
        self.secret_key = settings.minio_secret_key
        self.secure = settings.minio_secure
        self.bucket = settings.minio_bucket
        self.image_bucket = settings.minio_image_bucket
        self._session = aiobotocore.session.get_session()

    @asynccontextmanager
    async def _client(self):
        """
        Контекстный менеджер для создания S3-клиента.
        Автоматически закрывает соединение.
        """
        async with self._session.create_client(
            's3',
            endpoint_url=f"http{'s' if self.secure else ''}://{self.endpoint}",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            use_ssl=self.secure
        ) as client:
            yield client

    async def download_file(self, file_key: str) -> bytes:
        """
        Скачивает файл из основного бакета.

        :param file_key: ключ (путь) файла в MinIO
        :return: содержимое файла в виде байтов
        :raises StorageError: при любой ошибке доступа
        """
        try:
            async with self._client() as client:
                resp = await client.get_object(Bucket=self.bucket, Key=file_key)
                async with resp['Body'] as stream:
                    data = await stream.read()
                return data
        except Exception as e:
            raise StorageError(f"download {file_key}") from e

    async def upload_image(self, image_data: bytes, task_id: int, page_num: int, ext: str = ".png") -> str:
        """
        Загружает изображение в бакет для образов.

        :param image_data: байты изображения
        :param task_id: ID задачи (используется для формирования пути)
        :param page_num: номер страницы
        :param ext: расширение файла (например, ".png")
        :return: ключ (путь) загруженного изображения в MinIO
        :raises StorageError: при ошибке загрузки
        """
        key = f"task_{task_id}/page_{page_num}_{uuid.uuid4().hex}{ext}"
        try:
            async with self._client() as client:
                await client.put_object(
                    Bucket=self.image_bucket,
                    Key=key,
                    Body=io.BytesIO(image_data),
                    ContentType="image/png"
                )
            return key
        except Exception as e:
            raise StorageError(f"upload image {key}") from e

    async def get_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        Генерирует временную ссылку на файл в основном бакете.

        :param file_key: ключ файла
        :param expires_in: время жизни ссылки в секундах (по умолчанию 1 час)
        :return: подписанный URL
        """
        async with self._client() as client:
            url = await client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': file_key},
                ExpiresIn=expires_in
            )
            return url


# Глобальный экземпляр клиента
minio_client = MinIOClient()