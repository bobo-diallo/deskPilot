import csv
import io
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.agent.tools.base import Tool, ToolExecutionError
from app.domains.extraction.models import Extraction
from app.domains.extraction.schemas import Invoice
from app.domains.extraction.validation import validate_invoice


def _all_extractions(session: Session) -> list[Extraction]:
    return list(session.scalars(select(Extraction).order_by(Extraction.id)))


def _describe(extraction: Extraction) -> str:
    data = extraction.data
    return (
        f"id={extraction.id} | {data.get('supplier_name')} | n° {data.get('invoice_number')} | "
        f"{data.get('issue_date')} | {data.get('total')} {data.get('currency')} | "
        f"{extraction.status}"
    )


class ListInvoicesArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier: str | None = Field(default=None, description="Une partie du nom du fournisseur")
    status: Literal["validated", "needs_review", "approved", "corrected", "rejected"] | None = (
        Field(default=None, description="Statut de l'extraction")
    )
    limit: int = Field(default=10, ge=1, le=20)


class ListInvoicesTool(Tool):
    name = "list_invoices"
    description = (
        "Liste les factures extraites (id, fournisseur, numéro, date, total, statut), avec "
        "filtre optionnel par fournisseur ou statut. À utiliser pour compter ou retrouver des "
        "factures."
    )
    args_model = ListInvoicesArgs

    def __init__(self, session: Session):
        self._session = session

    def run(self, arguments: ListInvoicesArgs) -> str:
        matches = [
            extraction
            for extraction in _all_extractions(self._session)
            if (
                arguments.supplier is None
                or arguments.supplier.casefold()
                in str(extraction.data.get("supplier_name") or "").casefold()
            )
            and (arguments.status is None or extraction.status == arguments.status)
        ]
        if not matches:
            return "Aucune facture ne correspond."
        shown = matches[: arguments.limit]
        header = f"{len(matches)} facture(s) trouvée(s), {len(shown)} affichée(s) :"
        return "\n".join([header, *(_describe(extraction) for extraction in shown)])


class CheckInvoiceArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extraction_id: int = Field(description="Identifiant de la facture (id donné par list_invoices)")


class CheckInvoiceTool(Tool):
    name = "check_invoice"
    description = (
        "Vérifie une facture : recoupe les montants (lignes, sous-total, total) et cherche un "
        "doublon possible (même fournisseur et même numéro)."
    )
    args_model = CheckInvoiceArgs

    def __init__(self, session: Session):
        self._session = session

    def run(self, arguments: CheckInvoiceArgs) -> str:
        extraction = self._session.get(Extraction, arguments.extraction_id)
        if extraction is None:
            raise ToolExecutionError(f"Facture introuvable : id={arguments.extraction_id}")

        invoice = Invoice.model_validate(extraction.data)
        issues = validate_invoice(invoice)
        lines = [f"Facture {_describe(extraction)}"]
        lines += (
            [f"- anomalie {issue.code.value} : {issue.message}" for issue in issues]
            if issues
            else ["Aucune anomalie de montants."]
        )

        supplier = (invoice.supplier_name or "").casefold().strip()
        if supplier and invoice.invoice_number:
            for other in _all_extractions(self._session):
                other_data = other.data
                same = (
                    other.id != extraction.id
                    and str(other_data.get("supplier_name") or "").casefold().strip() == supplier
                    and other_data.get("invoice_number") == invoice.invoice_number
                )
                if same:
                    lines.append(f"Doublon possible avec {_describe(other)}")
        return "\n".join(lines)


class ExportInvoicesArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extraction_ids: list[int] = Field(min_length=1, max_length=50)


EXPORT_COLUMNS = (
    "id",
    "supplier_name",
    "invoice_number",
    "issue_date",
    "currency",
    "subtotal",
    "tax_amount",
    "total",
    "status",
)


def _safe_cell(value) -> str:
    """Neutralise l'injection de formule (cellule commençant par = + - ou @ dans un tableur)."""
    text = "" if value is None else str(value)
    return f"'{text}" if text[:1] in ("=", "+", "-", "@") else text


class ExportInvoicesTool(Tool):
    name = "export_invoices"
    description = (
        "Exporte des factures choisies dans un fichier CSV. Action sensible : elle n'est exécutée "
        "qu'après l'approbation d'un humain."
    )
    args_model = ExportInvoicesArgs
    sensitive = True

    def __init__(self, session: Session, export_dir: Path):
        self._session = session
        self._export_dir = Path(export_dir)

    def run(self, arguments: ExportInvoicesArgs) -> str:
        found = {e.id: e for e in _all_extractions(self._session)}
        missing = [i for i in arguments.extraction_ids if i not in found]
        if missing:
            # Rien n'est écrit si une seule facture manque : un export partiel serait trompeur.
            raise ToolExecutionError(f"Facture(s) introuvable(s) : id={missing}")

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for extraction_id in arguments.extraction_ids:
            extraction = found[extraction_id]
            row = {"id": extraction.id, "status": extraction.status}
            row.update({name: extraction.data.get(name) for name in EXPORT_COLUMNS[1:-1]})
            writer.writerow({key: _safe_cell(value) for key, value in row.items()})

        self._export_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = self._export_dir / f"export-{stamp}-{uuid.uuid4().hex[:6]}.csv"
        path.write_text(buffer.getvalue(), encoding="utf-8")
        return f"Export écrit : {path.name} ({len(arguments.extraction_ids)} facture(s))"
