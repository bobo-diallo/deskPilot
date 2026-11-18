import math
import zlib

from app.domains.search.keyword import tokenize

DIMENSIONS = 64


class FakeEmbedder:
    """Embedder factice : « sac de mots » haché en 64 dimensions. Rapide, sans modèle ni réseau.

    Il ne comprend pas le sens (deux synonymes n'ont rien en commun) mais il est déterministe
    et deux textes qui partagent des mots ont des vecteurs proches : suffisant pour les tests.
    """

    model_name = "fake"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    @staticmethod
    def _vector(text: str) -> list[float]:
        vector = [0.0] * DIMENSIONS
        for word in tokenize(text):
            vector[zlib.crc32(word.encode()) % DIMENSIONS] += 1.0
        norm = math.sqrt(sum(x * x for x in vector))
        return [x / norm for x in vector] if norm else vector
