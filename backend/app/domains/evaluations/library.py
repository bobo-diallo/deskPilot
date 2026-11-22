import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


class UnknownReportError(Exception):
    """L'identifiant demandé ne correspond à aucun rapport de la bibliothèque."""


@dataclass(frozen=True)
class ReportSummary:
    id: str
    title: str
    date: date | None


@dataclass(frozen=True)
class Table:
    headers: list[str]
    rows: list[list[str]]


@dataclass
class Section:
    title: str
    paragraphs: list[str] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)


@dataclass
class Report:
    id: str
    title: str
    date: date | None
    intro: str
    sections: list[Section]


_DATE_PREFIX = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def _date_of(report_id: str) -> date | None:
    """La date est le préfixe AAAA-MM-JJ du nom de fichier (ex. 2026-11-17-prompt-v2)."""
    match = _DATE_PREFIX.match(report_id)
    if not match:
        return None
    try:
        return date(*(int(part) for part in match.groups()))
    except ValueError:
        return None


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:|-]+\|", line.strip()))


def parse_report(report_id: str, markdown: str) -> Report:
    """Lit un rapport Markdown : titre, introduction, puis sections (texte et tableaux)."""
    title = report_id
    intro_lines: list[str] = []
    sections: list[Section] = []
    current: Section | None = None
    table_lines: list[str] = []

    def add_paragraph(text: str) -> None:
        if current is not None:
            current.paragraphs.append(text)
        else:
            intro_lines.append(text)

    def flush_table() -> None:
        nonlocal table_lines
        if current is not None and len(table_lines) >= 2:
            rows = [_cells(line) for line in table_lines[2:]]  # on saute l'en-tête et le séparateur
            current.tables.append(Table(headers=_cells(table_lines[0]), rows=rows))
        table_lines = []

    for line in markdown.splitlines():
        if line.startswith("|"):
            table_lines.append(line)
            continue
        flush_table()
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            current = Section(title=line[3:].strip())
            sections.append(current)
        elif line.strip():
            add_paragraph(line.strip())
    flush_table()

    return Report(
        id=report_id,
        title=title,
        date=_date_of(report_id),
        intro=" ".join(intro_lines),
        sections=sections,
    )


class ReportLibrary:
    """Lit les rapports d'évaluation (fichiers Markdown) d'un dossier, en lecture seule."""

    def __init__(self, directory: Path | str):
        self._directory = Path(directory)

    def _files(self) -> dict[str, Path]:
        if not self._directory.is_dir():
            return {}
        return {path.stem: path for path in self._directory.glob("*.md")}

    def list(self) -> list[ReportSummary]:
        summaries = [
            ReportSummary(
                id=report_id,
                title=parse_report(report_id, path.read_text(encoding="utf-8")).title,
                date=_date_of(report_id),
            )
            for report_id, path in self._files().items()
        ]
        return sorted(summaries, key=lambda s: s.id, reverse=True)

    def get(self, report_id: str) -> Report:
        # L'identifiant doit figurer dans la liste des fichiers existants : on ne construit
        # jamais un chemin à partir de la saisie, donc « ../ » ne mène nulle part.
        path = self._files().get(report_id)
        if path is None:
            raise UnknownReportError(report_id)
        return parse_report(report_id, path.read_text(encoding="utf-8"))
