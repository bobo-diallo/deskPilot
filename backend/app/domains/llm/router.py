from enum import Enum


class Task(Enum):
    """Type de tâche demandée à un modèle."""

    EXTRACTION = "extraction"  # lire un document et en tirer des champs : demande de la précision
    SIMPLE = "simple"  # reformuler, classer, répondre court : un petit modèle suffit


# Règle de routage : une tâche exigeante va vers un modèle plus capable (et plus cher).
MODEL_BY_TASK: dict[Task, str] = {
    Task.EXTRACTION: "claude-sonnet-5-5",
    Task.SIMPLE: "claude-haiku-5-5",
}


def choose_model(task: Task) -> str:
    return MODEL_BY_TASK[task]
