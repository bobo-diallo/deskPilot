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
## Story 02 — Extraction PDF/image vers JSON validé 🔄
- Branche : `story/02-document-extraction` (PR à ouvrir sur demande)
- Checklist :
  - [x] Schéma `Invoice` et règles de validation (tolérance d'un centime)
  - [x] Adaptateur LLM étendu : pièces jointes et sortie structurée
  - [x] Extracteur Claude, table `extractions`, service (statut validated / needs_review)
  - [x] `POST /extractions` (type détecté par signature, 10 Mo max) et `GET /extractions/{id}`
  - [x] 3 factures de démo avec valeurs attendues, tests réels verts (2 PDF et 1 image)
  - [x] Vérifié dans Docker : 0,0083 $ et 3,2 s pour une facture
  - [x] Guide `docs/apprentissage/08-extraction-de-documents.md`
  - [ ] Écran Angular de dépôt (en attente du design)
  - Décision en suspens : repli automatique en cas de refus du modèle
## Story 03 — Évaluation 📋
## Story 04 — Audio vers texte puis extraction 📋
## Story 05 — Agent avec outils et file de revue 📋
## Story 06 — Écran Coûts et publication du dépôt 📋
