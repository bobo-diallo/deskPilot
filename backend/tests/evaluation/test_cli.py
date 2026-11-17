import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.domains.extraction.schemas import Invoice, InvoiceLine
from app.domains.llm.providers.fake import FakeProvider
from app.evaluation.cli import main
from tests.evaluation.test_dataset_and_runner import write_case


def make_invoice() -> Invoice:
    return Invoice(
        supplier_name="Atelier Nord",
        invoice_number="1",
        issue_date=date(2026, 11, 12),
        currency="EUR",
        lines=[
            InvoiceLine(
                description="Chaise",
                quantity=Decimal("2"),
                unit_price=Decimal("10.00"),
                total=Decimal("20.00"),
            )
        ],
        subtotal=Decimal("20.00"),
        tax_amount=Decimal("4.00"),
        total=Decimal("24.00"),
    )


@pytest.fixture
def dataset(tmp_path) -> Path:
    directory = tmp_path / "dataset"
    directory.mkdir()
    write_case(directory, "a", ["digital"], make_invoice())
    write_case(directory, "b", ["scan"], make_invoice())
    return directory


def run_cli(dataset, tmp_path, provider, *extra):
    return main(
        [
            "--dataset", str(dataset),
            "--report-dir", str(tmp_path / "reports"),
            "--raw-dir", str(tmp_path / "raw"),
            "--name", "essai",
            *extra,
        ],
        provider_factory=lambda: provider,
    )  # fmt: skip


def test_without_yes_it_only_prints_an_estimate_and_spends_nothing(dataset, tmp_path, capsys):
    provider = FakeProvider(parsed=make_invoice())

    code = run_cli(dataset, tmp_path, provider, "--variants", "sonnet-vision", "--runs", "2")

    output = capsys.readouterr().out
    assert code == 1
    assert "Estimation" in output and "--yes" in output
    assert "4 appels" in output  # 2 cas x 2 répétitions x 1 variante
    assert provider.received == []


def test_with_yes_it_runs_every_trial_and_writes_a_report_and_raw_results(
    dataset, tmp_path, capsys
):
    provider = FakeProvider(parsed=make_invoice())

    code = run_cli(
        dataset, tmp_path, provider, "--variants", "sonnet-vision,haiku-vision", "--runs", "2",
        "--yes",
    )  # fmt: skip

    assert code == 0
    assert len(provider.received) == 8  # 2 cas x 2 répétitions x 2 variantes
    assert {r.model for r in provider.received} == {"claude-sonnet-5-5", "claude-haiku-5-5"}

    report = (tmp_path / "reports" / f"{date.today().isoformat()}-essai.md").read_text()
    assert "sonnet-vision" in report and "haiku-vision" in report

    raw = json.loads((tmp_path / "raw" / "essai.json").read_text())
    assert len(raw["variants"]) == 2
    assert len(raw["variants"][0]["trials"]) == 4


def test_limit_restricts_the_number_of_cases(dataset, tmp_path):
    provider = FakeProvider(parsed=make_invoice())

    run_cli(dataset, tmp_path, provider, "--variants", "haiku-vision", "--runs", "1",
            "--limit", "1", "--yes")  # fmt: skip

    assert len(provider.received) == 1


def test_an_unknown_variant_is_refused_before_any_call(dataset, tmp_path, capsys):
    provider = FakeProvider(parsed=make_invoice())

    code = run_cli(dataset, tmp_path, provider, "--variants", "inconnue", "--yes")

    assert code == 2
    assert "inconnue" in capsys.readouterr().out
    assert provider.received == []


def test_tags_keep_only_the_matching_cases(dataset, tmp_path):
    provider = FakeProvider(parsed=make_invoice())

    run_cli(dataset, tmp_path, provider, "--variants", "haiku-vision", "--runs", "1",
            "--tags", "scan", "--yes")  # fmt: skip

    assert len(provider.received) == 1  # seul le cas « b » est étiqueté « scan »


def test_text_variants_are_available_and_use_their_model(dataset, tmp_path):
    provider = FakeProvider(parsed=make_invoice())

    run_cli(dataset, tmp_path, provider, "--variants", "haiku-text", "--runs", "1", "--yes")

    # Les faux PDF du jeu de test n'ont pas de texte : l'extracteur refuse avant tout appel.
    assert provider.received == []
    raw = json.loads((tmp_path / "raw" / "essai.json").read_text())
    assert all(t["error"] for t in raw["variants"][0]["trials"])
