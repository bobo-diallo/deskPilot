# 11 — La revue humaine (story 05a)

## Pourquoi un humain reste dans la boucle
L'évaluation l'a montré : sur les dictées, 8 extractions « validées » sur 22 étaient fausses
(surtout des noms propres, que les contrôles de montants ne voient pas). Dans un domaine comme
la finance, on ne laisse pas passer ça : une personne relit, tranche, et **on garde la trace**.

## Les notions
| Notion | En une phrase | Où dans le projet |
|---|---|---|
| Machine à états | Un objet ne peut changer de statut que selon des règles | `needs_review` → `approved`, `corrected` ou `rejected`, une seule fois |
| Piste d'audit | On n'écrase pas l'histoire : chaque décision est une ligne datée | table `review_decisions` |
| Transaction | Tout est enregistré, ou rien | un seul `commit` par décision |
| Erreur du domaine | Le métier lève ses propres erreurs, sans connaître HTTP | `domains/review/errors.py` |
| Traduction en HTTP | La couche API choisit le code : 404, 409, 422 | `api/reviews.py` |
| Validation à l'entrée | Pydantic refuse une facture mal formée avant tout traitement | `CorrectionRequest.data: Invoice` |

## Le parcours
1. Une dictée est déposée : l'extraction arrive en `needs_review` avec le motif `from_audio`.
2. `GET /reviews` la liste (les plus anciennes d'abord).
3. L'humain **approuve** (c'est juste), **corrige** (il envoie la facture complète) ou **rejette**.
4. La décision enregistre la valeur d'origine, la valeur corrigée et les champs modifiés.
5. `GET /reviews/stats` donne le taux de correction et les champs les plus corrigés : c'est la
   première mesure d'erreurs **en usage réel**, pas sur un jeu fixe.

## Règles à retenir (chacune a son test)
- Une extraction ne se relit qu'**une fois** (sinon 409).
- Une extraction déjà « validée » automatiquement n'entre pas dans la file.
- Une correction qui ne change rien est refusée (422) : il fallait approuver.
- Une correction repasse par la validation des montants. Le motif « dictée » disparaît (un
  humain a relu) ; une incohérence restante reste visible.
- Si la revalidation plante, aucune décision n'est enregistrée à moitié (test d'atomicité).

## Fichiers
`domains/review/` (`models.py`, `service.py`, `errors.py`) · `api/reviews.py` · `http/reviews.http`

## Pour PHP/JS
- Les statuts ressemblent à une énumération d'états dans un workflow Symfony ou à un
  `reducer` : l'ensemble des transitions autorisées est petit et testé.
- `Depends(get_db_session)` joue le rôle d'un service injecté par requête.

## À essayer
1. Dépose la dictée de démo (`http/extractions.http`), puis ouvre `http/reviews.http` : liste,
   corrige le fournisseur, puis relis `GET /reviews/stats`.
2. Tente d'approuver deux fois la même extraction : lis le code 409 et son message.
3. `pytest tests/review -v` : chaque test décrit une règle.

## Exercices
1. Ajoute un champ `reviewer` (qui a décidé) à la décision. Que faudrait-il pour que ce soit
   fiable ? (indice : l'authentification est hors périmètre V1).
2. Ajoute une route qui renvoie l'historique des décisions d'une extraction.
3. Un humain veut annuler une décision. Pourquoi ne pas modifier la ligne ? Propose une
   décision `reopened` qui garde l'histoire.
