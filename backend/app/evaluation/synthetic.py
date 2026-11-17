"""Génération déterministe de factures fictives pour l'évaluation.

Pour chaque cas, on produit la facture attendue (la « vérité terrain ») **et** une mise en page
abstraite (une liste de textes positionnés). Deux moteurs la dessinent ensuite en PDF ou en
image (voir render.py). Comme la vérité est connue par construction, aucune annotation
manuelle n'est nécessaire.

Limite assumée : ce sont des factures synthétiques, plus propres que la réalité.
"""

import random
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.domains.extraction.schemas import Invoice, InvoiceLine

CENT = Decimal("0.01")

SUPPLIERS = [
    "Atelier Nord", "Café Laurier inc.", "Quincaillerie Dupont", "Boulangerie Moreau",
    "Garage Tremblay", "Imprimerie du Centre", "Papeterie Lemieux", "Jardin des Saveurs",
    "Électro Plus", "Librairie Gagnon", "Transports Beaulieu", "Pharmacie du Marché",
    "Studio Lumière", "Ferme des Collines", "Menuiserie Roy", "Nettoyage Express",
    "Fleuriste Bergeron", "Informatique Cloutier", "Traiteur Saint-Pierre", "Cabinet Dubois",
    "Mécanique Lavoie", "Distillerie Gauthier", "Vitrerie Pelletier", "Épicerie Fine Morin",
]  # fmt: skip

# (français, anglais, prix minimal en centimes, prix maximal en centimes)
CATALOG = [
    ("Chaise en chêne", "Oak chair", 3500, 9000),
    ("Table de salle à manger", "Dining table", 9000, 25000),
    ("Café en grains (kg)", "Coffee beans (kg)", 1800, 3200),
    ("Filtres papier (boîte)", "Paper filters (box)", 500, 1500),
    ("Vis à bois 4x40 (unité)", "Wood screw 4x40 (each)", 10, 40),
    ("Marteau", "Hammer", 1200, 3500),
    ("Peinture blanche 2,5 L", "White paint 2.5 L", 2500, 5500),
    ("Impression A4 (lot de 100)", "A4 printing (pack of 100)", 800, 2400),
    ("Cartouche d'encre", "Ink cartridge", 2200, 6800),
    ("Heure de main-d'œuvre", "Labour hour", 4500, 9500),
    ("Livraison", "Delivery", 800, 2500),
    ("Câble réseau 5 m", "Network cable 5 m", 600, 1800),
    ("Lampe de bureau", "Desk lamp", 2500, 7500),
    ("Abonnement mensuel", "Monthly subscription", 1500, 9900),
    ("Formation d'une journée", "One-day training", 30000, 60000),
    ("Entretien annuel", "Annual maintenance", 15000, 40000),
]  # fmt: skip

# Prix « premium » (centaines d'euros) pour provoquer des montants avec séparateur de milliers.
PREMIUM_CATALOG = [
    ("Poste de travail complet", "Complete workstation", 90000, 180000),
    ("Licence logicielle annuelle", "Annual software licence", 95000, 220000),
    ("Rénovation de cuisine (forfait)", "Kitchen renovation (flat fee)", 120000, 250000),
]  # fmt: skip

FR_MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
    "septembre", "octobre", "novembre", "décembre",
]  # fmt: skip
EN_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

LABELS = {
    "fr": {
        "invoice": "Facture n° ", "date": "Date : ", "description": "Description",
        "quantity": "Qté", "unit": "Prix unitaire", "total": "Total",
        "subtotal": "Total hors taxes : ", "due": "TOTAL À PAYER : ",
        "currency_note": "Montants exprimés en ", "discount": "Remise commerciale",
    },
    "en": {
        "invoice": "Invoice No. ", "date": "Date: ", "description": "Description",
        "quantity": "Qty", "unit": "Unit price", "total": "Amount",
        "subtotal": "Subtotal: ", "due": "TOTAL DUE: ",
        "currency_note": "All amounts in ", "discount": "Trade discount",
    },
}  # fmt: skip


@dataclass(frozen=True)
class TextItem:
    """Un texte posé sur la page (points ; origine en haut à gauche ; page A4 de 595 x 842)."""

    x: float
    y: float
    text: str
    bold: bool = False
    align: str = "left"  # "left", "right" ou "center"


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    invoice: Invoice  # vérité terrain
    tags: tuple[str, ...]
    medium: str  # "pdf", "png" (scan propre) ou "jpg" (scan bruité)
    items: tuple[TextItem, ...]  # mise en page


def _round(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _money(amount: Decimal, currency: str) -> str:
    if currency == "USD":
        sign = "-" if amount < 0 else ""
        return f"{sign}${abs(amount):,.2f}"
    text = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    return f"{text} {'€' if currency == 'EUR' else '$ CA'}"


def _quantity(quantity: Decimal, currency: str) -> str:
    text = f"{quantity:f}"
    return text if currency == "USD" else text.replace(".", ",")


def _date_text(day: date, currency: str, numeric: bool) -> str:
    if currency == "USD":
        if numeric:
            return f"{day.month:02d}/{day.day:02d}/{day.year}"
        return f"{EN_MONTHS[day.month - 1]} {day.day}, {day.year}"
    if numeric:
        return f"{day.day:02d}/{day.month:02d}/{day.year}"
    return f"{day.day} {FR_MONTHS[day.month - 1]} {day.year}"


def _tax_rules(currency: str, english: bool, rng: random.Random) -> list[tuple[str, Decimal]]:
    if currency == "CAD":
        if english:
            return [("GST 5 %", Decimal("0.05")), ("QST 9.975 %", Decimal("0.09975"))]
        return [("TPS 5 %", Decimal("0.05")), ("TVQ 9,975 %", Decimal("0.09975"))]
    if currency == "USD":
        return [("Sales tax 8 %" if english else "Taxe de vente 8 %", Decimal("0.08"))]
    if rng.random() < 0.7:
        return [("VAT 20 %" if english else "TVA 20 %", Decimal("0.20"))]
    return [("VAT 5.5 %" if english else "TVA 5,5 %", Decimal("0.055"))]


def _build_lines(
    rng: random.Random, premium: bool, decimal_quantity: bool, negative_line: bool, labels: dict
) -> list[InvoiceLine]:
    english = labels["invoice"].startswith("Invoice")
    catalog = PREMIUM_CATALOG if premium else CATALOG
    lines: list[InvoiceLine] = []
    for fr, en, low, high in rng.sample(catalog, k=min(len(catalog), rng.randint(2, 5))):
        unit_price = Decimal(rng.randint(low, high)) / 100
        if decimal_quantity and not lines:
            quantity = Decimal(rng.choice(["0.5", "1.5", "2.5"]))
        else:
            quantity = Decimal(rng.randint(1, 6))
        lines.append(
            InvoiceLine(
                description=en if english else fr,
                quantity=quantity,
                unit_price=unit_price,
                total=_round(quantity * unit_price),
            )
        )
    if negative_line:
        discount = _round(sum(line.total for line in lines) * Decimal("0.10"))
        lines.append(
            InvoiceLine(
                description=labels["discount"],
                quantity=Decimal("1"),
                unit_price=-discount,
                total=-discount,
            )
        )
    return lines


def _layout(
    variant: int,
    labels: dict,
    invoice: Invoice,
    taxes: list[tuple[str, Decimal]],
    date_text: str,
) -> tuple[TextItem, ...]:
    currency = invoice.currency
    items: list[TextItem] = []
    header_x, header_align = {0: (50, "left"), 1: (545, "right"), 2: (297, "center")}[variant]

    y = 60
    items.append(TextItem(header_x, y, invoice.supplier_name, bold=True, align=header_align))
    if invoice.invoice_number is not None:
        y += 28
        number = f"{labels['invoice']}{invoice.invoice_number}"
        items.append(TextItem(header_x, y, number, bold=True, align=header_align))
    y += 24
    items.append(TextItem(header_x, y, f"{labels['date']}{date_text}", align=header_align))

    # En-tête du tableau : la variante 1 place la quantité avant la description.
    y = 220
    if variant == 1:
        columns = [(50, "left", "quantity"), (95, "left", "description")]
    else:
        columns = [(50, "left", "description"), (335, "right", "quantity")]
    columns += [(440, "right", "unit"), (545, "right", "total")]
    for x, align, key in columns:
        items.append(TextItem(x, y, labels[key], bold=True, align=align))

    for line in invoice.lines:
        y += 24
        cells = {
            "description": line.description,
            "quantity": _quantity(line.quantity, currency),
            "unit": _money(line.unit_price, currency),
            "total": _money(line.total, currency),
        }
        for x, align, key in columns:
            items.append(TextItem(x, y, cells[key], align=align))

    y += 40
    items.append(
        TextItem(545, y, f"{labels['subtotal']}{_money(invoice.subtotal, currency)}", align="right")
    )
    for label, rate in taxes:
        y += 24
        amount = _money(_round(sum(line.total for line in invoice.lines) * rate), currency)
        items.append(TextItem(545, y, f"{label} : {amount}", align="right"))
    y += 28
    items.append(
        TextItem(545, y, f"{labels['due']}{_money(invoice.total, currency)}", True, "right")
    )
    items.append(TextItem(50, 800, f"{labels['currency_note']}{currency}"))
    return tuple(items)


def generate_cases(seed: int = 2026, count: int = 24) -> list[EvalCase]:
    rng = random.Random(seed)
    suppliers = rng.sample(SUPPLIERS, k=count)
    cases: list[EvalCase] = []

    for index in range(count):
        currency = ["EUR", "CAD", "USD"][index % 3]
        # Une facture en dollars US suit les conventions américaines complètes : libellés en
        # anglais et date mois/jour. Sans cela, une date comme 05/07/2026 est réellement ambiguë.
        english = index % 4 == 3 or currency == "USD"
        premium = index % 4 == 1
        negative_line = index % 5 == 2
        missing_number = index % 6 == 5
        decimal_quantity = index % 7 == 3
        medium = "pdf" if index < 14 else ("png" if index < 18 else "jpg")
        labels = LABELS["en" if english else "fr"]

        issue_date = date(2026, rng.randint(1, 12), rng.randint(1, 28))
        if currency == "USD":
            # Date américaine numérique avec jour <= 12 : volontairement ambiguë (12/11 ou 11/12 ?).
            issue_date = date(2026, rng.randint(1, 12), rng.choice([d for d in range(1, 13)]))
            if issue_date.day == issue_date.month:
                issue_date = date(2026, issue_date.month, (issue_date.day % 12) + 1)
            numeric_date = True
        else:
            numeric_date = rng.random() < 0.5
        ambiguous_date = (
            numeric_date and issue_date.day <= 12 and issue_date.day != issue_date.month
        )

        lines = _build_lines(rng, premium, decimal_quantity, negative_line, labels)
        taxes = _tax_rules(currency, english, rng)
        subtotal = sum(line.total for line in lines)
        tax_amount = sum(_round(subtotal * rate) for _, rate in taxes)

        number = None
        if not missing_number:
            number = rng.choice(
                [
                    f"2026-{rng.randint(1, 999):03d}",
                    f"INV-{rng.randint(1, 99999):05d}",
                    f"F{rng.randint(1, 9999)}",
                ]
            )
        invoice = Invoice(
            supplier_name=suppliers[index],
            invoice_number=number,
            issue_date=issue_date,
            currency=currency,
            lines=lines,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total=subtotal + tax_amount,
        )

        tags = {"digital" if medium == "pdf" else "scan"}
        if medium == "jpg":
            tags.add("noisy")
        if english:
            tags.add("english")
        if len(taxes) > 1:
            tags.add("multi_tax")
        if negative_line:
            tags.add("negative_line")
        if ambiguous_date:
            tags.add("ambiguous_date")
        if invoice.total >= 1000:
            tags.add("thousands")
        if missing_number:
            tags.add("missing_number")
        if decimal_quantity:
            tags.add("decimal_quantity")

        date_text = _date_text(issue_date, currency, numeric_date)
        cases.append(
            EvalCase(
                case_id=f"inv-{index + 1:02d}",
                invoice=invoice,
                tags=tuple(sorted(tags)),
                medium=medium,
                items=_layout(index % 3, labels, invoice, taxes, date_text),
            )
        )
    return cases
