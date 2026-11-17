from app.domains.extraction.validation import IssueCode, validate_invoice
from app.evaluation.synthetic import generate_cases

ALL_TAGS = {
    "digital",
    "scan",
    "noisy",
    "english",
    "multi_tax",
    "negative_line",
    "ambiguous_date",
    "thousands",
    "missing_number",
    "decimal_quantity",
}


def test_generates_24_cases_with_unique_ids():
    cases = generate_cases()

    assert len(cases) == 24
    assert len({case.case_id for case in cases}) == 24


def test_generation_is_deterministic_for_a_given_seed():
    first = generate_cases(seed=7)
    second = generate_cases(seed=7)

    assert first == second


def test_a_different_seed_gives_different_cases():
    assert generate_cases(seed=1) != generate_cases(seed=2)


def test_ground_truth_is_consistent_except_for_deliberately_missing_numbers():
    for case in generate_cases():
        issues = validate_invoice(case.invoice)
        if "missing_number" in case.tags:
            assert case.invoice.invoice_number is None
            assert [(i.code, i.field) for i in issues] == [
                (IssueCode.MISSING_FIELD, "invoice_number")
            ], case.case_id
        else:
            assert issues == [], case.case_id


def test_every_kind_of_difficulty_is_represented():
    tags = {tag for case in generate_cases() for tag in case.tags}

    assert ALL_TAGS <= tags


def test_medium_and_tags_agree():
    for case in generate_cases():
        if case.medium == "pdf":
            assert "digital" in case.tags and "scan" not in case.tags
        else:
            assert "scan" in case.tags and "digital" not in case.tags
        assert ("noisy" in case.tags) == (case.medium == "jpg"), case.case_id


def test_the_layout_prints_the_supplier_and_the_invoice_number_unless_missing():
    for case in generate_cases():
        printed = " ".join(item.text for item in case.items)
        assert case.invoice.supplier_name in printed, case.case_id
        if "missing_number" in case.tags:
            assert "n°" not in printed and "No." not in printed, case.case_id
        else:
            assert case.invoice.invoice_number in printed, case.case_id


def test_the_layout_prints_every_line_description():
    for case in generate_cases():
        printed = " ".join(item.text for item in case.items)
        for line in case.invoice.lines:
            assert line.description in printed, case.case_id


def _printed_date(case) -> str:
    return next(item.text for item in case.items if item.text.startswith("Date"))


def test_usd_invoices_follow_american_conventions_in_full():
    """Une facture en USD est en anglais avec une date mois/jour, sinon sa date est ambiguë.

    Défaut découvert par la première mesure : des factures en USD avec libellés français
    portaient une date américaine, que n'importe quel lecteur lirait à la française.
    """
    usd = [case for case in generate_cases() if case.invoice.currency == "USD"]

    assert usd
    for case in usd:
        printed = " ".join(item.text for item in case.items)
        assert "english" in case.tags, case.case_id
        assert "Facture" not in printed and "Date : " not in printed, case.case_id
        assert "All amounts in USD" in printed, case.case_id


def test_the_printed_date_always_matches_the_ground_truth_under_its_own_convention():
    import re

    for case in generate_cases():
        text = _printed_date(case).split(":", 1)[1].strip()
        match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", text)
        if match is None:
            continue  # date écrite en toutes lettres : pas d'ambiguïté
        first, second, year = (int(part) for part in match.groups())
        if case.invoice.currency == "USD":
            month, day = first, second  # convention américaine
        else:
            day, month = first, second  # convention européenne et canadienne-française
        assert (year, month, day) == (
            case.invoice.issue_date.year,
            case.invoice.issue_date.month,
            case.invoice.issue_date.day,
        ), case.case_id
