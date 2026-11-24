"""Prompts d'extraction versionnés.

Un prompt se traite comme du code : on ne le modifie pas en place, on ajoute une version, on la
compare à la précédente avec l'évaluation, puis on décide. `v1` reste intact pour pouvoir
reproduire les anciennes mesures.
"""

from app.domains.llm.prompts import PromptSet

_V1 = (
    "Tu extrais les champs d'une facture à partir du document fourni. "
    "Si une information est absente ou illisible, laisse le champ vide : "
    "n'invente jamais de valeur. "
    "Les montants sont des nombres décimaux sans symbole monétaire ni séparateur de milliers."
)

# Ajoutée après la première évaluation : des dates américaines étaient lues à l'envers.
_V2 = (
    _V1 + " Pour une date écrite en chiffres, applique la convention du document : "
    "mois/jour/année sur une facture américaine (montants en dollars US, libellés en anglais), "
    "jour/mois/année sinon."
)

# Version validée par l'évaluation (voir docs/evaluation/) ; `v1` reste sélectionnable.
DEFAULT_PROMPT_VERSION = "v2-date-convention"

EXTRACTION_PROMPTS = PromptSet(
    name="extraction",
    versions={"v1": _V1, "v2-date-convention": _V2},
    default=DEFAULT_PROMPT_VERSION,
)
PROMPTS = EXTRACTION_PROMPTS.versions


def get_prompt(version: str) -> str:
    return EXTRACTION_PROMPTS.get(version)
