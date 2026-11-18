from typing import Literal, get_args

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.documents.models import Chunk, Document
from app.domains.search.chunker import split_into_chunks
from app.domains.search.fusion import reciprocal_rank_fusion
from app.domains.search.keyword import BM25Index
from app.domains.search.models import ChunkEmbedding
from app.domains.search.ports import Embedder, SearchHit

Mode = Literal["keyword", "vector", "hybrid"]
# Nombre de candidats gardés par méthode avant la fusion : assez large pour que la fusion
# puisse remonter un morceau que l'une des deux méthodes classait loin.
POOL_SIZE = 20


def retrieval_text(title: str, text: str) -> str:
    """Texte réellement indexé : le titre du document devant la clause.

    Sans lui, « Préavis de deux mois » ne dit pas de quel contrat on parle, et une question
    qui nomme le fournisseur ne peut pas retrouver la clause.
    """
    return f"{title} : {text}"


class SearchService:
    """Indexe des textes et les retrouve par mots-clés, par sens, ou les deux (hybride)."""

    def __init__(self, session: Session, embedder: Embedder):
        self._session = session
        self._embedder = embedder

    def index_text(self, title: str, text: str) -> Document:
        pieces = split_into_chunks(text)
        if not pieces:
            raise ValueError("Le texte à indexer est vide")

        document = Document(filename=title, media_type="text/plain")
        self._session.add(document)
        self._session.flush()  # attribue l'id du document
        chunks = [
            Chunk(document_id=document.id, position=position, text=piece)
            for position, piece in enumerate(pieces)
        ]
        self._session.add_all(chunks)
        self._session.flush()

        vectors = self._embedder.embed([retrieval_text(title, chunk.text) for chunk in chunks])
        self._session.add_all(
            ChunkEmbedding(chunk_id=chunk.id, model=self._embedder.model_name, vector=vector)
            for chunk, vector in zip(chunks, vectors, strict=True)
        )
        self._session.commit()  # document, morceaux et vecteurs : tout ou rien
        return document

    def search(self, query: str, k: int = 5, mode: Mode = "hybrid") -> list[SearchHit]:
        if mode not in get_args(Mode):
            raise ValueError(f"Le mode de recherche « {mode} » est inconnu")

        rows = self._session.execute(
            select(Chunk, Document.filename).join(Document).order_by(Chunk.id)
        ).all()
        if not rows:
            return []
        texts = [retrieval_text(title, chunk.text) for chunk, title in rows]

        keyword = BM25Index(texts).search(query, POOL_SIZE) if mode != "vector" else []
        vector = (
            self._vector_ranking(query, [chunk.id for chunk, _ in rows])
            if mode != "keyword"
            else []
        )

        if mode == "keyword":
            ranked = keyword
        elif mode == "vector":
            ranked = vector
        else:
            ranked = reciprocal_rank_fusion(
                [[position for position, _ in keyword], [position for position, _ in vector]]
            )
        return [
            SearchHit(chunk.id, chunk.document_id, title, chunk.text, score)
            for position, score in ranked[:k]
            for chunk, title in [rows[position]]
        ]

    def _vector_ranking(self, query: str, chunk_ids: list[int]) -> list[tuple[int, float]]:
        """Positions classées par similarité cosinus avec la question (même modèle seulement)."""
        stored = {
            row.chunk_id: row.vector
            for row in self._session.scalars(
                select(ChunkEmbedding).where(ChunkEmbedding.model == self._embedder.model_name)
            )
        }
        candidates = [
            (position, stored[cid]) for position, cid in enumerate(chunk_ids) if cid in stored
        ]
        if not candidates:
            return []
        matrix = np.array([vector for _, vector in candidates], dtype=float)
        question = np.array(self._embedder.embed([query])[0], dtype=float)

        def unit(array: np.ndarray) -> np.ndarray:
            norms = np.linalg.norm(array, axis=-1, keepdims=True)
            return array / np.where(norms == 0, 1, norms)  # un vecteur nul reste nul

        similarities = unit(matrix) @ unit(question)
        order = sorted(range(len(candidates)), key=lambda i: (-similarities[i], candidates[i][0]))
        return [(candidates[i][0], float(similarities[i])) for i in order[:POOL_SIZE]]
