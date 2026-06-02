"""
Оркестратор пайплайна: выполняет шаги последовательно, обновляет статус и прогресс в task_store.
"""
from typing import List
from app.services.pipeline.steps import PipelineStep
from app.services.pipeline.context import ProcessingContext
from app.core.task_store import task_store
from app.core.task_models import TaskStatus
from app.core.exceptions import StorageError


class Pipeline:
    def __init__(self, steps: List[PipelineStep]):
        self.steps = steps

    async def run(self, ctx: ProcessingContext) -> ProcessingContext:
        total_steps = len(self.steps)
        try:
            for i, step in enumerate(self.steps):
                step_name = step.__class__.__name__
                progress = int((i / total_steps) * 100)
                await task_store.update_task(
                    ctx.task_id,
                    step=step_name,
                    step_detail=f"Шаг {i+1}/{total_steps}: {step_name}",
                    progress_percent=progress
                )
                ctx = await step.execute(ctx)

            # Финальный прогресс 100% после всех шагов
            await task_store.update_task(
                ctx.task_id,
                progress_percent=100,
                step="completed",
                step_detail="Все шаги пайплайна выполнены"
            )
            return ctx

        except StorageError as e:
            await task_store.update_task(
                ctx.task_id,
                status=TaskStatus.FAILED,
                error={"code": "STORAGE_ERROR", "message": str(e)}
            )
            raise
        except Exception as e:
            await task_store.update_task(
                ctx.task_id,
                status=TaskStatus.FAILED,
                error={"code": "PARSER_FAILED", "message": str(e)}
            )
            raise