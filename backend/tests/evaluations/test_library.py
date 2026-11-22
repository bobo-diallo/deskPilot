from datetime import date

import pytest

from app.domains.evaluations.library import ReportLibrary, UnknownReportError

SAMPLE = """# Rapport d'évaluation — 2026-11-17

Jeu de 24 factures, 2 répétitions.

## Résumé

| Variante | Factures parfaites |
|---|---|
| haiku | 87,5 % |
| haiku-v2 | 100,0 % |

## Exactitude par champ

Une seule ligne de commentaire.

| Champ | haiku |
|---|---|
| Date | 87,5 % |
"""


@pytest.fixture
def reports_dir(tmp_path):
    (tmp_path / "2026-11-17-prompt-v2.md").write_text(SAMPLE, encoding="utf-8")
    (tmp_path / "2026-11-18-search.md").write_text("# Recherche\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("pas un rapport", encoding="utf-8")
    return tmp_path


def test_list_returns_markdown_reports_newest_first(reports_dir):
    summaries = ReportLibrary(reports_dir).list()

    assert [s.id for s in summaries] == ["2026-11-18-search", "2026-11-17-prompt-v2"]


def test_summary_carries_the_title_and_the_date_of_the_file_name(reports_dir):
    summaries = ReportLibrary(reports_dir).list()

    assert summaries[1].title == "Rapport d'évaluation — 2026-11-17"
    assert summaries[1].date == date(2026, 11, 17)


def test_list_of_a_missing_directory_is_empty(tmp_path):
    assert ReportLibrary(tmp_path / "absent").list() == []


def test_get_parses_the_intro_and_the_sections(reports_dir):
    report = ReportLibrary(reports_dir).get("2026-11-17-prompt-v2")

    assert report.intro == "Jeu de 24 factures, 2 répétitions."
    assert [s.title for s in report.sections] == ["Résumé", "Exactitude par champ"]


def test_get_parses_a_table_into_headers_and_rows(reports_dir):
    report = ReportLibrary(reports_dir).get("2026-11-17-prompt-v2")

    table = report.sections[0].tables[0]
    assert table.headers == ["Variante", "Factures parfaites"]
    assert table.rows == [["haiku", "87,5 %"], ["haiku-v2", "100,0 %"]]


def test_get_keeps_the_text_around_a_table(reports_dir):
    section = ReportLibrary(reports_dir).get("2026-11-17-prompt-v2").sections[1]

    assert section.paragraphs == ["Une seule ligne de commentaire."]
    assert len(section.tables) == 1


@pytest.mark.parametrize("report_id", ["inconnu", "../secret", "..%2Fsecret", "notes", ""])
def test_get_rejects_an_id_that_is_not_a_listed_report(reports_dir, report_id):
    with pytest.raises(UnknownReportError):
        ReportLibrary(reports_dir).get(report_id)
