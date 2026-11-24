import pytest

from app.domains.llm.prompts import PromptSet


def make() -> PromptSet:
    return PromptSet(
        name="demo", versions={"v1": "Premier texte", "v2": "Second texte"}, default="v2"
    )


def test_a_version_returns_its_text():
    assert make().get("v1") == "Premier texte"


def test_an_unknown_version_is_refused_with_its_name():
    with pytest.raises(ValueError, match="v99"):
        make().get("v99")


def test_the_default_must_be_one_of_the_versions():
    with pytest.raises(ValueError, match="v3"):
        PromptSet(name="demo", versions={"v1": "x"}, default="v3")


def test_the_fingerprint_is_short_and_stable():
    fingerprint = make().fingerprint("v1")

    assert len(fingerprint) == 8
    assert fingerprint == make().fingerprint("v1")


def test_the_fingerprint_changes_when_the_text_changes_by_one_character():
    other = PromptSet(name="demo", versions={"v1": "Premier texte."}, default="v1")

    assert make().fingerprint("v1") != other.fingerprint("v1")


def test_two_versions_have_different_fingerprints():
    assert make().fingerprint("v1") != make().fingerprint("v2")
