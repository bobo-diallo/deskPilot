import pytest

from app.evaluation.search_metrics import first_relevant_rank, summarize_ranks


def test_the_rank_is_the_position_of_the_first_chunk_containing_the_phrase():
    chunks = ["Autre clause", "Préavis de deux mois", "Encore autre"]

    assert first_relevant_rank(chunks, "préavis de deux mois") == 2


def test_the_comparison_ignores_case_and_accents():
    assert first_relevant_rank(["PREAVIS DE DEUX MOIS"], "préavis de deux mois") == 1


def test_no_relevant_chunk_gives_no_rank():
    assert first_relevant_rank(["Autre clause"], "préavis") is None


def test_recall_at_k_is_the_share_of_questions_answered_within_k():
    summary = summarize_ranks([1, 3, None, 6], ks=(1, 3, 5))

    assert summary.recall == {1: 0.25, 3: 0.5, 5: 0.5}


def test_mrr_averages_the_inverse_of_the_rank_with_zero_for_misses():
    summary = summarize_ranks([1, 2, None, 4])

    assert summary.mrr == pytest.approx((1 + 0.5 + 0 + 0.25) / 4)


def test_an_empty_list_of_questions_is_rejected():
    with pytest.raises(ValueError):
        summarize_ranks([])
