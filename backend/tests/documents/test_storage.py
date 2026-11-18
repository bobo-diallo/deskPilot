import pytest

from app.domains.documents.storage import FileStorage


def test_a_saved_file_can_be_read_back(tmp_path):
    storage = FileStorage(tmp_path / "uploads")

    storage.save(7, "application/pdf", b"%PDF-1")

    assert storage.read(7, "application/pdf") == b"%PDF-1"
    assert (tmp_path / "uploads" / "7.pdf").exists()


def test_extension_follows_the_media_type(tmp_path):
    storage = FileStorage(tmp_path)

    storage.save(1, "image/png", b"x")
    storage.save(2, "image/jpeg", b"x")

    assert (tmp_path / "1.png").exists()
    assert (tmp_path / "2.jpg").exists()


def test_unknown_media_type_is_refused(tmp_path):
    with pytest.raises(ValueError, match="text/csv"):
        FileStorage(tmp_path).save(1, "text/csv", b"a,b")


@pytest.mark.parametrize(
    ("media_type", "extension"),
    [
        ("audio/wav", ".wav"),
        ("audio/mpeg", ".mp3"),
        ("audio/ogg", ".ogg"),
        ("audio/webm", ".webm"),
        ("audio/mp4", ".m4a"),
    ],
)
def test_audio_files_are_stored_with_their_extension(tmp_path, media_type, extension):
    path = FileStorage(tmp_path).save(7, media_type, b"son")

    assert path.name == f"7{extension}"
