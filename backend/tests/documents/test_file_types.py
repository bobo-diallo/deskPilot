import pytest

from app.domains.documents.file_types import detect_media_type


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (b"%PDF-1.7 ...", "application/pdf"),
        (b"\x89PNG\r\n\x1a\n....", "image/png"),
        (b"\xff\xd8\xff\xe0....", "image/jpeg"),
        (b"just some text", None),
        (b"", None),
    ],
)
def test_media_type_is_detected_from_the_first_bytes(content, expected):
    assert detect_media_type(content) == expected


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (b"RIFF\x24\x08\x00\x00WAVEfmt ", "audio/wav"),
        (b"ID3\x04\x00\x00....", "audio/mpeg"),
        (b"\xff\xfb\x90\x00....", "audio/mpeg"),
        (b"OggS\x00\x02....", "audio/ogg"),
        (b"\x1a\x45\xdf\xa3....", "audio/webm"),
        (b"\x00\x00\x00\x20ftypM4A \x00\x00", "audio/mp4"),
    ],
)
def test_audio_media_type_is_detected_from_the_first_bytes(content, expected):
    assert detect_media_type(content) == expected


def test_a_riff_file_that_is_not_wave_is_rejected():
    # Un AVI commence aussi par RIFF : seul « WAVE » à l'offset 8 identifie un son
    assert detect_media_type(b"RIFF\x24\x08\x00\x00AVI LIST") is None


def test_is_audio_only_accepts_audio_types():
    from app.domains.documents.file_types import is_audio

    assert is_audio("audio/wav")
    assert not is_audio("application/pdf")
