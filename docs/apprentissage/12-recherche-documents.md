# 12 — Retrouver l'information : la recherche dans les documents (story 05b)

## Pourquoi
Un agent ne peut pas lire tous les contrats à chaque question : trop long, trop cher, et le
modèle se perd dans un gros texte. On **retrouve d'abord** les quelques morceaux utiles, puis on
les donne au modèle. C'est le principe du RAG (génération augmentée par la recherche). Ici, on
construit et on **mesure** la partie « recherche ».

## Les notions
| Notion | En une phrase | Où dans le projet |
|---|---|---|
| Morceau (chunk) | Un extrait de document, ici une clause | `chunker.py` |
| BM25 | Note les morceaux selon les mots de la question qu'ils contiennent, mots rares comptant plus | `keyword.py` |
| Embedding | Un texte devient une liste de nombres ; deux textes de sens proche ont des listes proches | `embedders/` |
| Similarité cosinus | Mesure l'angle entre deux listes de nombres : 1 = même direction | `service.py` |
| Fusion RRF | Combine deux classements en additionnant 1 / (60 + rang) | `fusion.py` |
| En-tête de contexte | Le titre du document est collé devant chaque clause avant l'indexation | `retrieval_text` |
| Rappel@k | La bonne réponse est-elle dans les k premiers résultats ? | `search_metrics.py` |
| MRR | Voir ci-dessous | `search_metrics.py` |

## Le MRR, avec un exemple
MRR veut dire *Mean Reciprocal Rank*, « moyenne du rang réciproque ». Pour chaque question, on
regarde **à quelle place** apparaît la première bonne réponse, et on prend l'inverse de cette
place :

| Bonne réponse en position | Points |
|---|---|
| 1 | 1 |
| 2 | 1/2 = 0,5 |
| 3 | 1/3 ≈ 0,33 |
| 10 | 0,1 |
| absente des 10 premiers | 0 |

Le MRR est la **moyenne** de ces points sur toutes les questions. Trois questions réussies en
position 1, 2 et absente donnent (1 + 0,5 + 0) / 3 = 0,5. Un MRR de 1 veut dire « toujours en
première place » ; 0 veut dire « jamais trouvé ».

Pourquoi pas seulement « trouvé ou pas » ? Parce que l'ordre compte : une réponse en 1re place
sera lue par l'agent, une réponse en 9e souvent ignorée. Le rappel@k répond à « est-elle dans les
k premiers ? », le MRR à « à quelle place ? ». On regarde les deux.

## Ce que l'évaluation a appris (rapport `docs/evaluation/2026-11-18-search.md`)
| Mode | MRR | Pour quoi il est bon |
|---|---|---|
| Mots-clés | 0,649 | Noms exacts, chiffres, « plusieurs contrats possibles » (1,000) |
| Sens (vector) | **0,851** | Paraphrases : 0,750 contre 0,188 pour les mots-clés |
| Hybride | 0,829 | Chiffres précis (1,000), mais dilué sur les paraphrases |

1. **Chaque méthode a un point faible.** Les mots-clés ne trouvent rien quand la question n'a
   aucun mot en commun avec la clause (« fin de semaine » contre « samedi matin »). Le sens
   confond parfois des clauses semblables (« paiement comptant »).
2. **L'hybride n'a pas gagné.** J'avais posé la règle avant de mesurer : hybride retenu s'il est à
   moins de 0,02 de MRR du meilleur. Il est à 0,022. Règle non satisfaite, donc mode par défaut :
   `vector`. L'écart n'est pas significatif (intervalle de -15,3 à +9,7 points) : on le sait, et
   on s'en tient quand même à la règle plutôt que de la réécrire après coup.
3. **Ne pas régler sur le jeu.** Une piste : filtrer les mots-clés faibles qui polluent la fusion.
   La tester sur ces 24 questions serait tricher ; il faut un jeu neuf.
4. **Le titre devant chaque clause change tout.** Sans lui, « Préavis d'un mois » ne dit pas de
   quel contrat on parle, et une question qui nomme le fournisseur ne peut rien retrouver.

## Fichiers
`domains/search/` (`chunker.py`, `keyword.py`, `fusion.py`, `service.py`, `ports.py`,
`models.py`, `embedders/`) · `api/search.py` · `evaluation/search_*.py` · `demo-data/search-eval/`

## Pour PHP/JS
- BM25 est ce que fait Elasticsearch ou le plein-texte de MySQL ; ici, 40 lignes de Python.
- Un embedding ressemble à une empreinte de sens : comme un hash, mais où deux textes proches
  donnent des empreintes proches.

## À essayer
1. `.venv/bin/python -m app.evaluation.search_cli --embedder fake` : le même rapport avec un
   faux modèle qui ne comprend pas le sens. Compare le MRR des paraphrases.
2. `http/search.http` : indexe les deux contrats, puis pose la même question dans les trois modes.
3. `pytest tests/search -v`.

## Exercices
1. Ajoute à `questions.json` trois questions de ton choix (test d'abord : le test de cohérence
   du jeu doit passer). Le MRR change-t-il ?
2. Change `POOL_SIZE` de 20 à 5 : que devient l'hybride ? Pourquoi ne pas garder ce réglage si
   ça l'améliore sur ce jeu ?
3. Explique pourquoi on additionne des rangs plutôt que les notes de BM25 et du cosinus.
