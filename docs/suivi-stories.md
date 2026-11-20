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
## Story 03 — Évaluation ✅
- Branche : `story/03-evaluation` (PR à ouvrir sur demande)
- Checklist :
  - [x] Tableau des pratiques standard et niveau avancé (`docs/standards-ia.md`)
  - [x] Jeu de 24 factures synthétiques reproductibles, 10 difficultés étiquetées
  - [x] Métriques pures : exactitude par champ, valeurs inventées, fiabilité du statut, Wilson, bootstrap apparié
  - [x] Runner, rapport Markdown en français, commande avec estimation du coût et `--yes`
  - [x] Mesures : Sonnet contre Haiku (v1 et v2 du jeu), prompt v2, texte seul, jeu indépendant
  - [x] Défaut du jeu v1 découvert et corrigé, rapport v1 conservé avec avertissement
  - [x] Prompts versionnés (v1, v2) ; routeur d'extraction passé à Haiku + v2
  - [x] Essai Docling dans Docker : fonctionne, non retenu (`docs/evaluation/2026-11-17-docling-spike.md`)
  - [x] Guide `docs/apprentissage/09-evaluation.md`
  - Budget : 1,35 $ pour environ 460 appels réels (plafond 1,5 $)
  - Restes : jeu plus difficile (le jeu atteint 100 %), effort de réflexion, prompt caching, cascade Haiku vers Sonnet sur `needs_review`
## Story 04 — Audio vers texte puis extraction ✅
- Branche : `story/04-audio-extraction` (PR à ouvrir sur demande)
- Checklist :
  - [x] Essai préalable : `faster-whisper` tourne sur Mac Intel sans PyTorch (PyAV borné sous la v17)
  - [x] Types audio détectés par signature (WAV, MP3, OGG, WebM, M4A)
  - [x] Domaine `transcription` : interface `Transcriber`, faux transcripteur, adaptateur Whisper
  - [x] `AudioExtractor` (transcription locale puis Claude Haiku sur le texte) et `MediaTypeExtractor`
  - [x] Table `transcriptions`, `POST /extractions` accepte l'audio et renvoie `transcript`
  - [x] Docker : volume de cache des modèles, `WHISPER_MODEL_SIZE`, exemple `http/extractions.http`
  - [x] Jeu de 12 dictées (voix de synthèse macOS, bruit, débit rapide), WER, rapport audio
  - [x] Mesure des trois tailles de Whisper : `docs/evaluation/2026-11-17-audio-whisper-sizes.md`
  - [x] Défaut corrigé : réponse hors schéma, 500 devenu 502 (`LLMInvalidOutputError`)
  - [x] Guide `docs/apprentissage/10-audio.md`
  - Résultat : `small` est la seule taille utilisable (22 essais sur 24 aboutissent, contre 11 et
    13) mais aucune facture n'est parfaite (noms propres) et 25 % ont montants et date exacts
  - Budget : environ 0,09 $ journalisé pour 144 appels (plafond 0,30 $) ; les appels hors schéma
    ne sont pas journalisés, le coût réel est un peu plus haut
  - Restes : journaliser les appels hors schéma, tester `medium` et un prompt pour les montants
    dictés sur un jeu neuf, statut « à relire » systématique pour l'audio, vraies voix humaines
## Story 05a — File de revue humaine ✅
- Branche : `story/05a-review-queue`
- Checklist :
  - [x] Une extraction issue d'une dictée est toujours `needs_review` (motif `from_audio`)
  - [x] Statuts `approved`, `corrected`, `rejected` ; table `review_decisions` (valeur d'origine conservée)
  - [x] `ReviewService` : file (plus ancienne d'abord), approuver, corriger (revalidée), rejeter
  - [x] Une décision = une seule transaction ; une extraction ne se relit qu'une fois
  - [x] Statistiques : taux de correction et champs corrigés
  - [x] Routes `GET /reviews`, `GET /reviews/stats`, `POST /reviews/{id}/approve|correct|reject` et `http/reviews.http`
  - [x] Guide `docs/apprentissage/11-revue-humaine.md`
  - [ ] Écran Angular de revue (en attente du design)
## Story 05b — Recherche dans les documents (mini-RAG dans le dépôt) ✅
- Branche : `story/05b-document-search`
- Checklist :
  - [x] Essai préalable : fastembed (ONNX) tourne sur Mac Intel sans PyTorch
  - [x] Découpage par clause, BM25 en Python pur, fusion RRF, métriques rappel@k et MRR
  - [x] Embeddings locaux, vecteurs stockés avec le nom du modèle (table `chunk_embeddings`)
  - [x] `SearchService` : indexer, rechercher en 3 modes ; interface `DocumentSearch` pour l'agent
  - [x] Routes `POST /search/documents`, `GET /search` et `http/search.http`
  - [x] Jeu de 10 contrats et 24 questions (4 types) ; rapport `docs/evaluation/2026-11-18-search.md`
  - [x] Règle de décision posée avant la mesure : hybride non retenu, `vector` par défaut
  - [x] Guide `docs/apprentissage/12-recherche-documents.md`
  - Coût : 0 $ (tout est local)
## Story 05c — Agent avec outils ✅
- Branche : `story/05c-agent`
- Checklist :
  - [x] Appel d'outils dans l'adaptateur LLM (`ToolSpec`, `ToolCall`, blocs rejouables) et `ScriptedProvider`
  - [x] Quatre outils typés : `search_documents`, `list_invoices`, `check_invoice`, `export_invoices` (sensible)
  - [x] Boucle d'agent : 6 appels maximum, erreurs d'outils renvoyées au modèle, trace en base
  - [x] Approbation humaine obligatoire pour l'export, avec reprise (approuver ou refuser)
  - [x] Routes `POST /agent/ask`, `GET /agent/runs/{id}`, `/approve`, `/reject` et `http/agent.http`
  - [x] Évaluation : 12 questions, 8 factures, 11 contrats dont un piégé ; règle posée avant la mesure
  - [x] Résultat : Haiku retenu (91,7 % contre 94,4 %, 0 action non sûre, ~20x moins cher)
  - [x] Guide `docs/apprentissage/13-agent.md`
  - Budget : 0,45 $ (essai de fumée 0,05 $ plus mesure 0,40 $) pour 80 essais ; plafond 1,00 $
  - Restes : mode de recherche pour l'agent (à tester sur un jeu neuf), vérification dans Docker (Docker était en panne), serveur MCP (05d facultative), écran Angular
## Story 06a — API des coûts 🔄
- Branche : `story/06a-costs-api`
- Checklist :
  - [x] Colonne `task` dans `api_calls`, renseignée par chaque appelant (extraction, agent, simple)
  - [x] `CostService` : totaux, ventilation par modèle et par tâche (p50/p95), série par jour
  - [x] Routes `GET /costs/summary` et `GET /costs/daily` (`from`/`to` inclus) et `http/costs.http`
  - [x] Guide `docs/apprentissage/14-couts.md`
  - [ ] Vérification dans Docker
  - Base locale à recréer (pas d'Alembic en V1) : ancienne sauvegardée en `deskpilot.db.bak-before-06a`

## Story 06d — Page de test minimale ✅
- Branche : `story/06d-test-page`
- Checklist :
  - [x] Page `GET /test-page` (HTML + JavaScript pur, sans dépendance) : dépôt, revue, recherche, agent, santé et coûts
  - [x] Contenu venant de l'API affiché en `textContent` (jamais `innerHTML`)
  - [x] Tests : page servie, routes couvertes, aucun secret embarqué
  - [ ] Parcours cliqué dans un navigateur (syntaxe JavaScript et routes vérifiées, pas le rendu) et vérification dans Docker
  - Hors produit : outil de développement, l'interface réelle reste la 06b

## Story 06b — Écran Angular « Évaluation et coûts » 📋
- Attend le design de l'utilisateur. Décision : l'écran inclura aussi les rapports d'évaluation
  (petite API de lecture de `docs/evaluation/` à prévoir).

## Story 06c — Publication du dépôt 🔄
- Branche : `story/06c-publication`
- Checklist :
  - [x] Audit des secrets : `gitleaks` sur 70 commits, aucune fuite (`docs/securite-publication.md`)
  - [x] `experiments/` supprimé, résultats Docling conservés dans `docs/evaluation/`
  - [x] Intégration continue (`.github/workflows/ci.yml`) : backend (ruff, black, pytest), frontend (Vitest), secrets (gitleaks)
  - [x] Licence MIT et README public (chiffres mesurés, limites)
  - [x] CI validée sur GitHub (trois contrôles verts, 46 s au plus)
  - [x] Adresse e-mail : conservée dans les commits (décision de l'auteur), un seul dépôt
  - [x] Vérification Docker de bout en bout (extraction PDF et audio, revue, recherche, agent avec approbation d'export, coûts) ; image `deskpilot-docling-spike` et volume `docling-cache` supprimés
  - [ ] Passage en public (« go » explicite), puis protection de `main` avec les 3 contrôles requis
