class LLMRefusedError(Exception):
    """Le modèle a refusé de répondre (filtre de sécurité). La requête n'a pas de réponse utile."""


class LLMInvalidOutputError(Exception):
    """La réponse du modèle ne respecte pas le schéma demandé (ex. valeur non numérique)."""
