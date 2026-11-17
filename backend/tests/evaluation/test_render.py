import json

import pytest

from app.domains.documents.file_types import detect_media_type
from app.domains.extraction.schemas import Invoice
from app.evaluation.render import render_case, write_dataset
from app.evaluation.synthetic import generate_cases

EXPECTED_MEDIA = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg"}


@pytest.fixture(scope="module")
def cases():
    return generate_cases()


@pytest.mark.parametrize("medium", ["pdf", "png", "jpg"])
def test_each_medium_produces_a_file_of_the_right_type(cases, tmp_path, medium):
    case = next(c for c in cases if c.medium == medium)

    path = render_case(case, tmp_path)

    assert path.suffix == f".{medium}"
    assert detect_media_type(path.read_bytes()) == EXPECTED_MEDIA[medium]


def test_rendering_is_deterministic(cases, tmp_path):
    case = next(c for c in cases if c.medium == "jpg")

    first = render_case(case, tmp_path / "a").read_bytes()
    second = render_case(case, tmp_path / "b").read_bytes()

    assert first == second


def test_write_dataset_creates_files_expected_values_and_a_manifest(cases, tmp_path):
    write_dataset(cases, tmp_path)

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert len(manifest["cases"]) == len(cases)
    for entry, case in zip(manifest["cases"], cases, strict=True):
        assert entry["id"] == case.case_id
        assert entry["tags"] == list(case.tags)
        assert (tmp_path / entry["file"]).exists()
        expected = Invoice.model_validate_json(
            (tmp_path / f"{case.case_id}.expected.json").read_text()
        )
        assert expected == case.invoice
