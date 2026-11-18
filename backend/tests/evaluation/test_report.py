from datetime import date
from decimal import Decimal

from app.domains.extraction.schemas import Invoice
from app.evaluation.metrics import score_extraction
from app.evaluation.report import render_markdown
from app.evaluation.runner import TrialResult, VariantResult


def make_invoice(total: str = "30.00") -> Invoice:
    return Invoice(
        supplier_name="Atelier Nord",
        invoice_number="1",
        issue_date=date(2026, 11, 12),
        currency="EUR",
        lines=[],
        subtotal=Decimal("25.00"),
        tax_amount=Decimal("5.00"),
        total=Decimal(total),
    )


def trial(case_id, tags, extracted_total, run=1, cost=0.01, latency=1000, status="validated"):
    score = score_extraction(make_invoice(), make_invoice(extracted_total), status)
    return TrialResult(case_id, tags, run, score, "m", 100, 50, cost, latency, None)


def variant(name, results) -> VariantResult:
    return VariantResult(name=name, trials=results)


def make_report(baseline_ok=4, other_ok=2, total=4) -> str:
    def build(ok):
        return [
            trial(
                f"c{i}", ("digital",) if i % 2 == 0 else ("scan",), "30.00" if i < ok else "99.00"
            )
            for i in range(total)
        ]

    return render_markdown(
        [variant("sonnet", build(baseline_ok)), variant("haiku", build(other_ok))],
        runs=1,
        generated_on=date(2026, 11, 18),
    )


def test_report_names_every_variant_and_the_date():
    report = make_report()

    assert "sonnet" in report and "haiku" in report
    assert "2026-11-18" in report


def test_report_shows_perfect_rates_in_french_format_with_a_confidence_interval():
    report = make_report()

    assert "100,0 %" in report  # sonnet : 4 sur 4
    assert "50,0 %" in report  # haiku : 2 sur 4
    assert "IC 95 %" in report


def test_report_shows_cost_per_invoice_and_latency():
    report = make_report()

    assert "0,0100 $" in report
    assert "1,0 s" in report


def test_report_breaks_results_down_by_difficulty_tag():
    report = make_report()

    assert "PDF numérique" in report and "Image (scan)" in report
    assert "digital" not in report  # jamais de valeur technique brute


def test_report_compares_each_variant_with_the_first_one_using_a_paired_interval():
    report = make_report()

    assert "Comparaison avec la référence" in report
    assert "haiku" in report.split("Comparaison avec la référence")[1]


def test_report_states_its_limits():
    assert "Limites" in make_report()


def test_report_flags_silent_errors_of_the_validated_status():
    # Une facture fausse mais cohérente reste « validated » : erreur silencieuse.
    wrong_but_validated = trial("c0", ("digital",), "99.00", status="validated")
    report = render_markdown(
        [variant("v", [wrong_but_validated])], runs=1, generated_on=date(2026, 11, 18)
    )

    assert "Erreurs silencieuses" in report


def audio_trial(case_id, wer, audio_seconds=10.0, latency=5000):
    score = score_extraction(make_invoice(), make_invoice("30.00"), "validated")
    return TrialResult(
        case_id, ("fast",), 1, score, "m", 100, 50, 0.001, latency, None, wer, audio_seconds
    )


def make_audio_report() -> str:
    tiny = variant("whisper-tiny", [audio_trial("a", 0.30), audio_trial("b", 0.10)])
    base = variant("whisper-base", [audio_trial("a", 0.10, latency=20000), audio_trial("b", 0.0)])
    return render_markdown([tiny, base], runs=1, generated_on=date(2026, 11, 18))


def test_an_audio_report_shows_the_word_error_rate_and_the_speed_relative_to_the_audio():
    report = make_audio_report()

    assert "Erreurs sur les mots" in report
    assert "20,0 %" in report  # tiny : moyenne de 30 % et 10 %
    assert "5,0 %" in report  # base : moyenne de 10 % et 0 %
    assert "Temps de calcul / durée audio" in report
    assert "0,5" in report  # 5 s de calcul pour 10 s d'audio


def test_a_document_report_has_no_audio_columns():
    report = make_report()

    assert "Erreurs sur les mots" not in report
    assert "durée audio" not in report


def test_an_audio_report_warns_that_synthetic_voices_are_cleaner_than_real_ones():
    assert "voix de synthèse" in make_audio_report()


def test_audio_tags_have_french_labels():
    report = make_audio_report()

    assert "Débit rapide" in report
