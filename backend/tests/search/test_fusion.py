from app.domains.search.fusion import reciprocal_rank_fusion


def test_items_ranked_well_in_both_lists_come_before_those_found_by_one_list():
    keyword = [10, 20, 30]
    vector = [20, 10, 40]

    fused = [item for item, _ in reciprocal_rank_fusion([keyword, vector])]

    # 10 et 20 sont bien classés dans les deux listes (même score) : ils précèdent 30 et 40
    assert fused[:2] == [10, 20]
    assert set(fused[2:]) == {30, 40}


def test_an_item_found_by_only_one_list_is_still_returned():
    fused = reciprocal_rank_fusion([[1, 2], [3]])

    assert {item for item, _ in fused} == {1, 2, 3}


def test_the_score_follows_the_formula_one_over_k_plus_rank():
    fused = dict(reciprocal_rank_fusion([[7]], k=60))

    assert fused[7] == 1 / 61  # rang 1 : 1 / (60 + 1)


def test_ties_are_broken_by_item_for_a_reproducible_order():
    fused = reciprocal_rank_fusion([[2], [1]])

    assert [item for item, _ in fused] == [1, 2]


def test_no_rankings_gives_an_empty_result():
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []
