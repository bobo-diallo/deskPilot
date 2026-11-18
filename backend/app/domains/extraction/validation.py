from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.domains.extraction.schemas import Invoice

# Écart toléré pour les arrondis (un centime).
TOLERANCE = Decimal("0.01")

REQUIRED_FIELDS = ("supplier_name", "invoice_number", "issue_date", "total")


class IssueCode(Enum):
    MISSING_FIELD = "missing_field"
    NO_LINES = "no_lines"
    LINE_TOTAL_MISMATCH = "line_total_mismatch"
    SUBTOTAL_MISMATCH = "subtotal_mismatch"
    TOTAL_MISMATCH = "total_mismatch"
    FROM_AUDIO = "from_audio"  # source vocale : fiable sur les montants, pas sur les noms


@dataclass(frozen=True)
class ValidationIssue:
    """Une anomalie détectée. `code` sert aux programmes, `message` s'affiche à l'utilisateur."""

    code: IssueCode
    message: str
    field: str | None = None


def _differs(first: Decimal, second: Decimal) -> bool:
    return abs(first - second) > TOLERANCE


def validate_invoice(invoice: Invoice) -> list[ValidationIssue]:
    """Recoupe les montants de la facture. Une liste vide signifie « cohérente »."""
    issues: list[ValidationIssue] = []

    for field in REQUIRED_FIELDS:
        if getattr(invoice, field) is None:
            issues.append(
                ValidationIssue(IssueCode.MISSING_FIELD, f"Champ manquant : {field}", field=field)
            )

    if not invoice.lines:
        issues.append(ValidationIssue(IssueCode.NO_LINES, "Aucune ligne de facture trouvée"))

    for position, line in enumerate(invoice.lines, start=1):
        if _differs(line.quantity * line.unit_price, line.total):
            issues.append(
                ValidationIssue(
                    IssueCode.LINE_TOTAL_MISMATCH,
                    f"Ligne {position} : le total ne correspond pas à quantité × prix unitaire",
                )
            )

    if invoice.subtotal is not None and invoice.lines:
        if _differs(sum(line.total for line in invoice.lines), invoice.subtotal):
            issues.append(
                ValidationIssue(
                    IssueCode.SUBTOTAL_MISMATCH,
                    "Le total hors taxes ne correspond pas à la somme des lignes",
                )
            )

    if None not in (invoice.subtotal, invoice.tax_amount, invoice.total):
        if _differs(invoice.subtotal + invoice.tax_amount, invoice.total):
            issues.append(
                ValidationIssue(
                    IssueCode.TOTAL_MISMATCH,
                    "Le total ne correspond pas au total hors taxes plus les taxes",
                )
            )

    return issues
