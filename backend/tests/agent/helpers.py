from datetime import date
from decimal import Decimal

from app.domains.documents.models import Document
from app.domains.extraction.models import Extraction, ExtractionStatus
from app.domains.extraction.schemas import Invoice, InvoiceLine


def make_invoice(supplier="Atelier Nord", number="2026-014", total="1200.00", **changes) -> Invoice:
    values = dict(
        supplier_name=supplier,
        invoice_number=number,
        issue_date=date(2026, 3, 3),
        currency="EUR",
        lines=[
            InvoiceLine(
                description="Réparation",
                quantity=Decimal("1"),
                unit_price=Decimal("1000.00"),
                total=Decimal("1000.00"),
            )
        ],
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("200.00"),
        total=Decimal(total),
    )
    values.update(changes)
    return Invoice(**values)


def add_extraction(session, status=ExtractionStatus.VALIDATED, **invoice_changes) -> Extraction:
    document = Document(filename="f.pdf", media_type="application/pdf")
    session.add(document)
    session.commit()
    extraction = Extraction(
        document_id=document.id,
        document_type="invoice",
        status=status.value,
        data=make_invoice(**invoice_changes).model_dump(mode="json"),
        issues=[],
        model="claude-haiku-5-5",
    )
    session.add(extraction)
    session.commit()
    return extraction
