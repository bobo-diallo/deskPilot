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

## Tranché en story 03
- Modèle local contre API : API (Haiku v2). Docling essayé, non retenu (ADR 009).

## Resté ouvert
- Modèle open source local contre API pour l'audio (story 04, Whisper).
- Candidats Hugging Face restants : faster-whisper, Qwen3-ASR (audio). Pour les documents,
  PaddleOCR-VL, MinerU et Qwen3-VL seraient trop lents sur un Mac Intel sans GPU (non essayés).
  Vérifier la RAM nécessaire et les licences.

## Modèles de données (story 00)
`conversations`, `messages`, `documents`, `chunks` (extraits), `api_calls` (journal des
appels LLM : modèle, tokens, coût, latence).
