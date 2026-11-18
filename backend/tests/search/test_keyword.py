from app.domains.search.keyword import BM25Index, tokenize


def test_tokenize_folds_case_and_accents_and_drops_stopwords():
    assert tokenize("Le Préavis de RÉSILIATION est de deux mois") == [
        "preavis",
        "resiliation",
        "deux",
        "mois",
    ]


def test_tokenize_keeps_numbers():
    assert "30" in tokenize("Paiement sous 30 jours")


def test_a_document_containing_the_rare_term_ranks_first():
    index = BM25Index(
        [
            "Le paiement se fait sous trente jours.",
            "La garantie couvre les pièces pendant douze mois.",
            "Le paiement est comptant, la garantie est de douze mois.",
        ]
    )

    results = index.search("garantie comptant", k=3)

    assert results[0][0] == 2  # seul le document 2 contient les deux mots
    assert [position for position, _ in results] == [2, 1]  # le 0 ne contient aucun mot


def test_a_term_found_in_few_documents_weighs_more_than_a_common_one():
    index = BM25Index(
        [
            "contrat contrat contrat standard",
            "contrat spécial exclusivité",
            "contrat classique",
        ]
    )

    # « exclusivité » est rare : le document 1 gagne même si « contrat » est partout
    assert index.search("contrat exclusivité", k=1)[0][0] == 1


def test_a_query_without_any_known_word_gives_nothing():
    assert BM25Index(["Paiement sous trente jours."]).search("xylophone", k=3) == []


def test_k_limits_the_number_of_results():
    index = BM25Index([f"clause paiement numéro {n}" for n in range(10)])

    assert len(index.search("paiement", k=3)) == 3
