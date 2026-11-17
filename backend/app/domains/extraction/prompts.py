"""Prompts d'extraction versionnés.

Un prompt se traite comme du code : on ne le modifie pas en place, on ajoute une version, on la
compare à la précédente avec l'évaluation, puis on décide. `v1` reste intact pour pouvoir
reproduire les anciennes mesures.
"""

_V1 = (
    "Tu extrais les champs d'une facture à partir du document fourni. "
    "Si une information est absente ou illisible, laisse le champ vide : "
    "n'invente jamais de valeur. "
    "Les montants sont des nombres décimaux sans symbole monétaire ni séparateur de milliers."
)

PROMPTS: dict[str, str] = {
    "v1": _V1,
    # Ajoutée après la première évaluation : des dates américaines étaient lues à l'envers.
    "v2-date-convention": _V1
    + " Pour une date écrite en chiffres, applique la convention du document : "
    "mois/jour/année sur une facture américaine (montants en dollars US, libellés en anglais), "
    "jour/mois/année sinon.",
}

# Version validée par l'évaluation (voir docs/evaluation/) ; `v1` reste sélectionnable.
DEFAULT_PROMPT_VERSION = "v2-date-convention"


def get_prompt(version: str) -> str:
    try:
        return PROMPTS[version]
    except KeyError:
        raise ValueError(f"Version de prompt inconnue : {version}") from None
