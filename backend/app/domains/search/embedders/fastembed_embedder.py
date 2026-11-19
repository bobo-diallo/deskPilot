from pathlib import Path

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# Hors du dossier temporaire par défaut de fastembed, qui peut être vidé : le modèle (0,22 Go)
# ne doit se télécharger qu'une fois. Dans Docker, ce dossier est un volume.
CACHE_DIR = Path.home() / ".cache" / "fastembed"


class FastEmbedEmbedder:
    """Embeddings calculés en local par fastembed (ONNX, sans PyTorch, sur processeur).

    Modèle multilingue de 384 dimensions, licence Apache 2.0. Gratuit : aucun appel réseau
    après le premier téléchargement.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL, *, model=None):
        self.model_name = model_name
        self._model = model  # injectable pour les tests ; sinon chargé au premier appel

    def _load(self):
        if self._model is None:
            # Import ici : la bibliothèque et le modèle ne se chargent que si on s'en sert
            from fastembed import TextEmbedding

            self._model = TextEmbedding(self.model_name, cache_dir=str(CACHE_DIR))
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        # `embed` de fastembed est un générateur de tableaux NumPy ; on renvoie des listes
        # Python simples, stockables en JSON.
        return [[float(x) for x in vector] for vector in self._load().embed(texts)]
