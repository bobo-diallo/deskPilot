# Parcours d'apprentissage

Ce projet est aussi un cours. Tu n'as pas besoin de connaître Python : chaque notion est
expliquée quand elle apparaît, avec des comparaisons PHP/JavaScript quand elles aident.

## Comment lire ces guides
1. Lis d'abord la **vue d'ensemble** pour avoir la carte du projet.
2. Pour chaque guide : lis, ouvre les fichiers cités dans l'éditeur, essaie la section
   « À essayer », puis fais l'exercice.
3. Quand une story ajoute de nouvelles notions, un guide est ajouté ou complété ici.

## Les guides

| Guide | Tu y apprends |
|---|---|
| [00 — Vue d'ensemble](00-vue-ensemble.md) | La carte du projet et le trajet d'une requête |
| [01 — Python essentiel](01-python-essentiel.md) | Environnement virtuel, paquets, annotations de type, décorateurs |
| [02 — FastAPI](02-fastapi.md) | Une API web : routes, configuration, démarrage, documentation automatique |
| [03 — Base de données](03-base-de-donnees.md) | SQLAlchemy, modèles, relations, SQLite |
| [04 — Tests et TDD](04-tests-et-tdd.md) | pytest, cycle rouge-vert, Vitest côté Angular |
| [05 — Frontend Angular](05-frontend-angular.md) | Composants, traduction FR/EN avec Transloco |
| [06 — Docker](06-docker.md) | Dockerfile, docker compose, ports et volumes |
| [07 — LLM et adaptateur](07-llm-et-adaptateur.md) | Interface, injection de dépendances, coûts, routage (story 01) |
| [08 — Extraction de documents](08-extraction-de-documents.md) | Pydantic, sortie structurée, Decimal, upload, validation (story 02) |
| [09 — Évaluer un système d'IA](09-evaluation.md) | Vérité terrain, métriques, intervalles de confiance, jeu de validation, prompts versionnés (story 03) |
| [10 — De la voix au texte](10-audio.md) | Transcription Whisper en local, taux d'erreurs sur les mots, jeu de dictées, erreurs de format du modèle (story 04) |
| [11 — La revue humaine](11-revue-humaine.md) | Machine à états, piste d'audit, transactions atomiques, erreurs du domaine traduites en HTTP (story 05a) |
| [12 — La recherche dans les documents](12-recherche-documents.md) | BM25, embeddings, fusion, rappel@k et MRR, règle de décision posée avant la mesure (story 05b) |
| [13 — L'agent et ses outils](13-agent.md) | Appel d'outils, boucle d'agent, approbation humaine, injection de prompt, évaluer un agent (story 05c) |
| [14 — Lire le journal des coûts](14-couts.md) | Agrégats SQL, `GROUP BY`, percentiles p50/p95, période incluse/exclue (story 06a) |
| [15 — L'écran « Évaluation et coûts »](15-ecran-evaluation.md) | Composants Angular, signaux, `switchMap`, Material, graphique SVG, accessibilité, tests HTTP (story 06b) |
| [16 — Survivre aux pannes du fournisseur](16-resilience.md) | Erreurs passagères ou définitives, délai croissant, hasard, enrobage, idempotence (story 07) |

## Glossaire rapide

| Terme | Sens |
|---|---|
| API | Un programme qui répond à des requêtes HTTP avec des données (souvent du JSON) |
| Route | Une adresse de l'API associée à une fonction (`GET /health`) |
| ORM | Outil qui traduit des classes en tables SQL (SQLAlchemy ; équivalent de Doctrine ou Eloquent) |
| Environnement virtuel | Dossier `.venv` qui isole les bibliothèques Python d'un projet |
| TDD | Écrire le test avant le code : rouge (échoue), vert (passe), puis nettoyage |
| LLM | Grand modèle de langage (Claude, par exemple) |
| RAG | Répondre en allant d'abord chercher des extraits pertinents dans tes documents |
| Agent | Un LLM qui peut décider d'appeler des outils pour accomplir une tâche |
| i18n | Internationalisation : afficher l'interface en plusieurs langues |
| Délai croissant | Attendre de plus en plus longtemps entre deux nouvelles tentatives (1 s, 2 s, 4 s…) |
| Idempotent | Qu'on peut rejouer sans changer le résultat ni provoquer d'effet de bord |
