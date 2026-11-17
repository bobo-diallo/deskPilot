class LLMRefusedError(Exception):
    """Le modèle a refusé de répondre (filtre de sécurité). La requête n'a pas de réponse utile."""
