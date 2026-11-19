import math

import pytest
from sqlalchemy import select

from app.domains.documents.models import Chunk
from app.domains.search.embedders.fake import FakeEmbedder
from app.domains.search.models import ChunkEmbedding
from app.domains.search.service import SearchService

CONTRACT = """Article 1. Paiement sous trente jours fin de mois.

Article 2. Préavis de résiliation de deux mois.

Article 3. Pénalités de retard de 1,5 % par mois."""


class StubEmbedder:
    """Embedder aux vecteurs choisis à la main : isole le rôle des mots-clés et du sens."""

    model_name = "stub"

    def __init__(self, vectors: dict[str, list[float]], default=(0.0, 1.0)):
        self._vectors = vectors
        self._default = list(default)

    def embed(self, texts):
        return [
            next((v for key, v in self._vectors.items() if key in text), self._default)
            for text in texts
        ]


def test_indexing_a_text_stores_one_chunk_per_paragraph_with_its_embedding(session):
    service = SearchService(session, FakeEmbedder())

    document = service.index_text("Contrat Atelier Nord", CONTRACT)

    chunks = session.scalars(select(Chunk).order_by(Chunk.position)).all()
    assert [chunk.position for chunk in chunks] == [0, 1, 2]
    assert chunks[1].text == "Article 2. Préavis de résiliation de deux mois."
    assert {chunk.document_id for chunk in chunks} == {document.id}
    assert document.filename == "Contrat Atelier Nord"
    assert document.media_type == "text/plain"
    embeddings = session.scalars(select(ChunkEmbedding)).all()
    assert len(embeddings) == 3
    assert {e.model for e in embeddings} == {"fake"}


def test_the_document_title_helps_to_find_a_clause_that_does_not_name_the_supplier(session):
    service = SearchService(session, FakeEmbedder())
    service.index_text("Contrat Atelier Nord", "Préavis de résiliation de deux mois.")
    service.index_text("Contrat Garage Tremblay", "Préavis de résiliation de un mois.")

    hits = service.search("préavis du Garage Tremblay", k=1, mode="keyword")

    assert hits[0].title == "Contrat Garage Tremblay"
    assert hits[0].text == "Préavis de résiliation de un mois."


def test_a_hit_carries_its_source_and_a_score(session):
    service = SearchService(session, FakeEmbedder())
    document = service.index_text("Contrat A", "Paiement sous trente jours.")

    hit = service.search("paiement", k=1, mode="keyword")[0]

    assert (hit.document_id, hit.title) == (document.id, "Contrat A")
    assert hit.chunk_id > 0
    assert hit.score > 0


def test_keyword_mode_finds_exact_words_that_the_embedder_cannot_see(session):
    embedder = StubEmbedder({"xylophone": [1.0, 0.0]}, default=(0.0, 1.0))
    service = SearchService(session, embedder)
    service.index_text("A", "Clause xylophone paiement.")
    service.index_text("B", "Clause bavardage général.")

    hits = service.search("xylophone question", k=2, mode="keyword")

    assert [hit.title for hit in hits] == ["A"]  # B ne contient aucun mot de la question


def test_vector_mode_finds_meaning_without_shared_words(session):
    embedder = StubEmbedder({"xylophone": [1.0, 0.0]}, default=(0.0, 1.0))
    service = SearchService(session, embedder)
    service.index_text("A", "Clause xylophone paiement.")
    service.index_text("B", "Clause bavardage général.")

    hits = service.search("question sans mot commun", k=2, mode="vector")

    assert [hit.title for hit in hits] == ["B", "A"]  # B a le même vecteur que la question


def test_hybrid_mode_keeps_what_either_method_finds(session):
    embedder = StubEmbedder({"xylophone": [1.0, 0.0]}, default=(0.0, 1.0))
    service = SearchService(session, embedder)
    service.index_text("A", "Clause xylophone paiement.")
    service.index_text("B", "Clause bavardage général.")

    hits = service.search("xylophone question", k=2, mode="hybrid")

    assert {hit.title for hit in hits} == {"A", "B"}
    assert hits[0].title == "A"  # premier du mot-clé et deuxième du vecteur


def test_k_limits_the_results(session):
    service = SearchService(session, FakeEmbedder())
    service.index_text("Contrat", CONTRACT)

    assert len(service.search("paiement préavis pénalités", k=2)) == 2


def test_searching_an_empty_index_gives_nothing(session):
    assert SearchService(session, FakeEmbedder()).search("paiement") == []


def test_an_unknown_mode_is_rejected(session):
    with pytest.raises(ValueError, match="mode"):
        SearchService(session, FakeEmbedder()).search("x", mode="magique")


def test_embeddings_from_another_model_are_ignored_by_vector_search(session):
    SearchService(session, StubEmbedder({}, default=(1.0, 0.0))).index_text("A", "Clause un.")

    newer = SearchService(session, FakeEmbedder())  # autre modèle : vecteurs incomparables

    assert newer.search("clause", k=3, mode="vector") == []


def test_the_fake_embedder_gives_unit_vectors_and_is_deterministic():
    embedder = FakeEmbedder()

    first, second = embedder.embed(["préavis de deux mois"] * 2)

    assert first == second
    assert math.isclose(sum(x * x for x in first), 1.0)
