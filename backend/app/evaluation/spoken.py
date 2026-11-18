"""Fabrication des dictées d'évaluation : texte à dire, conditions d'enregistrement, étiquettes.

On part des mêmes factures synthétiques que pour les documents : la vérité terrain est donc
connue d'avance, et le texte exact qui est dit sert aussi de référence pour mesurer les erreurs
de transcription (voir `word_error_rate`). Fonctions pures, sans macOS ni ffmpeg.
"""

import re
from dataclasses import dataclass
from decimal import Decimal

from app.domains.extraction.schemas import Invoice
from app.evaluation.synthetic import FR_MONTHS, EvalCase

CURRENCY_NAMES = {"EUR": "euros", "CAD": "dollars canadiens", "USD": "dollars américains"}

# Étiquettes de contenu du jeu de documents qui ont encore un sens pour une dictée.
CONTENT_TAGS = {"multi_tax", "negative_line", "thousands", "missing_number", "decimal_quantity"}


@dataclass(frozen=True)
class RecordingConditions:
    voice: str
    words_per_minute: int
    noise_amplitude: float  # écart-type du bruit blanc ajouté, de 0 (aucun) à 1 (saturé)


def recording_conditions(index: int) -> RecordingConditions:
    """Conditions de prise de son, déterminées par la position du cas (donc reproductibles)."""
    return RecordingConditions(
        voice="Amélie" if index % 2 == 1 else "Thomas",  # Amélie : accent canadien
        words_per_minute=230 if index % 4 == 3 else 175,
        noise_amplitude=0.03 if index % 3 == 2 else 0.0,
    )


def select_audio_cases(cases: list[EvalCase], count: int) -> list[EvalCase]:
    """Garde les factures qu'on peut dicter naturellement en français (ni anglais, ni USD)."""
    keepable = [
        case
        for case in cases
        if case.invoice.currency in {"EUR", "CAD"} and "english" not in case.tags
    ]
    return keepable[:count]


def audio_tags(index: int, case: EvalCase) -> tuple[str, ...]:
    conditions = recording_conditions(index)
    tags = set(case.tags) & CONTENT_TAGS
    if conditions.words_per_minute > 200:
        tags.add("fast")
    if conditions.noise_amplitude > 0:
        tags.add("noisy")
    if conditions.voice == "Amélie":
        tags.add("canadian_voice")
    number = case.invoice.invoice_number
    if number and re.search(r"[A-Za-z]", number):
        tags.add("spelled_number")  # « I N V tiret 00123 » : lettres à épeler
    return tuple(sorted(tags))


def _spell(number: str) -> str:
    """Numéro de facture tel qu'on le dicte : lettres épelées, tiret prononcé."""
    parts = re.findall(r"[A-Za-z]|\d+|-", number)
    return " ".join("tiret" if part == "-" else part for part in parts)


def _amount(value: Decimal, currency: str) -> str:
    text = f"{abs(value):.2f}".replace(".", ",")  # pas de séparateur de milliers : 1234,50
    sign = "moins " if value < 0 else ""
    return f"{sign}{text} {CURRENCY_NAMES[currency]}"


def _quantity(value: Decimal) -> str:
    return format(value.normalize(), "f").replace(".", ",")


def spoken_text(invoice: Invoice) -> str:
    """Le texte lu à voix haute, comme le dicterait quelqu'un qui a la facture sous les yeux."""
    currency = invoice.currency
    day = invoice.issue_date
    opening = f"Facture {invoice.supplier_name}"
    if invoice.invoice_number:
        opening += f", numéro {_spell(invoice.invoice_number)}"
    sentences = [f"{opening}, émise le {day.day} {FR_MONTHS[day.month - 1]} {day.year}."]
    for position, line in enumerate(invoice.lines, start=1):
        sentences.append(
            f"Ligne {position} : {line.description}, {_quantity(line.quantity)} "
            f"à {_amount(line.unit_price, currency)}, soit {_amount(line.total, currency)}."
        )
    sentences += [
        f"Total hors taxes : {_amount(invoice.subtotal, currency)}.",
        f"Taxes : {_amount(invoice.tax_amount, currency)}.",
        f"Total toutes taxes comprises : {_amount(invoice.total, currency)}.",
    ]
    return " ".join(sentences)
