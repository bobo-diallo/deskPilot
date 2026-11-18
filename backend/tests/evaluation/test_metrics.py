from datetime import date
from decimal import Decimal

import pytest

from app.domains.extraction.schemas import Invoice, InvoiceLine
from app.evaluation.metrics import (
    FIELDS,
    CaseScore,
    ScoredTrial,
    paired_bootstrap,
    score_extraction,
    status_outcome,
    summarize,
    wilson_interval,
)


def make_invoice(**changes) -> Invoice:
    values = {
        "supplier_name": "Atelier Nord",
        "invoice_number": "2026-014",
        "issue_date": date(2026, 11, 12),
        "currency": "EUR",
        "lines": [
            InvoiceLine(
                description="Chaise",
                quantity=Decimal("2"),
                unit_price=Decimal("10.00"),
                total=Decimal("20.00"),
            ),
            InvoiceLine(
                description="Livraison",
                quantity=Decimal("1"),
                unit_price=Decimal("5.00"),
                total=Decimal("5.00"),
            ),
        ],
        "subtotal": Decimal("25.00"),
        "tax_amount": Decimal("5.00"),
        "total": Decimal("30.00"),
    }
    values.update(changes)
    return Invoice(**values)


def line(description="Chaise", quantity="2", unit_price="10.00", total="20.00") -> InvoiceLine:
    return InvoiceLine(
        description=description,
        quantity=Decimal(quantity),
        unit_price=Decimal(unit_price),
        total=Decimal(total),
    )


def wrong_fields(score: CaseScore) -> set[str]:
    return {name for name, ok in score.fields.items() if not ok}


# --- comparaison champ par champ -------------------------------------------------------------


def test_an_identical_extraction_is_perfect():
    score = score_extraction(make_invoice(), make_invoice(), status="validated")

    assert set(score.fields) == set(FIELDS)
    assert score.perfect
    assert score.hallucinations == 0
    assert not score.failed


def test_text_comparison_ignores_case_and_extra_spaces():
    extracted = make_invoice(supplier_name="  ATELIER   nord ")

    assert score_extraction(make_invoice(), extracted, "validated").perfect


def test_amounts_are_compared_by_value_not_by_text():
    extracted = make_invoice(total=Decimal("30"), subtotal=Decimal("25.0"))

    assert score_extraction(make_invoice(), extracted, "validated").perfect


def test_a_one_cent_error_on_a_total_is_wrong():
    extracted = make_invoice(total=Decimal("30.01"))

    score = score_extraction(make_invoice(), extracted, "needs_review")

    assert wrong_fields(score) == {"total"}


def test_a_wrong_date_only_breaks_the_date_field():
    extracted = make_invoice(issue_date=date(2026, 12, 11))

    assert wrong_fields(score_extraction(make_invoice(), extracted, "validated")) == {"issue_date"}


def test_inventing_a_value_for_an_absent_field_is_counted_as_a_hallucination():
    expected = make_invoice(invoice_number=None)
    extracted = make_invoice(invoice_number="2026-014")

    score = score_extraction(expected, extracted, "validated")

    assert wrong_fields(score) == {"invoice_number"}
    assert score.hallucinations == 1


def test_correctly_leaving_an_absent_field_empty_is_right():
    expected = make_invoice(invoice_number=None)
    extracted = make_invoice(invoice_number=None)

    score = score_extraction(expected, extracted, "needs_review")

    assert score.perfect
    assert score.hallucinations == 0


def test_a_wrong_quantity_breaks_line_amounts_but_not_descriptions():
    lines = [line(quantity="3"), line("Livraison", "1", "5.00", "5.00")]
    extracted = make_invoice(lines=lines)

    score = score_extraction(make_invoice(), extracted, "needs_review")

    assert wrong_fields(score) == {"line_amounts"}


def test_a_different_number_of_lines_breaks_every_line_field():
    extracted = make_invoice(lines=[line()])

    score = score_extraction(make_invoice(), extracted, "needs_review")

    assert wrong_fields(score) == {"line_count", "line_amounts", "line_descriptions"}


def test_a_failed_extraction_scores_zero_everywhere():
    score = score_extraction(make_invoice(), None, status=None)

    assert score.failed
    assert not score.perfect
    assert wrong_fields(score) == set(FIELDS)


# --- fiabilité du statut ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("perfect", "status", "outcome"),
    [
        (True, "validated", "true_accept"),
        (False, "validated", "false_accept"),  # l'erreur silencieuse : la plus dangereuse
        (True, "needs_review", "false_alarm"),
        (False, "needs_review", "caught"),
    ],
)
def test_status_outcome_classifies_the_four_cases(perfect, status, outcome):
    expected = make_invoice()
    extracted = make_invoice() if perfect else make_invoice(issue_date=date(2026, 1, 1))

    assert status_outcome(score_extraction(expected, extracted, status)) == outcome


# --- statistiques ----------------------------------------------------------------------------


def test_wilson_interval_matches_a_known_value():
    low, high = wilson_interval(successes=8, trials=10)

    assert low == pytest.approx(0.490, abs=0.005)
    assert high == pytest.approx(0.943, abs=0.005)


def test_wilson_interval_without_trials_is_uninformative():
    assert wilson_interval(0, 0) == (0.0, 1.0)


def _trial(case_id, tags, extracted, status="validated"):
    return ScoredTrial(case_id, tuple(tags), score_extraction(make_invoice(), extracted, status))


def test_summary_aggregates_accuracy_by_field_and_by_tag():
    trials = [
        _trial("a", ["digital"], make_invoice()),
        _trial("b", ["digital"], make_invoice(total=Decimal("99"))),
        _trial("c", ["scan"], make_invoice()),
        _trial("d", ["scan"], make_invoice(total=Decimal("99")), status="needs_review"),
    ]

    summary = summarize(trials)

    assert summary.trials == 4
    assert summary.perfect_rate == pytest.approx(0.5)
    assert summary.field_accuracy["total"] == pytest.approx(0.5)
    assert summary.field_accuracy["supplier_name"] == pytest.approx(1.0)
    assert summary.perfect_rate_by_tag == {"digital": 0.5, "scan": 0.5}
    assert summary.status_counts == {
        "true_accept": 2,
        "false_accept": 1,
        "false_alarm": 0,
        "caught": 1,
    }


def test_summary_reports_how_trustworthy_the_validated_status_is():
    trials = [
        _trial("a", [], make_invoice()),
        _trial("b", [], make_invoice(total=Decimal("99"))),  # erreur non détectée
        _trial("c", [], make_invoice(total=Decimal("98")), status="needs_review"),
    ]

    summary = summarize(trials)

    assert summary.validated_precision == pytest.approx(0.5)  # 1 bonne sur 2 « validated »
    assert summary.error_detection_rate == pytest.approx(0.5)  # 1 erreur détectée sur 2


def test_paired_bootstrap_of_identical_results_has_zero_difference():
    result = paired_bootstrap([1.0, 0.0, 1.0, 1.0], [1.0, 0.0, 1.0, 1.0])

    assert result.difference == 0.0
    assert result.low <= 0.0 <= result.high


def test_paired_bootstrap_detects_a_clear_difference():
    result = paired_bootstrap([1.0] * 10, [0.0] * 10)

    assert result.difference == 1.0
    assert (result.low, result.high) == (1.0, 1.0)


def test_paired_bootstrap_is_reproducible():
    a = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
    b = [1.0, 1.0, 0.0, 1.0, 0.0, 0.0]

    assert paired_bootstrap(a, b, seed=3) == paired_bootstrap(a, b, seed=3)


def test_word_error_rate_is_zero_for_identical_texts():
    from app.evaluation.metrics import word_error_rate

    assert word_error_rate("facture numéro douze", "Facture, numéro douze.") == 0.0


def test_word_error_rate_counts_substitutions_insertions_and_deletions():
    from app.evaluation.metrics import word_error_rate

    # Référence de 4 mots ; 1 substitution + 1 suppression = 2 erreurs sur 4
    assert word_error_rate("a b c d", "a x c") == 0.5


def test_word_error_rate_ignores_thousands_separators_in_numbers():
    from app.evaluation.metrics import word_error_rate

    assert word_error_rate("total 1234,50 euros", "total 1 234,50 euros") == 0.0


def test_word_error_rate_of_an_empty_hypothesis_is_one():
    from app.evaluation.metrics import word_error_rate

    assert word_error_rate("a b", "") == 1.0


def test_financial_perfect_ignores_names_and_descriptions_but_not_amounts():
    from app.evaluation.metrics import FIELDS, CaseScore

    only_names_wrong = dict.fromkeys(FIELDS, True)
    only_names_wrong.update(supplier_name=False, invoice_number=False, line_descriptions=False)
    amount_wrong = dict.fromkeys(FIELDS, True)
    amount_wrong["total"] = False

    assert CaseScore(only_names_wrong, 0, "validated", False).financial_perfect
    assert not CaseScore(only_names_wrong, 0, "validated", False).perfect
    assert not CaseScore(amount_wrong, 0, "validated", False).financial_perfect


def test_summary_reports_the_financial_perfect_rate():
    from app.evaluation.metrics import FIELDS, CaseScore, ScoredTrial, summarize

    good = dict.fromkeys(FIELDS, True)
    names_wrong = {**good, "supplier_name": False}
    trials = [
        ScoredTrial("a", (), CaseScore(good, 0, "validated", False)),
        ScoredTrial("b", (), CaseScore(names_wrong, 0, "validated", False)),
    ]

    summary = summarize(trials)

    assert summary.perfect_rate == 0.5
    assert summary.financial_perfect_rate == 1.0
