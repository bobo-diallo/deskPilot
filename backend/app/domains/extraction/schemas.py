from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class InvoiceLine(BaseModel):
    description: str
    quantity: Decimal
    unit_price: Decimal = Field(description="Prix unitaire hors taxes")
    total: Decimal = Field(description="Total de la ligne hors taxes")


class Invoice(BaseModel):
    """Champs d'une facture. Un champ absent du document vaut None : on n'invente jamais."""

    supplier_name: str | None = Field(default=None, description="Nom du fournisseur")
    invoice_number: str | None = Field(default=None, description="Numéro de facture")
    issue_date: date | None = Field(default=None, description="Date d'émission")
    currency: str | None = Field(default=None, description="Code devise, ex. EUR, CAD")
    lines: list[InvoiceLine] = Field(default_factory=list)
    subtotal: Decimal | None = Field(default=None, description="Total hors taxes")
    tax_amount: Decimal | None = Field(default=None, description="Montant total des taxes")
    total: Decimal | None = Field(default=None, description="Total toutes taxes comprises")
