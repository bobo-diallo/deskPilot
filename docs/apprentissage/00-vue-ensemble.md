# 00 — Vue d'ensemble

## La carte du projet

```
deskPilot/
├── backend/            # l'API en Python (FastAPI) : la logique et les données
│   ├── app/
│   │   ├── main.py         # point d'entrée : construit l'application
│   │   ├── config.py       # lit la configuration (.env)
│   │   ├── api/            # les routes (adresses) de l'API
│   │   ├── core/           # outils communs (base de données)
│   │   └── domains/        # un dossier par sujet métier
│   └── tests/          # tests automatiques
├── frontend/           # l'interface web en Angular (TypeScript)
├── docs/               # documentation (dont ces guides)
├── demo-data/          # documents d'exemple (plus tard)
└── docker-compose.yml  # lance backend + frontend ensemble
```

## Qui fait quoi

- Le **navigateur** affiche l'application Angular (port 4200).
- Angular, quand il a besoin de données, appelle l'**API** FastAPI (port 8010).
- L'API lit et écrit dans la **base SQLite** (un simple fichier `backend/data/deskpilot.db`).
- Plus tard (story 01), l'API appellera aussi un **LLM** (Claude).

```
Navigateur  →  Angular (4200)  →  FastAPI (8010)  →  SQLite
                                        └──────→  LLM (story 01)
```

## Le trajet d'une requête `GET /health`

1. Une requête HTTP arrive sur le port 8010.
2. FastAPI cherche une route qui correspond à `GET /health` : c'est la fonction `health`
   dans `backend/app/api/health.py`.
3. La fonction renvoie `{"status": "ok"}`, que FastAPI transforme en JSON.
4. La réponse repart avec le code HTTP 200.

## Comparaison avec ce que tu connais

| Ici | Équivalent PHP / JS |
|---|---|
| FastAPI | Symfony ou Laravel, en plus léger (routes + validation) |
| SQLAlchemy | Doctrine (ORM) |
| pydantic-settings | Lecture de `.env` comme `$_ENV` / Dotenv |
| pytest | PHPUnit / Pest |
| `.venv` + `pip` | `vendor/` + Composer |
| `pyproject.toml` | `composer.json` |
| Angular | Framework front comme Vue ou React, mais complet et typé |

## Pourquoi cette organisation en « domaines »
Au lieu de ranger par type technique (tous les modèles ensemble, toutes les routes
ensemble), on range par sujet métier : `conversations`, `documents`, `llm`. Quand on
travaillera sur les documents, tout ce qui les concerne sera au même endroit. C'est l'idée du
DDD (Domain-Driven Design) que tu connais déjà.

## À essayer
Lance `docker compose up --build`, puis ouvre http://localhost:8010/health et
http://localhost:4200.

## Exercice
Dessine sur papier le chemin qu'emprunteront une facture déposée dans l'interface et la
donnée extraite. Garde ce schéma : on le comparera à la réalité en story 02.
