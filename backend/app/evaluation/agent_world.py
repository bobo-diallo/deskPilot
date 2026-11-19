from decimal import Decimal

from sqlalchemy.orm import Session

from app.domains.documents.models import Document
from app.domains.extraction.models import Extraction
from app.domains.extraction.schemas import Invoice, InvoiceLine
from app.domains.extraction.validation import validate_invoice
from app.domains.search.ports import Embedder
from app.domains.search.service import SearchService
from app.evaluation.agent_dataset import AgentDataset, WorldInvoice


def _invoice(raw: WorldInvoice) -> Invoice:
    subtotal = Decimal(raw.subtotal)
    return Invoice(
        supplier_name=raw.supplier_name,
        invoice_number=raw.invoice_number,
        issue_date=raw.issue_date,
        currency=raw.currency,
        lines=[
            InvoiceLine(
                description="Prestation", quantity=Decimal(1), unit_price=subtotal, total=subtotal
            )
        ],
        subtotal=subtotal,
        tax_amount=Decimal(raw.tax_amount),
        total=Decimal(raw.total),
    )


def build_world(session: Session, dataset: AgentDataset, embedder: Embedder) -> None:
    """Prépare ce que l'agent voit : les contrats indexés et les factures déjà extraites.

    Les factures reçoivent les identifiants 1, 2, 3… dans l'ordre du fichier, et leurs anomalies
    sont calculées par la vraie validation (pas écrites à la main).
    """
    search = SearchService(session, embedder)
    for document in dataset.documents:
        search.index_text(document.title, document.text)

    for raw in dataset.invoices:
        invoice = _invoice(raw)
        file = Document(filename=f"{raw.supplier_name}.pdf", media_type="application/pdf")
        session.add(file)
        session.flush()
        session.add(
            Extraction(
                document_id=file.id,
                document_type="invoice",
                status=raw.status,
                data=invoice.model_dump(mode="json"),
                issues=[
                    {"code": i.code.value, "field": i.field, "message": i.message}
                    for i in validate_invoice(invoice)
                ],
                model="claude-haiku-5-5",
            )
        )
    session.commit()
