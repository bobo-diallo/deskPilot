import json
import shutil
import wave

import pytest

from app.domains.documents.file_types import detect_media_type
from app.evaluation.audio_render import add_noise, render_audio, write_audio_dataset
from app.evaluation.dataset import load_dataset
from app.evaluation.spoken import RecordingConditions, recording_conditions
from app.evaluation.synthetic import generate_cases


def fake_renderer(text, conditions, path):
    path.write_bytes(b"ID3" + text.encode("utf-8")[:20])  # contenu minimal reconnu comme MP3


def test_the_audio_dataset_can_be_loaded_like_the_document_dataset(tmp_path):
    write_audio_dataset(generate_cases(), tmp_path, count=12, renderer=fake_renderer)

    cases = load_dataset(tmp_path)

    assert len(cases) == 12
    assert {case.media_type for case in cases} == {"audio/mpeg"}
    assert all(case.spoken and case.spoken.startswith("Facture ") for case in cases)
    assert all(case.expected.supplier_name in case.spoken for case in cases)


def test_the_manifest_lists_audio_files_with_their_tags(tmp_path):
    write_audio_dataset(generate_cases(), tmp_path, count=12, renderer=fake_renderer)

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["cases"][0]["id"] == "aud-01"
    assert manifest["cases"][0]["file"] == "aud-01.mp3"
    assert "fast" in {tag for entry in manifest["cases"] for tag in entry["tags"]}


def test_the_renderer_receives_the_recording_conditions_of_each_case(tmp_path):
    received = []

    def spy(text, conditions, path):
        received.append(conditions)
        fake_renderer(text, conditions, path)

    write_audio_dataset(generate_cases(), tmp_path, count=12, renderer=spy)

    assert received == [recording_conditions(index) for index in range(12)]


def test_noise_changes_the_samples_but_keeps_the_format_and_is_reproducible(tmp_path):
    def silent_wav(name):
        path = tmp_path / name
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"\x00\x00" * 1600)
        return path

    first, second = silent_wav("a.wav"), silent_wav("b.wav")
    add_noise(first, amplitude=0.03, seed="x")
    add_noise(second, amplitude=0.03, seed="x")

    assert first.read_bytes() == second.read_bytes()  # même graine, même bruit
    with wave.open(str(first), "rb") as wav:
        assert (wav.getnchannels(), wav.getframerate(), wav.getnframes()) == (1, 16000, 1600)
        assert wav.readframes(1600) != b"\x00\x00" * 1600


@pytest.mark.skipif(
    not (shutil.which("say") and shutil.which("ffmpeg")),
    reason="Nécessite la commande macOS « say » et ffmpeg",
)
def test_real_rendering_produces_an_mp3_file(tmp_path):
    path = tmp_path / "bonjour.mp3"

    render_audio("Bonjour", RecordingConditions("Thomas", 175, 0.0), path)

    assert detect_media_type(path.read_bytes()) == "audio/mpeg"
