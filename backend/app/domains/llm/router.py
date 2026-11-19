from enum import Enum


class Task(Enum):
    """Type de tâche demandée à un modèle."""

    EXTRACTION = "extraction"  # lire un document et en tirer des champs : demande de la précision
    AGENT = "agent"  # choisir des outils, enchaîner des étapes, répondre : demande du jugement
    SIMPLE = "simple"  # reformuler, classer, répondre court : un petit modèle suffit


# Règle de routage : chaque tâche va vers le plus petit modèle que l'évaluation juge suffisant.
# Extraction : Haiku 5.5 avec le prompt v2 a obtenu 100 % de factures parfaites sur deux jeux
# (principal et indépendant), contre 93,8 % pour Sonnet avec le prompt v1, pour ~18x moins cher
# (docs/evaluation/). Provisoire : le jeu est synthétique et désormais trop facile pour trancher.
MODEL_BY_TASK: dict[Task, str] = {
    Task.EXTRACTION: "claude-haiku-5-5",
    # Provisoire : Haiku par défaut, à confirmer ou à remplacer par l'évaluation de l'agent.
    Task.AGENT: "claude-haiku-5-5",
    Task.SIMPLE: "claude-haiku-5-5",
}


def choose_model(task: Task) -> str:
    return MODEL_BY_TASK[task]
