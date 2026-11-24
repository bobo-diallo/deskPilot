from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select

from app.domains.extraction.errors import ExtractionError
from app.domains.extraction.extractors.claude import ClaudeExtractor
from app.domains.extraction.ports import ExtractionOutput
from app.domains.extraction.schemas import Invoice, InvoiceLine
from app.domains.llm.models import ApiCall
from app.domains.llm.providers.fake import FakeProvider
from app.domains.llm.service import LLMService
from app.evaluation.dataset import load_dataset
from app.evaluation.runner import run_variant

DATASET_DIR = Path(__file__).resolve().parents[3] / "demo-data" / "eval"


def make_invoice(total: str = "30.00") -> Invoice:
    return Invoice(
        supplier_name="Atelier Nord",
        invoice_number="2026-014",
        issue_date=date(2026, 11, 12),
        currency="EUR",
        lines=[
            InvoiceLine(
                description="Chaise",
                quantity=Decimal("2"),
                unit_price=Decimal("10.00"),
                total=Decimal("20.00"),
            ),
            InvoiceLine(
                description="Livraison",
                quantity=Decimal("1"),
                unit_price=Decimal("5.00"),
                total=Decimal("5.00"),
            ),
        ],
        subtotal=Decimal("25.00"),
        tax_amount=Decimal("5.00"),
        total=Decimal(total),
    )


def write_case(directory: Path, case_id: str, tags: list[str], invoice: Invoice) -> None:
    import json

    (directory / f"{case_id}.pdf").write_bytes(b"%PDF-1.4 " + case_id.encode())
    (directory / f"{case_id}.expected.json").write_text(invoice.model_dump_json())
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"cases": []}
    manifest["cases"].append({"id": case_id, "file": f"{case_id}.pdf", "tags": tags})
    manifest_path.write_text(json.dumps(manifest))


@pytest.fixture
def small_dataset(tmp_path) -> Path:
    write_case(tmp_path, "a", ["digital"], make_invoice())
    write_case(tmp_path, "b", ["scan"], make_invoice())
    return tmp_path


# --- chargeur ---------------------------------------------------------------------------------


def test_the_committed_dataset_loads_completely():
    cases = load_dataset(DATASET_DIR)

    assert len(cases) == 24
    assert all(case.path.exists() for case in cases)
    assert {case.media_type for case in cases} == {"application/pdf", "image/png", "image/jpeg"}


def test_loader_reads_expected_values_tags_and_media_type(small_dataset):
    first, second = load_dataset(small_dataset)

    assert (first.case_id, first.tags, first.media_type) == ("a", ("digital",), "application/pdf")
    assert first.expected == make_invoice()
    assert second.case_id == "b"


# --- ClaudeExtractor : modèle imposé ----------------------------------------------------------


def test_extractor_can_force_a_model_instead_of_using_the_router(session):
    provider = FakeProvider(parsed=make_invoice())
    extractor = ClaudeExtractor(LLMService(provider, session), model="claude-haiku-5-5")

    extractor.extract(b"%PDF-1", "application/pdf")

    assert provider.received[0].model == "claude-haiku-5-5"


# --- exécution d'une variante -----------------------------------------------------------------


def test_runner_runs_every_case_the_requested_number_of_times(small_dataset, session):
    provider = FakeProvider(parsed=make_invoice())
    extractor = ClaudeExtractor(LLMService(provider, session))

    result = run_variant("test", extractor, load_dataset(small_dataset), session, runs=3)

    assert len(result.trials) == 6
    assert {(t.case_id, t.run) for t in result.trials} == {
        (case, run) for case in ("a", "b") for run in (1, 2, 3)
    }


def test_runner_scores_each_trial_against_the_ground_truth(small_dataset, session):
    provider = FakeProvider(parsed=make_invoice(total="99.00"))  # le modèle se trompe
    extractor = ClaudeExtractor(LLMService(provider, session))

    result = run_variant("test", extractor, load_dataset(small_dataset), session, runs=1)

    assert all(not trial.score.perfect for trial in result.trials)
    assert all(trial.score.fields["total"] is False for trial in result.trials)
    # 99 ≠ 25 + 5 : la validation signale l'incohérence.
    assert all(trial.score.status == "needs_review" for trial in result.trials)


def test_runner_collects_tokens_and_cost_from_the_journal(small_dataset, session):
    provider = FakeProvider(parsed=make_invoice(), input_tokens=1_000, output_tokens=500)
    extractor = ClaudeExtractor(LLMService(provider, session))

    result = run_variant("test", extractor, load_dataset(small_dataset), session, runs=1)

    for trial in result.trials:
        assert (trial.input_tokens, trial.output_tokens) == (1_000, 500)
        assert trial.cost_usd == pytest.approx(0.00035)  # modèle du routeur : Haiku
        assert trial.latency_ms >= 0
    assert len(session.scalars(select(ApiCall)).all()) == 2


def test_runner_records_a_failure_and_keeps_going(small_dataset, session):
    class FlakyExtractor:
        def __init__(self):
            self.calls = 0

        def extract(self, content, media_type):
            self.calls += 1
            if self.calls == 1:
                raise ExtractionError("réponse inexploitable")
            return ExtractionOutput(data=make_invoice(), model="x")

    result = run_variant("test", FlakyExtractor(), load_dataset(small_dataset), session, runs=1)

    failed, ok = result.trials
    assert failed.score.failed and "inexploitable" in failed.error
    assert ok.score.perfect and ok.error is None


def test_the_spoken_reference_is_loaded_when_the_dataset_has_one(tmp_path):
    write_case(tmp_path, "a", ["fast"], make_invoice())
    (tmp_path / "a.spoken.txt").write_text("Facture Atelier Nord", encoding="utf-8")

    assert load_dataset(tmp_path)[0].spoken == "Facture Atelier Nord"


def test_a_dataset_without_spoken_reference_has_none(small_dataset):
    assert load_dataset(small_dataset)[0].spoken is None


def test_the_runner_measures_the_word_error_rate_and_the_audio_duration(tmp_path, session):
    from app.domains.extraction.ports import ExtractionOutput
    from app.domains.transcription.schemas import Transcript

    write_case(tmp_path, "a", ["fast"], make_invoice())
    (tmp_path / "a.spoken.txt").write_text("facture atelier nord", encoding="utf-8")

    class SpeakingExtractor:
        def extract(self, content, media_type):
            transcript = Transcript(
                text="facture atelier sud", language="fr", duration_seconds=8.0, model="m"
            )
            return ExtractionOutput(data=make_invoice(), model="m", transcript=transcript)

    result = run_variant("v", SpeakingExtractor(), load_dataset(tmp_path), session, runs=1)

    trial = result.trials[0]
    assert trial.word_error_rate == pytest.approx(1 / 3)
    assert trial.audio_seconds == 8.0


def test_a_document_trial_has_no_word_error_rate(small_dataset, session):
    provider = FakeProvider(parsed=make_invoice())
    extractor = ClaudeExtractor(LLMService(provider, session))

    result = run_variant("v", extractor, load_dataset(small_dataset), session, runs=1)

    assert result.trials[0].word_error_rate is None
    assert result.trials[0].audio_seconds is None


def test_runner_remembers_the_prompt_version_the_extractor_reported(small_dataset, session):
    provider = FakeProvider(parsed=make_invoice())
    extractor = ClaudeExtractor(LLMService(provider, session), prompt_version="v1")

    result = run_variant("test", extractor, load_dataset(small_dataset), session, runs=1)

    assert result.prompt_version == "v1"


def test_runner_leaves_the_prompt_version_empty_when_the_extractor_gives_none(
    small_dataset, session
):
    class NoPrompt:
        def extract(self, content, media_type):
            return ExtractionOutput(data=make_invoice(), model="x")

    result = run_variant("test", NoPrompt(), load_dataset(small_dataset), session, runs=1)

    assert result.prompt_version is None
