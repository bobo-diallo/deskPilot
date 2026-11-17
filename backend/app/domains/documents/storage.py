from pathlib import Path

_EXTENSIONS = {"application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg"}


class FileStorage:
    """Range les fichiers déposés dans un dossier, sous le nom `<id du document>.<extension>`."""

    def __init__(self, base_dir: Path):
        self._base_dir = Path(base_dir)

    def _path(self, document_id: int, media_type: str) -> Path:
        extension = _EXTENSIONS.get(media_type)
        if extension is None:
            raise ValueError(f"Type de fichier non pris en charge : {media_type}")
        return self._base_dir / f"{document_id}{extension}"

    def save(self, document_id: int, media_type: str, content: bytes) -> Path:
        path = self._path(document_id, media_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def read(self, document_id: int, media_type: str) -> bytes:
        return self._path(document_id, media_type).read_bytes()
