import json
from datetime import date
from pathlib import Path

import pytest

from app.domains.search.embedders.fake import FakeEmbedder
from app.evaluation.search_cli import main
from app.evaluation.search_dataset import load_search_dataset
from app.evaluation.search_metrics import _fold
from app.evaluation.search_report import render_search_report
from app.evaluation.search_runner import MODES, run_search_eval

DATASET_DIR = Path(__file__).resolve().parents[3] / "demo-data" / "search-eval"


@pytest.fixture(scope="module")
def dataset():
    return load_search_dataset(DATASET_DIR)


def test_the_dataset_has_ten_contracts_and_twenty_four_questions(dataset):
    assert len(dataset.documents) == 10
    assert len(dataset.questions) == 24
    assert {tag for q in dataset.questions for tag in q.tags} == {
        "name_lookup",
        "numeric",
        "paraphrase",
        "cross_doc",
    }


def test_every_expected_answer_really_exists_in_its_contract(dataset):
    # Garde-fou contre une faute de frappe qui rendrait une question impossible à réussir
    texts = {document.title: _fold(document.text) for document in dataset.documents}
    for question in dataset.questions:
        assert question.expected_title in texts, question.id
        assert _fold(question.expected_phrase) in texts[question.expected_title], question.id


def test_question_ids_are_unique(dataset):
    ids = [question.id for question in dataset.questions]
    assert len(ids) == len(set(ids))


def test_each_mode_gets_one_rank_per_question(dataset):
    results = run_search_eval(dataset, FakeEmbedder())

    assert set(results) == set(MODES)
    for mode in MODES:
        assert len(results[mode]) == 24


def test_keyword_search_finds_most_questions_that_name_the_supplier(dataset):
    results = run_search_eval(dataset, FakeEmbedder())

    named = [r for r in results["keyword"] if "name_lookup" in r.tags]
    assert sum(1 for r in named if r.rank == 1) >= 4  # sur 6 : le nom du contrat est un bon indice


def test_the_report_compares_the_three_modes_with_recall_and_mrr(dataset):
    results = run_search_eval(dataset, FakeEmbedder())

    report = render_search_report(results, date(2026, 11, 19), embedder_name="fake")

    for mode in MODES:
        assert mode in report
    assert "Rappel@1" in report and "Rappel@3" in report and "MRR" in report
    assert "Paraphrase" in report and "Nom du fournisseur" in report
    assert "IC 95 %" in report  # comparaison appariée avec intervalle de confiance
    assert "voix" not in report  # pas de vocabulaire du rapport audio


def test_the_command_writes_the_report_and_raw_results(tmp_path, capsys):
    code = main(
        [
            "--embedder",
            "fake",
            "--dataset",
            str(DATASET_DIR),
            "--report-dir",
            str(tmp_path),
            "--raw-dir",
            str(tmp_path / "raw"),
            "--name",
            "search-test",
        ]
    )

    assert code == 0
    assert list(tmp_path.glob("*-search-test.md"))
    raw = json.loads((tmp_path / "raw" / "search-test.json").read_text(encoding="utf-8"))
    assert set(raw["modes"]) == set(MODES)
    assert "Terminé" in capsys.readouterr().out
