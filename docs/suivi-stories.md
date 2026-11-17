# Suivi des stories

## Story 00 — Fondations ✅
- Branche : `story/00-foundations`
- PR : [#1](https://github.com/bobo-diallo/deskPilot/pull/1), fusionnée
- Checklist :
  - [x] Dépôt git local et dépôt GitHub privé (nommé d'abord `bureau-ia`, renommé `deskPilot`)
  - [x] Cadrage produit, architecture, feuille de route (`docs/`)
  - [x] Backend FastAPI : `/health`, configuration `.env`, pytest, Black, Ruff
  - [x] Modèles SQLAlchemy (conversations, messages, documents, chunks, api_calls)
  - [x] Frontend Angular : écran à trois zones, bascule FR/EN (Transloco)
  - [x] Docker Compose (backend 8010, frontend 4200), README, CLAUDE.md
  - [x] Guides d'apprentissage (`docs/apprentissage/`) et prompt de design (`docs/design/`)

## Story 01 — Adaptateur LLM, routeur et journal des coûts ✅
- Branche : `story/01-llm-adapter`
- PR : [#2](https://github.com/bobo-diallo/deskPilot/pull/2), fusionnée
- Checklist :
  - [x] Calcul du coût par modèle (`pricing`)
  - [x] Interface `LLMProvider`, schémas, fournisseur factice
  - [x] Service avec journal `api_calls` (coût, tokens, latence)
  - [x] Routeur de modèles par tâche
  - [x] Fournisseur Anthropic (refus géré), test réel ignoré sans clé
  - [x] Route `POST /llm/complete`
  - [x] Guide `docs/apprentissage/07-llm-et-adaptateur.md`
  - [x] Essai réel avec une clé API : `pong` via Haiku 5.5, 4,3e-6 $, ligne dans `api_calls`, test réel vert
  - [ ] Repli automatique en cas de refus (`fallbacks`), à décider
## Story 02 — Extraction PDF/image vers JSON validé 📋
## Story 03 — Évaluation 📋
## Story 04 — Audio vers texte puis extraction 📋
## Story 05 — Agent avec outils et file de revue 📋
## Story 06 — Écran Coûts et publication du dépôt 📋
