# Architecture

## Principes
DDD léger, TDD, SOLID. Un dossier par domaine côté backend ; les dépendances pointent
vers le domaine. Le LLM reste derrière une interface (port) pour changer de modèle sans
toucher au métier.

## Pile
- Backend : Python 3.12, FastAPI, SQLAlchemy 2, pydantic-settings, pytest, Black, Ruff.
- Base : SQLite en V1, PostgreSQL en V2 (introduire Alembic à ce moment-là).
- Frontend : Angular (standalone), Transloco pour le FR/EN à l'exécution.
- Exécution : Docker Compose (backend + frontend).

## Décisions (ADR)
| N° | Décision | Raison |
|---|---|---|
| 001 | Transloco plutôt que `@angular/localize` | Bascule de langue en direct, sans build par langue |
| 002 | Création des tables au démarrage (`create_all`) en V1 | Simplicité ; Alembic arrive avec PostgreSQL |
| 003 | Identifiants techniques en anglais, libellés en français | Convention du projet |
| 004 | Fournisseur LLM par défaut : Anthropic, derrière une interface | Changer de modèle sans refonte (story 01) |
| 005 | Extraction : Claude lit directement PDF et images, derrière `DocumentExtractor` | Simple et précis ; Docling local à comparer en story 03 |
| 006 | Confiance mesurée par recoupements de montants, pas par probabilité du modèle | L'API ne fournit pas de score par champ |
| 007 | Montants en `Decimal`, type de fichier détecté par signature | Exactitude de l'argent ; ne pas croire le client |
| 008 | Extraction routée vers Haiku 5.5 avec le prompt v2 (provisoire) | 100 % sur deux jeux, ~18x moins cher que Sonnet ; jeu trop facile pour trancher définitivement |
| 009 | Docling non retenu en V1 | Fonctionne dans Docker mais lent sur CPU (28 s par image), ne remplace pas l'appel LLM ; `experiments/docling/` |
| 010 | Règle d'adoption posée avant la mesure, jeu de validation indépendant, prompts versionnés | Éviter de justifier un résultat après coup et la fuite de réglage |
| 011 | Voix : Whisper en local (`faster-whisper`, taille `small` par défaut), puis Claude Haiku sur le texte | Gratuit, l'audio ne quitte pas la machine, tourne sans PyTorch sur Mac Intel ; `small` est la seule taille utilisable (voir le rapport audio) |
| 012 | Réponse du modèle hors schéma = erreur nommée (`LLMInvalidOutputError`, 502), pas un plantage | Révélé par l'évaluation audio : une valeur non numérique dans un champ décimal donnait une erreur 500 |
| 013 | Une extraction issue d'une dictée est toujours « à relire » ; chaque décision humaine est un fait daté (`review_decisions`) qui garde la valeur d'origine | La voix se trompe sur les noms sans que les montants le montrent (8 extractions « validées » fausses sur 22) ; piste d'audit exigée en finance |
| 014 | Recherche dans les documents : embeddings locaux (fastembed, MiniLM multilingue), BM25 maison, fusion RRF ; mode par défaut `vector` | Mesuré sur 24 questions : vector MRR 0,851, hybride 0,829, mots-clés 0,649 ; règle « hybride si pas plus de 0,02 sous le meilleur » posée avant, non satisfaite. L'écart avec l'hybride n'est pas significatif |
| 015 | Modèle de l'agent : règle posée avant la mesure — Haiku si son taux de réussite est à 10 points ou moins de Sonnet **et** s'il n'a aucune action non sûre (export non demandé, instruction cachée suivie) ; sinon Sonnet. Une action sensible exige toujours l'approbation d'un humain | Choisir par la mesure, sans rationaliser après coup ; la sécurité ne se négocie pas contre le coût |

## Tranché en story 03
- Modèle local contre API : API (Haiku v2). Docling essayé, non retenu (ADR 009).

## Tranché en story 04
- Audio : Whisper local (ADR 011). Hugging Face en ligne est payant (crédit gratuit minime ou
  nul) : non essayé, aucun gain attendu face à Claude pour le texte.
- Claude ne transcrit pas l'audio : c'est le seul endroit où un modèle ouvert est nécessaire.

## Tranché en story 05a
- Dictée toujours à relire (ADR 013). Une correction humaine repasse par la validation des
  montants et supprime le motif « dictée » ; une incohérence restante reste visible.

## Tranché en story 05b
- Le mini-RAG vit dans ce dépôt derrière `DocumentSearch` ; le tien pourra s'y brancher plus tard.
- Mode de recherche par défaut : `vector` (ADR 014), à revoir avec un jeu plus grand.

## Resté ouvert
- Hybride : les mots-clés faibles (« fin », « semaine ») dégradent la fusion sur les paraphrases.
  Pondérer ou filtrer les mots-clés est une piste, **à tester sur un jeu neuf** (le régler sur
  celui-ci reviendrait à tricher).
- Un modèle Whisper plus gros (`medium`) ou un prompt adapté aux montants dictés (« 12 euros
  97 centimes ») : à tester sur un jeu neuf (le prompt ne doit pas être réglé sur ce jeu).
- Candidats Hugging Face restants : Qwen3-ASR (audio). Pour les documents,
  PaddleOCR-VL, MinerU et Qwen3-VL seraient trop lents sur un Mac Intel sans GPU (non essayés).
  Vérifier la RAM nécessaire et les licences.

## Modèles de données (story 00)
`conversations`, `messages`, `documents`, `chunks` (extraits), `api_calls` (journal des
appels LLM : modèle, tokens, coût, latence).
