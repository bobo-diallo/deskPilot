import io

from app.domains.transcription.errors import TranscriptionError
from app.domains.transcription.schemas import Transcript


class FasterWhisperTranscriber:
    """Transcrit l'audio avec Whisper, en local, sur le processeur (aucun coût par appel).

    Le modèle (quelques dizaines à quelques centaines de Mo selon la taille) se télécharge
    au premier usage depuis Hugging Face, sans jeton, puis reste en cache sur la machine.
    """

    def __init__(self, model_size: str = "base", *, model=None):
        self._model_size = model_size
        self._model = model  # injectable pour les tests ; sinon chargé au premier appel

    def _load_model(self):
        if self._model is None:
            # Import ici : on ne charge la bibliothèque (lourde) que si on transcrit vraiment
            from faster_whisper import WhisperModel

            # int8 : poids compressés, rapide sur processeur et sans perte notable
            self._model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
        return self._model

    def transcribe(self, content: bytes, language: str | None = None) -> Transcript:
        try:
            model = self._load_model()
            segments, info = model.transcribe(io.BytesIO(content), language=language)
            # `segments` est un générateur : le calcul se fait pendant qu'on le parcourt
            text = " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as error:
            raise TranscriptionError(str(error)) from error
        return Transcript(
            text=text,
            language=info.language,
            duration_seconds=info.duration,
            model=f"faster-whisper-{self._model_size}",
        )
