# Début (« signature ») de chaque type de fichier accepté.
_SIGNATURES: list[tuple[bytes, str]] = [
    (b"%PDF-", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    # Audio
    (b"ID3", "audio/mpeg"),  # MP3 avec étiquettes
    (b"\xff\xfb", "audio/mpeg"),  # MP3 brut (trame MPEG, couche III)
    (b"\xff\xf3", "audio/mpeg"),
    (b"\xff\xf2", "audio/mpeg"),
    (b"OggS", "audio/ogg"),
    (b"\x1a\x45\xdf\xa3", "audio/webm"),  # conteneur Matroska/WebM
]

AUDIO_PREFIX = "audio/"


def is_audio(media_type: str) -> bool:
    return media_type.startswith(AUDIO_PREFIX)


def detect_media_type(content: bytes) -> str | None:
    """Devine le vrai type d'un fichier d'après ses premiers octets.

    On ne fait pas confiance au nom ni au type déclaré par le client : ils peuvent mentir.
    """
    for signature, media_type in _SIGNATURES:
        if content.startswith(signature):
            return media_type
    # Certains formats ont leur marque plus loin que le début du fichier.
    # WAV : « RIFF », 4 octets de taille, puis « WAVE » (un AVI commence aussi par RIFF).
    if content[:4] == b"RIFF" and content[8:12] == b"WAVE":
        return "audio/wav"
    # M4A / MP4 : « ftyp » à partir du 5e octet.
    if content[4:8] == b"ftyp":
        return "audio/mp4"
    return None
