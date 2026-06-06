"""
TaskResultCache – опциональный компонент для хранения больших результатов отдельно.

В текущей реализации (in-memory) все результаты хранятся непосредственно в TaskInfo.
Этот класс оставлен как заглушка для возможного будущего перехода на Redis или файловое кеширование.
"""
from typing import Optional, Any


class TaskResultCache:
    """Заглушка – методы ничего не делают."""

    async def get(self, task_id: int) -> Optional[Any]:
        """В реальной реализации мог бы получать результат из внешнего хранилища."""
        return None

    async def set(self, task_id: int, result: Any) -> None:
        """Сохранить результат во внешнее хранилище."""
        pass

    async def delete(self, task_id: int) -> None:
        """Удалить результат."""
        pass