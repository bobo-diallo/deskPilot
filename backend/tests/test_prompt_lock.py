"""Verrou des prompts : une version publiée ne se modifie jamais en place.

Chaque version a été (ou sera) mesurée par l'évaluation. Changer son texte rendrait les anciens
rapports faux sans que personne s'en aperçoive. Pour modifier un prompt : ajouter une NOUVELLE
version, la comparer par l'évaluation, puis ajouter son empreinte ci-dessous.
"""

import pytest

from app.domains.agent.prompts import AGENT_PROMPTS
from app.domains.extraction.prompts import EXTRACTION_PROMPTS

LOCKED = {
    ("extraction", "v1"): "cce8374a",
    ("extraction", "v2-date-convention"): "8ffb1d16",
    ("agent", "v1"): "ffce61f4",
}
PROMPT_SETS = {"extraction": EXTRACTION_PROMPTS, "agent": AGENT_PROMPTS}


@pytest.mark.parametrize(("key", "fingerprint"), list(LOCKED.items()))
def test_a_published_prompt_has_not_been_edited_in_place(key, fingerprint):
    name, version = key

    assert PROMPT_SETS[name].fingerprint(version) == fingerprint, (
        f"Le prompt {name}/{version} a changé. Ne le modifie pas : ajoute une nouvelle version, "
        "mesure-la avec l'évaluation, puis verrouille son empreinte dans ce fichier."
    )


@pytest.mark.parametrize("name", list(PROMPT_SETS))
def test_every_version_in_the_code_is_locked(name):
    registered = {(name, version) for version in PROMPT_SETS[name].versions}

    assert registered <= set(LOCKED), (
        f"Version non verrouillée dans {name} : ajoute son empreinte à LOCKED "
        "après l'avoir mesurée."
    )
