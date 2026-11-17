from datetime import date
from decimal import Decimal

from app.domains.extraction.schemas import Invoice, InvoiceLine
from app.domains.extraction.validation import IssueCode, validate_invoice


def make_invoice(**changes) -> Invoice:
    """Facture cohérente : 2 x 10,00 + 1 x 5,00 = 25,00 HT ; TVA 5,00 ; total 30,00."""
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


def codes(invoice: Invoice) -> list[IssueCode]:
    return [issue.code for issue in validate_invoice(invoice)]


def test_a_consistent_invoice_has_no_issue():
    assert validate_invoice(make_invoice()) == []


def test_line_total_must_match_quantity_times_unit_price():
    bad_line = InvoiceLine(
        description="Chaise",
        quantity=Decimal("2"),
        unit_price=Decimal("10.00"),
        total=Decimal("25.00"),
    )

    assert IssueCode.LINE_TOTAL_MISMATCH in codes(make_invoice(lines=[bad_line]))


def test_subtotal_must_match_sum_of_lines():
    assert IssueCode.SUBTOTAL_MISMATCH in codes(make_invoice(subtotal=Decimal("99.00")))


def test_total_must_match_subtotal_plus_tax():
    assert IssueCode.TOTAL_MISMATCH in codes(make_invoice(total=Decimal("31.00")))


def test_a_one_cent_rounding_gap_is_tolerated():
    assert validate_invoice(make_invoice(total=Decimal("30.01"))) == []


def test_missing_required_fields_are_reported_with_their_name():
    issues = validate_invoice(make_invoice(invoice_number=None, total=None))

    missing = {issue.field for issue in issues if issue.code == IssueCode.MISSING_FIELD}
    assert missing == {"invoice_number", "total"}


def test_an_invoice_without_lines_is_reported():
    assert IssueCode.NO_LINES in codes(make_invoice(lines=[], subtotal=None))


def test_every_issue_has_a_french_message():
    issues = validate_invoice(make_invoice(subtotal=Decimal("99.00")))

    assert all(issue.message for issue in issues)
