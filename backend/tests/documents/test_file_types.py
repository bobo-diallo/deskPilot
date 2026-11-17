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
