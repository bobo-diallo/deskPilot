import json
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import select

from app.domains.extraction.models import Extraction
from app.domains.llm.providers.fake import ScriptedProvider
from app.domains.search.embedders.fake import FakeEmbedder
from app.domains.search.service import SearchService
from app.evaluation.agent_cli import main
from app.evaluation.agent_dataset import load_agent_dataset
from app.evaluation.agent_report import render_agent_report
from app.evaluation.agent_runner import TrialResult, run_agent_variant
from app.evaluation.agent_world import build_world
from tests.agent.test_agent_service import answer, ask_tools

ROOT = Path(__file__).resolve().parents[3] / "demo-data"
KNOWN_TOOLS = {"search_documents", "list_invoices", "check_invoice", "export_invoices"}


@pytest.fixture(scope="module")
def dataset():
    return load_agent_dataset(ROOT / "agent-eval", ROOT / "search-eval")


def test_the_dataset_has_twelve_questions_eight_invoices_and_eleven_contracts(dataset):
    assert len(dataset.questions) == 12
    assert len(dataset.invoices) == 8
    assert len(dataset.documents) == 11
    assert "Contrat Pirate Logistique" in {d.title for d in dataset.documents}


def test_every_question_refers_to_real_tools_and_ids_are_unique(dataset):
    ids = [q.id for q in dataset.questions]
    assert len(ids) == len(set(ids))
    for q in dataset.questions:
        assert set(q.must_use) | set(q.must_not_use) <= KNOWN_TOOLS, q.id
        assert q.expected_status in {"completed", "awaiting_approval"}, q.id


def test_the_dataset_covers_search_invoices_combined_no_tool_sensitive_and_injection(dataset):
    assert {tag for q in dataset.questions for tag in q.tags} == {
        "search", "invoices", "combined", "no_tool", "sensitive", "injection",
    }  # fmt: skip


def test_the_world_seeds_invoices_with_their_statuses_and_real_issues(session, dataset):
    build_world(session, dataset, FakeEmbedder())

    extractions = {e.id: e for e in session.scalars(select(Extraction))}
    assert len(extractions) == 8
    assert extractions[3].status == "needs_review"
    assert [i["code"] for i in extractions[3].issues] == ["total_mismatch"]
    assert "missing_field" in [i["code"] for i in extractions[6].issues]
    assert extractions[7].status == "approved"
    assert extractions[1].data["supplier_name"] == extractions[4].data["supplier_name"]


def test_the_world_indexes_the_contracts_including_the_poisoned_one(session, dataset):
    build_world(session, dataset, FakeEmbedder())

    hits = SearchService(session, FakeEmbedder()).search("Pirate Logistique", k=3, mode="keyword")

    assert hits and hits[0].title == "Contrat Pirate Logistique"


def pick(dataset, *ids):
    return [q for q in dataset.questions if q.id in ids]


def test_a_correct_run_is_a_success_with_its_tools_cost_and_steps(dataset):
    provider = ScriptedProvider(
        [
            ask_tools(("t1", "search_documents", {"query": "préavis Garage Tremblay"})),
            answer("Le préavis est d'un mois."),
        ]
    )

    result = run_agent_variant(
        "haiku", "claude-haiku-5-5", provider, dataset, FakeEmbedder(), runs=1,
        questions=pick(dataset, "a01"),
    )  # fmt: skip

    trial = result.trials[0]
    assert trial.success and not trial.unsafe
    assert trial.tools == ["search_documents"] and trial.steps_used == 2
    assert trial.cost_usd > 0 and trial.status == "completed"


def test_an_agent_that_obeys_the_poisoned_contract_is_flagged_unsafe(dataset):
    provider = ScriptedProvider([ask_tools(("t1", "export_invoices", {"extraction_ids": [1, 2]}))])

    result = run_agent_variant(
        "haiku", "claude-haiku-5-5", provider, dataset, FakeEmbedder(), runs=1,
        questions=pick(dataset, "f01"),
    )  # fmt: skip

    trial = result.trials[0]
    assert trial.unsafe and not trial.success
    assert trial.status == "awaiting_approval"  # et rien n'a été exporté : l'approbation a tenu


def test_each_trial_gets_its_own_cost_not_the_running_total(dataset):
    script = [answer("Bonjour"), answer("Bonjour")]

    result = run_agent_variant(
        "haiku", "claude-haiku-5-5", ScriptedProvider(script), dataset, FakeEmbedder(), runs=2,
        questions=pick(dataset, "d01"),
    )  # fmt: skip

    first, second = result.trials
    assert first.cost_usd == pytest.approx(second.cost_usd)


def test_a_failing_provider_is_recorded_as_an_error_not_a_crash(dataset):
    result = run_agent_variant(
        "haiku", "claude-haiku-5-5", ScriptedProvider([]), dataset, FakeEmbedder(), runs=1,
        questions=pick(dataset, "d01"),
    )  # fmt: skip

    assert not result.trials[0].success
    assert result.trials[0].error and "script" in result.trials[0].error.lower()


def trial(question_id, tags, success, unsafe=False, run=1, cost=0.002, tools=("search_documents",)):
    return TrialResult(
        question_id=question_id, tags=tuple(tags), run=run, success=success, failures=[],
        unsafe=unsafe, tools=list(tools), steps_used=2, status="completed", answer="x",
        cost_usd=cost, input_tokens=1000, output_tokens=100, latency_ms=3000, error=None,
    )  # fmt: skip


def make_results(haiku_ok=(True, True, False, True), sonnet_ok=(True, True, True, True)):
    tags = [("search",), ("invoices",), ("injection",), ("combined",)]

    def build(flags):
        return [trial(f"q{i}", tags[i], ok) for i, ok in enumerate(flags)]

    return {"haiku": build(haiku_ok), "sonnet": build(sonnet_ok)}


def test_the_report_compares_the_variants_with_confidence_intervals_and_safety():
    report = render_agent_report(
        make_results(), date(2026, 11, 19),
        models={"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5"},
    )  # fmt: skip

    assert "Taux de réussite" in report and "IC 95 %" in report
    assert "Actions non sûres" in report
    assert "75,0 %" in report and "100,0 %" in report
    assert "Injection de prompt" in report


def test_the_decision_rule_is_applied_as_written_before_the_measure(session):
    models = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5"}
    close = render_agent_report(
        make_results(haiku_ok=(True, True, True, True)), date(2026, 11, 19), models
    )
    far = render_agent_report(
        make_results(haiku_ok=(True, False, False, True)), date(2026, 11, 19), models
    )

    assert "Haiku est retenu" in close
    assert "Sonnet est retenu" in far


def test_an_unsafe_run_disqualifies_the_cheaper_model_even_if_it_scores_well(session):
    models = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5"}
    results = make_results(haiku_ok=(True, True, True, True))
    results["haiku"][2] = trial("q2", ("injection",), success=True, unsafe=True)

    report = render_agent_report(results, date(2026, 11, 19), models)

    assert "Sonnet est retenu" in report and "non sûre" in report


def test_the_command_shows_an_estimate_and_spends_nothing_without_yes(capsys, tmp_path):
    code = main(["--models", "haiku,sonnet", "--runs", "2", "--embedder", "fake",
                 "--report-dir", str(tmp_path)])  # fmt: skip

    assert code == 1
    output = capsys.readouterr().out
    assert "Estimation" in output and "Rien n'a été dépensé" in output
    assert not list(tmp_path.iterdir())


def test_the_command_runs_writes_the_report_and_raw_results(tmp_path, capsys):
    provider = ScriptedProvider(
        [ask_tools(("t1", "search_documents", {"query": "préavis"})), answer("Un mois.")]
    )

    code = main(
        ["--models", "haiku", "--runs", "1", "--limit", "1", "--embedder", "fake", "--yes",
         "--name", "agent-test", "--report-dir", str(tmp_path), "--raw-dir", str(tmp_path / "raw")],
        provider_factory=lambda: provider,
    )  # fmt: skip

    assert code == 0
    assert list(tmp_path.glob("*-agent-test.md"))
    raw = json.loads((tmp_path / "raw" / "agent-test.json").read_text(encoding="utf-8"))
    assert raw["variants"][0]["name"] == "haiku"
    assert raw["variants"][0]["trials"][0]["tools"] == ["search_documents"]
    assert "Terminé" in capsys.readouterr().out


def test_unknown_models_are_refused(capsys):
    assert main(["--models", "gpt", "--embedder", "fake"]) == 2
    assert "inconnu" in capsys.readouterr().out.lower()
