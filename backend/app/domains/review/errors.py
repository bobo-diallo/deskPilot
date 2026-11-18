class ReviewError(Exception):
    """Base des erreurs de revue humaine."""


class ExtractionNotFoundError(ReviewError):
    """Aucune extraction ne porte cet identifiant."""


class NotReviewableError(ReviewError):
    """L'extraction n'est pas (ou plus) en attente de relecture."""


class InvalidCorrectionError(ReviewError):
    """La correction proposée n'a pas de sens (par exemple : rien n'a changé)."""
