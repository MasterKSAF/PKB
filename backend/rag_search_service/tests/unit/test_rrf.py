"""Unit-тесты для алгоритма Reciprocal Rank Fusion (RRF)."""


from app.core.search.rrf import reciprocal_rank_fusion


class TestReciprocalRankFusion:
    """Тесты алгоритма RRF."""

    def test_single_list(self):
        """Один список: скоры вычисляются корректно."""
        id1 = 101
        id2 = 102
        id3 = 103

        ranked_list = [id1, id2, id3]
        scores = reciprocal_rank_fusion([ranked_list], k=60)

        # Проверяем, что все ID присутствуют
        assert len(scores) == 3
        assert id1 in scores
        assert id2 in scores
        assert id3 in scores

        # Проверяем порядок (первый элемент имеет наибольший скор)
        assert scores[id1] > scores[id2] > scores[id3]

        # Проверяем конкретные значения
        # rank 0: 1 / (60 + 0 + 1) = 1/61 ≈ 0.01639
        assert abs(scores[id1] - (1.0 / 61.0)) < 0.0001
        # rank 1: 1 / (60 + 1 + 1) = 1/62 ≈ 0.01613
        assert abs(scores[id2] - (1.0 / 62.0)) < 0.0001
        # rank 2: 1 / (60 + 2 + 1) = 1/63 ≈ 0.01587
        assert abs(scores[id3] - (1.0 / 63.0)) < 0.0001

    def test_two_lists_with_overlap(self):
        """Два списка с пересечением: элементы в обоих списках получают больший скор."""
        id1 = 101
        id2 = 102
        id3 = 103
        id4 = 104

        list1 = [id1, id2, id3]  # id2 на позиции 1
        list2 = [id2, id3, id4]  # id2 на позиции 0

        scores = reciprocal_rank_fusion([list1, list2], k=60)

        # id2 должен быть первым (присутствует в обоих списках на высоких позициях)
        sorted_ids = list(scores.keys())
        assert sorted_ids[0] == id2

        # Проверяем скор id2: 1/(60+1+1) + 1/(60+0+1) = 1/62 + 1/61
        expected_id2_score = (1.0 / 62.0) + (1.0 / 61.0)
        assert abs(scores[id2] - expected_id2_score) < 0.0001

    def test_empty_lists(self):
        """Пустые списки возвращают пустой результат."""
        scores = reciprocal_rank_fusion([], k=60)
        assert scores == {}

        scores = reciprocal_rank_fusion([[], []], k=60)
        assert scores == {}

    def test_k_parameter_affects_scores(self):
        """Параметр k влияет на значения скоров."""
        id1 = 101
        ranked_list = [id1]

        scores_k60 = reciprocal_rank_fusion([ranked_list], k=60)
        scores_k100 = reciprocal_rank_fusion([ranked_list], k=100)

        # При большем k скоры меньше
        assert scores_k60[id1] > scores_k100[id1]

        # Проверяем конкретные значения
        assert abs(scores_k60[id1] - (1.0 / 61.0)) < 0.0001
        assert abs(scores_k100[id1] - (1.0 / 101.0)) < 0.0001

    def test_disjoint_lists(self):
        """Два непересекающихся списка: все элементы присутствуют."""
        id1 = 101
        id2 = 102
        id3 = 103
        id4 = 104

        list1 = [id1, id2]
        list2 = [id3, id4]

        scores = reciprocal_rank_fusion([list1, list2], k=60)

        # Все 4 ID должны присутствовать
        assert len(scores) == 4
        assert id1 in scores
        assert id2 in scores
        assert id3 in scores
        assert id4 in scores

    def test_result_is_sorted_by_score(self):
        """Результат отсортирован по убыванию скора."""
        id1 = 101
        id2 = 102
        id3 = 103

        list1 = [id1, id2, id3]
        list2 = [id3, id2, id1]

        scores = reciprocal_rank_fusion([list1, list2], k=60)

        # Проверяем, что скоры убывают
        score_values = list(scores.values())
        for i in range(len(score_values) - 1):
            assert score_values[i] >= score_values[i + 1]

    def test_duplicate_in_same_list(self):
        """Дубликаты в одном списке: учитывается только первое вхождение."""
        id1 = 101
        id2 = 102

        # id1 встречается дважды на позициях 0 и 2
        ranked_list = [id1, id2, id1]

        scores = reciprocal_rank_fusion([ranked_list], k=60)

        # id1 должен получить скор только за позицию 0 (первое вхождение)
        # id2 должен получить скор за позицию 1
        assert len(scores) == 2
        assert scores[id1] > scores[id2]
        assert abs(scores[id1] - (1.0 / 61.0)) < 0.0001
        assert abs(scores[id2] - (1.0 / 62.0)) < 0.0001