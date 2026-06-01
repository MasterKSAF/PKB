"""Алгоритм Reciprocal Rank Fusion (RRF) для объединения ранжированных списков."""

from __future__ import annotations


def reciprocal_rank_fusion(
    ranked_lists: list[list[int]],
    k: int = 60,
) -> dict[int, float]:
    """
    Объединить несколько ранжированных списков в единый скор с помощью RRF.

    Формула: score(d) = Σ 1 / (k + rank_i(d))
    где k — константа (обычно 60), rank_i(d) — позиция элемента в i-м списке (нумерация с 0).

    Если элемент встречается несколько раз в ОДНОМ списке, учитывается только
    первое (наилучшее) вхождение. Это защищает от искусственного завышения скора
    из-за дубликатов в выдаче БД.

    Args:
        ranked_lists: Список ранжированных списков ID чанков.
        k: Константа RRF (по умолчанию 60).

    Returns:
        Словарь {chunk_id: rrf_score}, отсортированный по убыванию скора.
    """
    scores: dict[int, float] = {}

    for ranked_list in ranked_lists:
        # Отслеживаем уже учтённые ID в пределах ТЕКУЩЕГО списка
        # Это предотвращает суммирование скоров за дубликаты внутри одного списка
        seen_in_this_list: set[int] = set()

        for rank, chunk_id in enumerate(ranked_list):
            if chunk_id in seen_in_this_list:
                continue  # Пропускаем дубликат

            seen_in_this_list.add(chunk_id)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)

    # Сортируем по убыванию скора
    sorted_scores = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))

    return sorted_scores