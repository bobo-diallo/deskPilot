from app.domains.transcription.transcribers.fake import FakeTranscriber


def test_fake_transcriber_returns_the_configured_text_and_records_the_audio():
    transcriber = FakeTranscriber(text="Facture numéro 12", language="fr", duration_seconds=4.5)

    transcript = transcriber.transcribe(b"audio-bytes", language="fr")

    assert transcript.text == "Facture numéro 12"
    assert transcript.language == "fr"
    assert transcript.duration_seconds == 4.5
    assert transcript.model == "fake"
    assert transcriber.received == [b"audio-bytes"]
