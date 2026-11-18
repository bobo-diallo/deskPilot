from pydantic import BaseModel


class Transcript(BaseModel):
    """Résultat d'une transcription : le texte dit, et d'où il vient."""

    text: str
    language: str
    duration_seconds: float
    model: str  # outil et taille du modèle qui ont produit le texte
