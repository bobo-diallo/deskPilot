# deskPilot — Bureau IA

Démonstrateur d'automatisation IA pour PME : transforme des documents non structurés
(PDF, images, audio) en données structurées validées, avec un agent IA outillé (dont un
mini-RAG) et une évaluation chiffrée. Projet d'apprentissage « AI engineer ».
Dépôt GitHub : `deskPilot` (public depuis le 2026-11-21, `main` protégée : PR et 3 contrôles requis). Nom d'écran : « Bureau IA ».
Pratiques standard de l'intégration IA (suivi de ce qui est couvert) : `docs/standards-ia.md`.
Guides de cours : `docs/apprentissage/`. Prompt de design : `docs/design/prompt-design.md`.
Cadrage : `docs/produit.md`. Décisions : `docs/architecture.md`. Idées V2 : `docs/roadmap.md`.

## Stack
- Backend : Python 3.12 (`.venv` dans `backend/`), FastAPI, SQLAlchemy 2, pydantic-settings,
  pytest, Black, Ruff (configurés dans `backend/pyproject.toml`).
- Base : SQLite en V1 (tables créées au démarrage), PostgreSQL + Alembic en V2.
- Frontend : Angular 21 (standalone), Transloco (FR/EN à l'exécution), tests Vitest.
- Exécution : `docker compose up --build` (backend sur le port 8010, frontend sur 4200).
- LLM : Anthropic (SDK `anthropic`) derrière l'interface `LLMProvider` ; routeur Haiku 5.5 pour l'extraction (prompt v2, validé par évaluation) et pour les tâches simples ; chaque appel est journalisé dans `api_calls` ; les pannes passagères sont retentées (`RetryingProvider`) et traduites en erreurs HTTP propres.

## Architecture
1. Monorepo : `backend/`, `frontend/`, `demo-data/`, `docs/`.
2. Backend organisé par domaine dans `backend/app/domains/` (conversations, documents, extraction, llm, transcription, review, search, agent, costs, evaluations).
3. Chaque domaine isole son modèle métier ; les routes sont dans `backend/app/api/`.
4. `backend/app/core/database.py` : moteur SQLAlchemy et création des tables au démarrage.
5. `backend/app/config.py` : configuration lue depuis `.env` (modèle : `.env.example`).
6. Tables : `conversations`, `messages`, `documents`, `chunks`, `api_calls` (journal des coûts), `extractions`, `transcriptions`, `review_decisions` (piste d'audit de la revue), `chunk_embeddings` (vecteurs de la recherche), `agent_runs` et `agent_steps` (trace de l'agent).
7. Le LLM est appelé via une interface unique ; `backend/app/evaluation/` mesure la qualité (jeu annoté, métriques, rapports dans `docs/evaluation/`).
8. Frontend : textes dans `frontend/public/i18n/{fr,en}.json`, jamais en dur dans les gabarits.
9. Domaine de démonstration V1 : factures et contrats de PME.
10. Le mini-RAG (en cours de développement, hors de ce dépôt) devient un outil de l'agent (story 05).

## Conventions
- **Langue** : échanges, messages de commit, descriptions de PR et commentaires de code en
  français. Identifiants techniques (branches, fichiers, variables, classes, noms de tests)
  en anglais. Libellés affichés à l'utilisateur en français, jamais de valeur technique brute.
- **Méthode** : DDD, TDD (test d'abord), SOLID. Plan bref validé avant le code d'une story.
  Une étape = une fonctionnalité vérifiable. Pas de fonctionnalité « au cas où ».
- **Erreurs** : montrer le message d'erreur brut complet.
- **Git** : `main` est la seule branche longue. Une branche `story/<nn>-<short-summary>` par
  story, créée avant de modifier le code. Un commit = un changement logique, message en
  français expliquant le pourquoi, préfixé `<branche>: `. Jamais de ligne `Co-Authored-By`.
  **Jamais de push ni de pull request sans « go » explicite** (commandes `/push` et `/pr`).
- **Mode apprentissage** : l'utilisateur découvre Python et ses frameworks. Expliquer chaque
  nouvelle notion quand elle apparaît (avec des comparaisons PHP/JS), garder le code simple,
  et ajouter ou compléter un guide dans `docs/apprentissage/` à chaque story.
- **Standards IA** : rester dans les pratiques courantes de l'industrie (voir `docs/standards-ia.md`) ;
  chaque story met à jour ce tableau.
- **Fichiers ignorés** : jamais de fichiers d'éditeur ni de secrets dans git (`.idea/`,
  `.vscode/`, `.vs/`, `.env`, `.venv/`…). Vérifier avec `git ls-files` avant de commiter.
- **Données de démo** : pour tout ce qui touche à Google (clés, inscriptions), utiliser le compte de démonstration défini dans les préférences globales, jamais le compte personnel.

## Commandes
```
docker compose up --build        # lance backend (8010) et frontend (4200)
cd backend && source .venv/bin/activate
pytest                           # tests backend
python -m app.evaluation --help  # évaluation (estime le coût, --yes pour exécuter)
python scripts/generate_eval_audio.py   # jeu de dictées (macOS : say + ffmpeg)
python -m app.evaluation.search_cli    # évaluation de la recherche (gratuite, tout est local)
python -m app.evaluation.agent_cli --help   # évaluation de l'agent (estime le coût, --yes pour exécuter)
black app tests && ruff check app tests
cd frontend && npx ng test --watch=false   # tests frontend
# http://localhost:4200/evaluation : écran Évaluation et coûts
```

## Avancement (V1)
- [x] 00 Fondations
- [x] 01 Adaptateur LLM, routeur et journal des coûts
- [x] 02 Extraction PDF/image vers JSON validé (évaluation du mini-RAG déplacée en story 05)
- [x] 03 Évaluation : jeu annoté, précision par champ, comparaison de modèles
- [x] 04 Audio vers texte puis extraction (Whisper local `small`, jeu de dictées, rapport audio)
- [x] 05a File de revue humaine (dictée toujours à relire, piste d'audit, statistiques)
- [x] 05b Recherche dans les documents : mini-RAG dans le dépôt derrière `DocumentSearch` (mode `vector` par défaut)
- [x] 05c Agent avec outils (recherche, vérification, export avec approbation) et son évaluation (Haiku retenu)
- [x] 06a API des coûts (`/costs/summary`, `/costs/daily`, colonne `task` dans `api_calls`)
- [x] 06d Page de test minimale (`/test-page`, outil de développement)
- [x] 06b Écran Angular « Évaluation et coûts » (Material, API `/evaluations` ; design définitif encore attendu, autres écrans à faire)
- [x] 06c Publication du dépôt : audit, CI, README, licence MIT, vérification Docker, passage en public et protection de `main`
- [x] 07 Résilience des appels au modèle (erreurs nommées, nouvelles tentatives à délai croissant, réponses 502/503/504)
- [x] 08 Prompts versionnés et reliés aux résultats (empreintes verrouillées, `prompt_version` dans `extractions` et `agent_runs`)

Détail par story : `docs/suivi-stories.md`.

## Notes techniques
- Un prompt publié ne se modifie jamais : ajouter une nouvelle version, la mesurer, puis verrouiller son empreinte dans `backend/tests/test_prompt_lock.py`.
- Pas d'Alembic en V1 : une colonne ajoutée à un modèle demande un `ALTER TABLE` manuel sur la base locale (sauvegarde d'abord ; voir `docs/apprentissage/17-prompts-versionnes.md`).
- Le conteneur frontend copie le code au build : après une modification, `docker compose up -d --build frontend`.
- Le frontend appelle `/api/...` ; le proxy (`frontend/proxy.conf.js`) retire `/api` et transmet au backend.
- Après modification de `.env`, recréer le conteneur : `docker compose up -d --force-recreate backend`.
- Angular 21 (et non la dernière version) : la machine de développement a Node 24.10, alors que
  le dernier Angular CLI exige Node ≥ 24.15.
- Port 8010 pour le backend : le port 8000 est utilisé par un autre projet local.
- Le `package-lock.json` doit être régénéré avec `npx npm@11.19.1 install --package-lock-only`
  (compatibilité avec le npm de l'image Docker).
- Audio : `faster-whisper` (sans PyTorch) ; garder `av<17` dans `pyproject.toml` (PyAV 17+ casse
  le décodage). Taille par défaut `small` (`WHISPER_MODEL_SIZE`). Les modèles se téléchargent
  au premier usage (volume Docker `whisper-cache`). Les latences se mesurent mal quand la
  machine est chargée (Docker de l'autre projet) : revérifier la charge avant de comparer.
