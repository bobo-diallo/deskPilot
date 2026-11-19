from app.domains.search.chunker import split_into_chunks


def test_each_paragraph_becomes_one_chunk():
    text = "Article 1. Paiement sous 30 jours.\n\nArticle 2. Préavis de deux mois."

    assert split_into_chunks(text) == [
        "Article 1. Paiement sous 30 jours.",
        "Article 2. Préavis de deux mois.",
    ]


def test_blank_lines_and_surrounding_spaces_are_ignored():
    assert split_into_chunks("\n\n  Un.  \n\n\n\n Deux. \n\n") == ["Un.", "Deux."]


def test_an_empty_text_gives_no_chunks():
    assert split_into_chunks("") == []
    assert split_into_chunks("   \n\n  ") == []


def test_a_long_paragraph_is_cut_at_sentence_boundaries_without_losing_text():
    sentences = [f"Phrase numéro {n} du paragraphe." for n in range(1, 21)]
    paragraph = " ".join(sentences)

    chunks = split_into_chunks(paragraph, max_chars=120)

    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)
    assert " ".join(chunks) == paragraph  # rien n'est perdu, rien n'est coupé en plein mot


def test_a_single_sentence_longer_than_the_limit_is_kept_whole():
    sentence = "Mot " * 50 + "fin."

    assert split_into_chunks(sentence.strip(), max_chars=40) == [sentence.strip()]
