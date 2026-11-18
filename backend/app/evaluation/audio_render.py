"""Fabrique les enregistrements du jeu d'évaluation audio, et écrit le jeu sur disque.

Utilise la synthèse vocale de macOS (`say`) et `ffmpeg` : ce module ne sert qu'à fabriquer
le jeu, jamais à l'application. Les fichiers sont des MP3 à 32 kbit/s (environ 100 Ko chacun),
assez légers pour être versionnés, et proches de ce qu'un utilisateur enverrait vraiment.
"""

import array
import json
import random
import subprocess
import tempfile
import wave
from collections.abc import Callable
from pathlib import Path

from app.evaluation.spoken import (
    RecordingConditions,
    audio_tags,
    recording_conditions,
    select_audio_cases,
    spoken_text,
)
from app.evaluation.synthetic import EvalCase

Renderer = Callable[[str, RecordingConditions, Path], None]


def add_noise(wav_path: Path, amplitude: float, seed: str) -> None:
    """Ajoute un bruit blanc (gaussien) à un fichier WAV 16 bits, de façon reproductible."""
    with wave.open(str(wav_path), "rb") as source:
        params = source.getparams()
        samples = array.array("h", source.readframes(source.getnframes()))
    rng = random.Random(seed)
    sigma = amplitude * 32767
    noisy = array.array(
        "h", (max(-32768, min(32767, round(s + rng.gauss(0, sigma)))) for s in samples)
    )
    with wave.open(str(wav_path), "wb") as target:
        target.setparams(params)
        target.writeframes(noisy.tobytes())


def render_audio(text: str, conditions: RecordingConditions, path: Path) -> None:
    """Lit `text` à voix haute (`say`), convertit en WAV 16 kHz mono, bruite, puis encode en MP3."""
    with tempfile.TemporaryDirectory() as temp:
        voice_file, wav_file = Path(temp) / "voice.aiff", Path(temp) / "voice.wav"
        subprocess.run(
            ["say", "-v", conditions.voice, "-r", str(conditions.words_per_minute),
             "-o", str(voice_file), "-f", "-"],
            input=text.encode("utf-8"), check=True,
        )  # fmt: skip
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", str(voice_file),
             "-ar", "16000", "-ac", "1", str(wav_file)],
            check=True,
        )  # fmt: skip
        if conditions.noise_amplitude > 0:
            add_noise(wav_file, conditions.noise_amplitude, seed=path.stem)
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav_file),
             "-codec:a", "libmp3lame", "-b:a", "32k", str(path)],
            check=True,
        )  # fmt: skip


def write_audio_dataset(
    cases: list[EvalCase], directory: Path, count: int = 12, renderer: Renderer = render_audio
) -> None:
    """Écrit pour chaque cas : le MP3, `<id>.expected.json`, `<id>.spoken.txt` et le manifeste."""
    directory.mkdir(parents=True, exist_ok=True)
    entries = []
    for index, case in enumerate(select_audio_cases(cases, count)):
        case_id = f"aud-{index + 1:02d}"
        text = spoken_text(case.invoice)
        renderer(text, recording_conditions(index), directory / f"{case_id}.mp3")
        (directory / f"{case_id}.spoken.txt").write_text(text + "\n", encoding="utf-8")
        (directory / f"{case_id}.expected.json").write_text(
            json.dumps(case.invoice.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        entries.append(
            {"id": case_id, "file": f"{case_id}.mp3", "tags": list(audio_tags(index, case))}
        )
    (directory / "manifest.json").write_text(
        json.dumps({"cases": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
