# deskPilot — Bureau IA

Démonstrateur d'automatisation IA pour PME : transforme des documents non structurés
(PDF, images, audio) en données structurées validées, avec un agent IA outillé (dont un
mini-RAG) et une évaluation chiffrée. Projet d'apprentissage « AI engineer ».
Guides de cours : `docs/apprentissage/`. Prompt de design : `docs/design/prompt-design.md`.
Cadrage : `docs/produit.md`. Décisions : `docs/architecture.md`. Idées V2 : `docs/roadmap.md`.

## Stack
- Backend : Python 3.12 (`.venv` dans `backend/`), FastAPI, SQLAlchemy 2, pydantic-settings,
  pytest, Black, Ruff (configurés dans `backend/pyproject.toml`).
- Base : SQLite en V1 (tables créées au démarrage), PostgreSQL + Alembic en V2.
- Frontend : Angular 21 (standalone), Transloco (FR/EN à l'exécution), tests Vitest.
- Exécution : `docker compose up --build` (backend sur le port 8010, frontend sur 4200).
- LLM : Anthropic par défaut, derrière une interface (story 01).

## Architecture
1. Monorepo : `backend/`, `frontend/`, `demo-data/`, `docs/`.
2. Backend organisé par domaine dans `backend/app/domains/` (conversations, documents, llm).
3. Chaque domaine isole son modèle métier ; les routes sont dans `backend/app/api/`.
4. `backend/app/core/database.py` : moteur SQLAlchemy et création des tables au démarrage.
5. `backend/app/config.py` : configuration lue depuis `.env` (modèle : `.env.example`).
6. Tables : `conversations`, `messages`, `documents`, `chunks`, `api_calls` (journal des coûts).
7. Le LLM sera appelé via une interface unique pour changer de modèle sans toucher au métier.
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
- **Fichiers ignorés** : jamais de fichiers d'éditeur ni de secrets dans git (`.idea/`,
  `.vscode/`, `.vs/`, `.env`, `.venv/`…). Vérifier avec `git ls-files` avant de commiter.
- **Données de démo** : compte Google `curioflow.demo@gmail.com`, jamais le compte personnel.

## Commandes
```
docker compose up --build        # lance backend (8010) et frontend (4200)
cd backend && source .venv/bin/activate
pytest                           # tests backend
black app tests && ruff check app tests
cd frontend && npx ng test --watch=false   # tests frontend
```

## Avancement (V1)
- [x] 00 Fondations
- [ ] 01 Adaptateur LLM, routeur et journal des coûts
- [ ] 02 Extraction PDF/image vers JSON validé (avec évaluation du mini-RAG en ouverture si prêt)
- [ ] 03 Évaluation : jeu annoté, précision par champ, comparaison de modèles
- [ ] 04 Audio vers texte puis extraction
- [ ] 05 Agent avec outils (mini-RAG, vérification, export) et file de revue humaine
- [ ] 06 Écran Coûts et publication du dépôt (passage en public)

Détail par story : `docs/suivi-stories.md`.

## Notes techniques
- Angular 21 (et non la dernière version) : la machine de développement a Node 24.10, alors que
  le dernier Angular CLI exige Node ≥ 24.15.
- Port 8010 pour le backend : le port 8000 est utilisé par un autre projet local.
- Le `package-lock.json` doit être régénéré avec `npx npm@11.19.1 install --package-lock-only`
  (compatibilité avec le npm de l'image Docker).
