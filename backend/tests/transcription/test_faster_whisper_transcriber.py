import io
import wave
from types import SimpleNamespace

import pytest

from app.domains.transcription.errors import TranscriptionError
from app.domains.transcription.transcribers.faster_whisper import FasterWhisperTranscriber


class StubWhisperModel:
    """Imite WhisperModel : renvoie des segments et des informations, sans modèle réel."""

    def __init__(self, texts, language="fr", duration=3.0, fail=False):
        self._texts = texts
        self._info = SimpleNamespace(language=language, duration=duration)
        self._fail = fail
        self.calls: list[dict] = []

    def transcribe(self, audio, **options):
        if self._fail:
            raise RuntimeError("décodage impossible")
        self.calls.append({"audio": audio, **options})
        # Comme le vrai modèle, on renvoie un générateur de segments
        return (SimpleNamespace(text=text) for text in self._texts), self._info


def test_segments_are_joined_into_one_text_with_language_and_duration():
    model = StubWhisperModel([" Facture Tremblay,", " total 120 euros "], duration=6.2)
    transcriber = FasterWhisperTranscriber("base", model=model)

    transcript = transcriber.transcribe(b"fake-audio", language="fr")

    assert transcript.text == "Facture Tremblay, total 120 euros"
    assert transcript.language == "fr"
    assert transcript.duration_seconds == 6.2
    assert transcript.model == "faster-whisper-base"
    # La langue demandée est transmise : plus fiable que la détection automatique
    assert model.calls[0]["language"] == "fr"


def test_the_audio_is_given_to_the_model_as_a_file_like_object():
    model = StubWhisperModel(["ok"])
    FasterWhisperTranscriber("base", model=model).transcribe(b"abc")

    assert model.calls[0]["audio"].read() == b"abc"


def test_a_model_failure_becomes_a_transcription_error():
    transcriber = FasterWhisperTranscriber("base", model=StubWhisperModel([], fail=True))

    with pytest.raises(TranscriptionError, match="décodage impossible"):
        transcriber.transcribe(b"corrompu")


def _silent_wav(seconds: float = 1.0) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * int(16000 * seconds))
    return buffer.getvalue()


def _tiny_model_is_cached() -> bool:
    try:
        from faster_whisper.utils import download_model

        download_model("tiny", local_files_only=True)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _tiny_model_is_cached(), reason="Modèle Whisper « tiny » non téléchargé")
def test_real_whisper_decodes_a_wav_file():
    transcript = FasterWhisperTranscriber("tiny").transcribe(_silent_wav(1.0), language="fr")

    assert transcript.duration_seconds == pytest.approx(1.0, abs=0.1)
    assert transcript.model == "faster-whisper-tiny"
