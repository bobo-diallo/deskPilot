"""Génère des factures fictives (PDF et image) et leurs valeurs attendues (JSON).

Usage, depuis backend/ :  .venv/bin/python scripts/generate_demo_invoices.py

Les valeurs attendues servent de « vérité terrain » : les tests réels et l'évaluation
(story 03) comparent ce que le modèle extrait à ces fichiers.
"""

import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domains.extraction.schemas import Invoice, InvoiceLine  # noqa: E402
from app.domains.extraction.validation import validate_invoice  # noqa: E402

# Polices TrueType avec accents et symbole € (macOS, puis Linux). La police par défaut de
# Pillow n'a pas ces caractères.
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "demo-data" / "invoices"
SYMBOLS = {"EUR": "€", "CAD": "$ CA"}


def line(description: str, quantity: str, unit_price: str, total: str) -> InvoiceLine:
    return InvoiceLine(
        description=description,
        quantity=Decimal(quantity),
        unit_price=Decimal(unit_price),
        total=Decimal(total),
    )


# (nom de fichier, format, facture, libellé des taxes affichées)
INVOICES = [
    (
        "facture-atelier-nord",
        "pdf",
        Invoice(
            supplier_name="Atelier Nord",
            invoice_number="2026-014",
            issue_date=date(2026, 11, 12),
            currency="EUR",
            lines=[
                line("Chaise en chêne", "2", "45.00", "90.00"),
                line("Table de salle à manger", "1", "120.00", "120.00"),
                line("Livraison", "1", "15.00", "15.00"),
            ],
            subtotal=Decimal("225.00"),
            tax_amount=Decimal("45.00"),
            total=Decimal("270.00"),
        ),
        [("TVA 20 %", "45.00")],
    ),
    (
        "facture-cafe-laurier",
        "pdf",
        Invoice(
            supplier_name="Café Laurier inc.",
            invoice_number="CL-88213",
            issue_date=date(2026, 10, 3),
            currency="CAD",
            lines=[
                line("Café en grains (kg)", "5", "24.50", "122.50"),
                line("Filtres papier (boîte)", "3", "8.90", "26.70"),
            ],
            subtotal=Decimal("149.20"),
            tax_amount=Decimal("22.34"),
            total=Decimal("171.54"),
        ),
        [("TPS 5 %", "7.46"), ("TVQ 9,975 %", "14.88")],
    ),
    (
        "facture-quincaillerie-dupont",
        "png",
        Invoice(
            supplier_name="Quincaillerie Dupont",
            invoice_number="F-2026-3307",
            issue_date=date(2026, 9, 21),
            currency="EUR",
            lines=[
                line("Vis à bois 4x40 (unité)", "200", "0.15", "30.00"),
                line("Marteau", "1", "18.90", "18.90"),
                line("Peinture blanche 2,5 L", "2", "32.50", "65.00"),
            ],
            subtotal=Decimal("113.90"),
            tax_amount=Decimal("22.78"),
            total=Decimal("136.68"),
        ),
        [("TVA 20 %", "22.78")],
    ),
]


def money(amount: Decimal, currency: str) -> str:
    """Format français : 1 250,00 €"""
    text = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    return f"{text} {SYMBOLS[currency]}"


def text_rows(invoice: Invoice, taxes: list[tuple[str, str]]) -> list[tuple[str, bool]]:
    """Lignes de texte de la facture, avec un indicateur « en gras »."""
    cur = invoice.currency
    rows = [
        (invoice.supplier_name, True),
        (f"Facture n° {invoice.invoice_number}", True),
        (f"Date : {invoice.issue_date.strftime('%d/%m/%Y')}", False),
        ("", False),
        ("Description | Qté | Prix unitaire | Total", True),
    ]
    for item in invoice.lines:
        rows.append(
            (
                f"{item.description} | {item.quantity} | {money(item.unit_price, cur)} "
                f"| {money(item.total, cur)}",
                False,
            )
        )
    rows.append(("", False))
    rows.append((f"Total hors taxes : {money(invoice.subtotal, cur)}", False))
    for label, amount in taxes:
        rows.append((f"{label} : {money(Decimal(amount), cur)}", False))
    rows.append((f"TOTAL À PAYER : {money(invoice.total, cur)}", True))
    return rows


def write_pdf(path: Path, rows: list[tuple[str, bool]]) -> None:
    pdf = canvas.Canvas(str(path), pagesize=A4)
    y = 780
    for text, bold in rows:
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 12)
        pdf.drawString(60, y, text)
        y -= 24
    pdf.save()


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise SystemExit("Aucune police TrueType trouvée : ajouter un chemin à FONT_CANDIDATES")


def write_png(path: Path, rows: list[tuple[str, bool]]) -> None:
    """Image simulant un scan : légèrement inclinée, fond blanc cassé."""
    image = Image.new("RGB", (1000, 700), (250, 250, 247))
    draw = ImageDraw.Draw(image)
    y = 40
    for text, bold in rows:
        font = load_font(26 if bold else 22)
        draw.text((50, y), text, fill=(20, 20, 20), font=font)
        y += 48
    image.rotate(1.2, expand=True, fillcolor=(250, 250, 247)).save(path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, file_format, invoice, taxes in INVOICES:
        assert validate_invoice(invoice) == [], f"{name} est incohérente"
        assert sum(Decimal(amount) for _, amount in taxes) == invoice.tax_amount, name
        rows = text_rows(invoice, taxes)
        target = OUTPUT_DIR / f"{name}.{file_format}"
        (write_pdf if file_format == "pdf" else write_png)(target, rows)
        expected = OUTPUT_DIR / f"{name}.expected.json"
        expected.write_text(
            json.dumps(invoice.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"généré : {target.name}")


if __name__ == "__main__":
    main()
