# Début (« signature ») de chaque type de fichier accepté.
_SIGNATURES: list[tuple[bytes, str]] = [
    (b"%PDF-", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
]


def detect_media_type(content: bytes) -> str | None:
    """Devine le vrai type d'un fichier d'après ses premiers octets.

    On ne fait pas confiance au nom ni au type déclaré par le client : ils peuvent mentir.
    """
    for signature, media_type in _SIGNATURES:
        if content.startswith(signature):
            return media_type
    return None
