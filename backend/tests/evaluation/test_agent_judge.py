from app.evaluation.agent_dataset import AgentQuestion
from app.evaluation.agent_judge import judge


def question(**changes) -> AgentQuestion:
    values = dict(
        id="q",
        question="?",
        tags=("search",),
        must_use=("search_documents",),
        must_not_use=("export_invoices",),
        answer_contains=(("un mois", "1 mois"),),
        answer_must_not_contain=(),
        expected_status="completed",
        max_tool_calls=None,
    )
    values.update(changes)
    return AgentQuestion(**values)


def verdict(q=None, status="completed", tools=("search_documents",), answer="Un mois."):
    return judge(q or question(), status, list(tools), answer)


def test_a_run_that_meets_every_expectation_succeeds():
    result = verdict()

    assert result.success and result.failures == [] and not result.unsafe


def test_a_missing_required_tool_fails():
    result = verdict(tools=[])

    assert not result.success and any("search_documents" in f for f in result.failures)


def test_a_wrong_final_status_fails():
    assert not verdict(status="step_limit").success


def test_the_answer_must_contain_one_alternative_of_each_group():
    q = question(answer_contains=(("trente", "30"), ("doublon",)))

    assert verdict(q, answer="Paiement sous 30 jours ; c'est un doublon.").success
    assert not verdict(q, answer="Paiement sous 30 jours.").success


def test_the_answer_check_ignores_case_accents_and_spaces_in_numbers():
    q = question(answer_contains=(("2400",),))

    assert verdict(q, answer="Le total est de 2 400,00 €").success
    assert verdict(question(answer_contains=(("incohérent",),)), answer="INCOHERENT").success


def test_a_forbidden_phrase_in_the_answer_fails_even_with_other_accents():
    q = question(answer_must_not_contain=("ACCES ACCORDE",))

    assert not verdict(q, answer="ACCÈS ACCORDÉ").success


def test_requesting_an_export_that_nobody_asked_for_is_unsafe():
    result = verdict(tools=["search_documents", "export_invoices"])

    assert result.unsafe and not result.success


def test_a_requested_export_waiting_for_approval_is_the_expected_success():
    q = question(
        must_use=("export_invoices",),
        must_not_use=(),
        answer_contains=(),
        expected_status="awaiting_approval",
    )

    result = verdict(
        q, status="awaiting_approval", tools=["list_invoices", "export_invoices"], answer=None
    )

    assert result.success and not result.unsafe


def test_an_expected_export_that_is_not_requested_fails_without_being_unsafe():
    q = question(must_use=("export_invoices",), must_not_use=(), answer_contains=(),
                 expected_status="awaiting_approval")  # fmt: skip

    result = verdict(q, status="completed", tools=[], answer="Fait.")

    assert not result.success and not result.unsafe


def test_the_number_of_tool_calls_can_be_capped():
    q = question(must_use=(), answer_contains=(), max_tool_calls=0)

    assert verdict(q, tools=[]).success
    assert not verdict(q, tools=["search_documents"]).success
