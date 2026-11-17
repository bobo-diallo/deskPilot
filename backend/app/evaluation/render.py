"""Dessine les cas synthétiques en PDF ou en image, et écrit le jeu de données sur disque.

Nécessite reportlab et pillow (dépendances de développement) : ce module n'est utilisé que
pour fabriquer le jeu d'évaluation, jamais par l'application.
"""

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.evaluation.synthetic import EvalCase, TextItem

PAGE_HEIGHT = A4[1]
IMAGE_SCALE = 1.5

# Polices avec accents et symbole € (macOS, puis Linux).
MACOS_FONTS = "/System/Library/Fonts/Supplemental"
LINUX_FONTS = "/usr/share/fonts/truetype/dejavu"
FONT_CANDIDATES = [
    (f"{MACOS_FONTS}/Arial.ttf", f"{MACOS_FONTS}/Arial Bold.ttf"),
    (f"{LINUX_FONTS}/DejaVuSans.ttf", f"{LINUX_FONTS}/DejaVuSans-Bold.ttf"),
]


def _font(size: int, bold: bool) -> ImageFont.FreeTypeFont:
    for regular, heavy in FONT_CANDIDATES:
        path = heavy if bold else regular
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise RuntimeError("Aucune police TrueType trouvée : ajouter un chemin à FONT_CANDIDATES")


def _render_pdf(case: EvalCase, path: Path) -> None:
    pdf = canvas.Canvas(str(path), pagesize=A4, invariant=1)  # invariant : sortie reproductible
    for item in case.items:
        pdf.setFont("Helvetica-Bold" if item.bold else "Helvetica", 11)
        y = PAGE_HEIGHT - item.y
        if item.align == "right":
            pdf.drawRightString(item.x, y, item.text)
        elif item.align == "center":
            pdf.drawCentredString(item.x, y, item.text)
        else:
            pdf.drawString(item.x, y, item.text)
    pdf.save()


def _draw_item(draw: ImageDraw.ImageDraw, item: TextItem) -> None:
    font = _font(round(11 * IMAGE_SCALE), item.bold)
    width = draw.textlength(item.text, font=font)
    x = item.x * IMAGE_SCALE
    if item.align == "right":
        x -= width
    elif item.align == "center":
        x -= width / 2
    draw.text((x, item.y * IMAGE_SCALE), item.text, fill=(20, 20, 20), font=font)


def _render_image(case: EvalCase, path: Path) -> None:
    size = (round(595 * IMAGE_SCALE), round(PAGE_HEIGHT * IMAGE_SCALE))
    page_color = (250, 250, 247)
    image = Image.new("RGB", size, page_color)
    draw = ImageDraw.Draw(image)
    for item in case.items:
        _draw_item(draw, item)

    if case.medium == "png":
        image.save(path)
        return

    # Scan bruité : légère rotation, flou, compression JPEG forte. Graine = id du cas.
    rng = random.Random(case.case_id)
    image = image.rotate(rng.uniform(-2.0, 2.0), fillcolor=page_color)
    image = image.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.5, 0.9)))
    image.save(path, quality=45)


def render_case(case: EvalCase, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{case.case_id}.{case.medium}"
    if case.medium == "pdf":
        _render_pdf(case, path)
    else:
        _render_image(case, path)
    return path


def write_dataset(cases: list[EvalCase], directory: Path) -> None:
    """Écrit pour chaque cas : le fichier, `<id>.expected.json`, et un `manifest.json` global."""
    entries = []
    for case in cases:
        path = render_case(case, directory)
        (directory / f"{case.case_id}.expected.json").write_text(
            json.dumps(case.invoice.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        entries.append({"id": case.case_id, "file": path.name, "tags": list(case.tags)})
    (directory / "manifest.json").write_text(
        json.dumps({"cases": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
