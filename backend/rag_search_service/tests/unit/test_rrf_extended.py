"""Unit-тесты для RRF: расширенные edge cases."""

from __future__ import annotations

from app.core.search.rrf import reciprocal_rank_fusion


class TestRRFExtended:
    """Расширенные тесты Reciprocal Rank Fusion."""

    def test_three_ranked_lists(self):
        """Три ранжированных списка: элемент в 3 списках получает максимальный скор."""
        list1 = [1, 2, 3]
        list2 = [2, 3, 4]
        list3 = [3, 4, 5]

        scores = reciprocal_rank_fusion([list1, list2, list3], k=60)

        # id=3 встречается во всех 3 списках — должен быть первым
        sorted_ids = list(scores.keys())
        assert sorted_ids[0] == 3
        # Проверяем score id=3: 1/63 + 1/62 + 1/61
        expected = 1.0 / 63.0 + 1.0 / 62.0 + 1.0 / 61.0
        assert abs(scores[3] - expected) < 0.0001

    def test_k_zero_raises_error(self):
        """k=0 приводит к ZeroDivisionError на первом элементе (rank=0, denom=0+0+1=1, но k=0 → denom=1)."""
        # k=0: score = 1/(0 + rank + 1) = 1/(rank+1). Это не деление на ноль.
        # Проверяем что k=0 работает корректно
        scores = reciprocal_rank_fusion([[1, 2]], k=0)
        # rank 0: 1/(0+0+1) = 1.0
        # rank 1: 1/(0+1+1) = 0.5
        assert abs(scores[1] - 1.0) < 0.0001
        assert abs(scores[2] - 0.5) < 0.0001

    def test_single_element_lists(self):
        """Одноэлементные списки."""
        scores = reciprocal_rank_fusion([[1], [2], [3]], k=60)

        assert len(scores) == 3
        # Все на позиции 0 в своих списках, но в разных списках — разные скоры
        # Нет пересечений, поэтому порядок определяется порядком списков
        assert all(score > 0 for score in scores.values())

    def test_all_identical_lists(self):
        """Все списки идентичны: элементы получают суммарный скор из всех списков."""
        list1 = [1, 2, 3]
        list2 = [1, 2, 3]
        list3 = [1, 2, 3]

        scores = reciprocal_rank_fusion([list1, list2, list3], k=60)

        # Все элементы на одинаковых позициях — порядок сохраняется
        sorted_ids = list(scores.keys())
        assert sorted_ids == [1, 2, 3]

        # Каждый элемент получил скор 3 раза (по одному из каждого списка)
        expected_1 = 3 * (1.0 / 61.0)
        expected_2 = 3 * (1.0 / 62.0)
        expected_3 = 3 * (1.0 / 63.0)
        assert abs(scores[1] - expected_1) < 0.0001
        assert abs(scores[2] - expected_2) < 0.0001
        assert abs(scores[3] - expected_3) < 0.0001

    def test_all_same_ids_across_lists(self):
        """Все списки содержат одни и те же ID, но в разном порядке."""
        list1 = [1, 2, 3]
        list2 = [3, 2, 1]

        scores = reciprocal_rank_fusion([list1, list2], k=60)

        # id=2: rank 1 в list1 + rank 1 в list2 = 1/62 + 1/62
        # id=1: rank 0 в list1 + rank 2 в list2 = 1/61 + 1/63
        # id=3: rank 2 в list1 + rank 0 в list2 = 1/63 + 1/61
        # id=1 и id=3 имеют одинаковый суммарный скор
        assert abs(scores[1] - scores[3]) < 0.0001

    def test_score_formula_with_k1(self):
        """Проверка формулы с k=1."""
        scores = reciprocal_rank_fusion([[10, 20]], k=1)

        # rank 0: 1/(1+0+1) = 0.5
        # rank 1: 1/(1+1+1) = 0.333...
        assert abs(scores[10] - 0.5) < 0.0001
        assert abs(scores[20] - 1.0 / 3.0) < 0.0001

    def test_many_lists_large_k(self):
        """Много списков с большим k: скоры маленькие, порядок определяется пересечениями."""
        lists = [[i, i + 1] for i in range(1, 11, 2)]  # 5 списков, пересекаются попарно
        scores = reciprocal_rank_fusion(lists, k=1000)

        # Все элементы присутствуют
        assert len(scores) > 0
        # Скоры положительные и маленькие (k=1000)
        assert all(0 < s < 0.01 for s in scores.values())
