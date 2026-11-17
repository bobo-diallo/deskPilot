import io
from datetime import date
from decimal import Decimal

import pytest
from reportlab.pdfgen import canvas

from app.domains.extraction.errors import ExtractionError
from app.domains.extraction.extractors.text_layer import TextLayerExtractor
from app.domains.extraction.schemas import Invoice
from app.domains.llm.providers.fake import FakeProvider
from app.domains.llm.service import LLMService


def make_pdf(*lines: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    for number, text in enumerate(lines):
        pdf.drawString(72, 750 - 20 * number, text)
    pdf.save()
    return buffer.getvalue()


def make_invoice() -> Invoice:
    return Invoice(
        supplier_name="Atelier Nord",
        invoice_number="1",
        issue_date=date(2026, 11, 12),
        currency="EUR",
        lines=[],
        subtotal=Decimal("20.00"),
        tax_amount=Decimal("4.00"),
        total=Decimal("24.00"),
    )


def build(session, model=None):
    provider = FakeProvider(parsed=make_invoice())
    return provider, TextLayerExtractor(LLMService(provider, session), model=model)


def test_only_the_text_is_sent_to_the_model_not_the_file(session):
    provider, extractor = build(session)

    extractor.extract(make_pdf("Atelier Nord", "Total : 24,00 EUR"), "application/pdf")

    request = provider.received[0]
    assert request.attachments == []  # aucune image de page : c'est tout l'intérêt
    assert "Atelier Nord" in request.messages[0].content
    assert "Total : 24,00 EUR" in request.messages[0].content
    assert request.response_schema is Invoice


def test_the_model_can_be_forced(session):
    provider, extractor = build(session, model="claude-haiku-5-5")

    extractor.extract(make_pdf("Facture"), "application/pdf")

    assert provider.received[0].model == "claude-haiku-5-5"


def test_the_result_is_returned_with_the_model_used(session):
    _, extractor = build(session, model="claude-haiku-5-5")

    output = extractor.extract(make_pdf("Facture"), "application/pdf")

    assert output.data == make_invoice()
    assert output.model == "claude-haiku-5-5"


def test_an_image_is_refused_without_calling_the_model(session):
    provider, extractor = build(session)

    with pytest.raises(ExtractionError, match="PDF"):
        extractor.extract(b"\x89PNG\r\n\x1a\n", "image/png")

    assert provider.received == []


def test_a_pdf_without_text_layer_is_refused_without_calling_the_model(session):
    provider, extractor = build(session)
    empty_pdf = make_pdf()  # page blanche : comme un scan sans texte

    with pytest.raises(ExtractionError, match="texte"):
        extractor.extract(empty_pdf, "application/pdf")

    assert provider.received == []


def test_the_prompt_version_can_be_chosen(session):
    from app.domains.extraction.prompts import get_prompt

    provider = FakeProvider(parsed=make_invoice())
    extractor = TextLayerExtractor(LLMService(provider, session), prompt_version="v1")

    extractor.extract(make_pdf("Facture"), "application/pdf")

    assert provider.received[0].system == get_prompt("v1")
