class AgentRunNotFoundError(Exception):
    """Aucune exécution d'agent ne porte cet identifiant."""


class AgentStateError(Exception):
    """L'action demandée n'est pas possible dans l'état actuel de l'exécution."""
