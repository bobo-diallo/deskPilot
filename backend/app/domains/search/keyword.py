"""Recherche par mots-clés (BM25), en Python pur : aucune dépendance, aucun modèle.

BM25 note chaque morceau selon les mots de la question qu'il contient, en donnant plus de poids
aux mots rares (« exclusivité ») qu'aux mots courants (« contrat »). C'est l'algorithme des
moteurs de recherche classiques (Elasticsearch, Lucene) : un bon point de départ, difficile à battre
sur les mots exacts, noms propres et chiffres.
"""

import math
import re
import unicodedata
from collections import Counter

# Mots très fréquents qui n'aident pas à distinguer deux morceaux.
STOPWORDS = frozenset(
    "le la les l un une des du de d et ou a au aux en dans pour par sur sous que qui est sont "
    "ce se sa son ses leur leurs il elle ils elles on ne pas plus ou où y à être avoir".split()
)
# Réglages standard de BM25 (valeurs usuelles de la littérature, non réglées sur nos données).
K1 = 1.5
B = 0.75


def _fold(text: str) -> str:
    """Minuscules et accents retirés : « Préavis » et « PREAVIS » deviennent « preavis »."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", _fold(text))
    return [word for word in words if word not in STOPWORDS]


class BM25Index:
    """Index en mémoire d'une liste de textes ; les résultats sont des positions dans la liste."""

    def __init__(self, documents: list[str]):
        self._counts = [Counter(tokenize(document)) for document in documents]
        self._lengths = [sum(counts.values()) for counts in self._counts]
        self._average_length = sum(self._lengths) / len(documents) if documents else 0.0
        frequency: Counter[str] = Counter()
        for counts in self._counts:
            frequency.update(counts.keys())  # nombre de documents contenant chaque mot
        total = len(documents)
        self._idf = {
            word: math.log(1 + (total - n + 0.5) / (n + 0.5)) for word, n in frequency.items()
        }

    def search(self, query: str, k: int = 5) -> list[tuple[int, float]]:
        """Les k meilleurs morceaux (position, score), du plus au moins pertinent."""
        words = [word for word in tokenize(query) if word in self._idf]
        scored = []
        for position, counts in enumerate(self._counts):
            score = 0.0
            for word in words:
                occurrences = counts.get(word, 0)
                if occurrences:
                    length_ratio = self._lengths[position] / self._average_length
                    norm = occurrences + K1 * (1 - B + B * length_ratio)
                    score += self._idf[word] * occurrences * (K1 + 1) / norm
            if score > 0:
                scored.append((position, score))
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        return scored[:k]
