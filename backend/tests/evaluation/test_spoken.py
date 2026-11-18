from datetime import date
from decimal import Decimal

from app.domains.extraction.schemas import Invoice, InvoiceLine
from app.evaluation.spoken import audio_tags, select_audio_cases, spoken_text
from app.evaluation.synthetic import generate_cases


def make_invoice(**changes) -> Invoice:
    values = dict(
        supplier_name="Plomberie Tremblay",
        invoice_number="INV-00123",
        issue_date=date(2026, 3, 3),
        currency="EUR",
        lines=[
            InvoiceLine(
                description="Réparation de fuite",
                quantity=Decimal("1.5"),
                unit_price=Decimal("450.00"),
                total=Decimal("675.00"),
            ),
            InvoiceLine(
                description="Remise commerciale",
                quantity=Decimal("1"),
                unit_price=Decimal("-45.00"),
                total=Decimal("-45.00"),
            ),
        ],
        subtotal=Decimal("630.00"),
        tax_amount=Decimal("126.00"),
        total=Decimal("756.00"),
    )
    values.update(changes)
    return Invoice(**values)


def test_the_supplier_the_date_in_words_and_the_totals_are_dictated():
    text = spoken_text(make_invoice())

    assert "Plomberie Tremblay" in text
    assert "3 mars 2026" in text  # la date se dicte en toutes lettres : pas d'ambiguïté
    assert "630,00 euros" in text
    assert "126,00 euros" in text
    assert "756,00 euros" in text


def test_the_invoice_number_is_spelled_out_as_a_person_would_dictate_it():
    assert "I N V tiret 00123" in spoken_text(make_invoice())


def test_lines_are_dictated_with_decimal_quantity_and_negative_amounts():
    text = spoken_text(make_invoice())

    assert "Réparation de fuite, 1,5 à 450,00 euros, soit 675,00 euros" in text
    assert "moins 45,00 euros" in text


def test_a_missing_invoice_number_is_simply_not_mentioned():
    assert "numéro" not in spoken_text(make_invoice(invoice_number=None))


def test_the_currency_name_follows_the_invoice():
    assert "dollars canadiens" in spoken_text(make_invoice(currency="CAD"))


def test_audio_cases_are_french_and_not_in_us_dollars():
    cases = select_audio_cases(generate_cases(), count=12)

    assert len(cases) == 12
    assert all(case.invoice.currency in {"EUR", "CAD"} for case in cases)
    assert all("english" not in case.tags for case in cases)


def test_audio_tags_describe_the_recording_conditions_and_the_content():
    cases = select_audio_cases(generate_cases(), count=12)

    all_tags = {tag for index, case in enumerate(cases) for tag in audio_tags(index, case)}

    assert {"fast", "noisy", "canadian_voice", "spelled_number"} <= all_tags
    # Les étiquettes propres au document papier n'ont plus de sens pour une dictée
    assert not {"digital", "scan", "ambiguous_date"} & all_tags
