import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptSet:
    """Les versions d'un même prompt (extraction, agent…), traitées comme du code.

    Une version publiée ne se modifie jamais : on en ajoute une nouvelle, on la mesure avec
    l'évaluation, puis on change le défaut. L'empreinte (`fingerprint`) permet de détecter
    qu'un texte a changé en place (voir `tests/test_prompt_lock.py`).
    """

    name: str
    versions: dict[str, str]
    default: str

    def __post_init__(self):
        if self.default not in self.versions:
            raise ValueError(f"Version par défaut inconnue : {self.default}")

    def get(self, version: str) -> str:
        try:
            return self.versions[version]
        except KeyError:
            raise ValueError(f"Version de prompt inconnue : {version}") from None

    def fingerprint(self, version: str) -> str:
        """8 premiers caractères du SHA-256 du texte : change dès qu'un caractère change."""
        return hashlib.sha256(self.get(version).encode("utf-8")).hexdigest()[:8]
