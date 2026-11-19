import numpy as np
import pytest

from app.domains.search.embedders.fastembed_embedder import (
    CACHE_DIR,
    DEFAULT_MODEL,
    FastEmbedEmbedder,
)


class StubTextEmbedding:
    """Imite fastembed.TextEmbedding : un générateur de tableaux NumPy."""

    def embed(self, texts):
        return (np.array([float(len(text)), 1.0], dtype=np.float32) for text in texts)


def test_vectors_are_returned_as_plain_python_lists_ready_for_json():
    embedder = FastEmbedEmbedder(model=StubTextEmbedding())

    vectors = embedder.embed(["abc", "de"])

    assert vectors == [[3.0, 1.0], [2.0, 1.0]]
    assert all(type(x) is float for vector in vectors for x in vector)


def test_the_model_name_is_exposed_to_tag_stored_vectors():
    assert FastEmbedEmbedder(model=StubTextEmbedding()).model_name == DEFAULT_MODEL


@pytest.mark.skipif(
    not (CACHE_DIR.exists() and any(CACHE_DIR.iterdir())),
    reason="Modèle d'embeddings non téléchargé (se télécharge au premier usage réel)",
)
def test_real_model_gives_close_vectors_for_close_meanings():
    embedder = FastEmbedEmbedder()

    pay, notice, question = embedder.embed(
        [
            "Le client dispose de trente jours pour régler chaque facture.",
            "Le contrat peut être résilié moyennant un préavis de deux mois.",
            "Combien de temps pour payer une facture ?",
        ]
    )

    def cosine(a, b):
        a, b = np.array(a), np.array(b)
        return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

    assert len(pay) == 384
    assert cosine(question, pay) > cosine(question, notice)
