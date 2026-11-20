# deskPilot — « Bureau IA »

[![CI](https://github.com/bobo-diallo/deskPilot/actions/workflows/ci.yml/badge.svg)](https://github.com/bobo-diallo/deskPilot/actions/workflows/ci.yml)
[![Licence : MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

Démonstrateur d'automatisation IA pour PME : il transforme des documents non structurés
(PDF, images, dictées audio) en **données structurées validées**, avec une **revue humaine**,
une **recherche dans les contrats**, un **agent outillé** et, surtout, une **évaluation chiffrée**
de chaque choix (modèle, prompt, mode de recherche).

Projet d'apprentissage « ingénieur IA » : chaque décision est mesurée et documentée, y compris
quand la mesure contredit l'intuition. *(English: an AI-automation demo for small businesses —
documents in, validated structured data out — built to show measured, documented engineering
decisions rather than demos that merely look good.)*

## Ce que ça fait
| Capacité | Contenu |
|---|---|
| Extraction | Facture PDF, image ou dictée → JSON validé par un schéma, règles métier (totaux, taxes) |
| Revue humaine | File « à relire » (une dictée l'est toujours), approbation, correction, piste d'audit |
| Recherche | Mini-RAG sur les contrats : mots-clés, sens (embeddings locaux) ou hybride |
| Agent | Outils typés (recherche, liste, vérification, export) ; **l'export exige l'accord d'un humain** |
| Coûts | Journal de chaque appel : tokens, coût, latence, ventilé par modèle, tâche et jour |

## Résultats mesurés
Tous les rapports sont dans [`docs/evaluation/`](docs/evaluation/), avec leurs limites.

| Question | Résultat |
|---|---|
| Extraction de factures (24 factures, 2 passes) | Haiku 5.5 avec un prompt amélioré : **100 %** de factures parfaites (IC 95 % : 92,6–100 %), à 0,0006 $ la facture |
| Audio (Whisper local, 12 dictées) | Le modèle `small` est le meilleur des trois testés, mais les dictées denses restent difficiles : taux d'erreur de mots **41,9 %** |
| Recherche (24 questions) | MRR : mots-clés 0,649 ; **sens 0,851** ; hybride 0,829 → le mode « sens » est retenu par une règle posée avant la mesure |
| Agent (12 questions, 3 passes) | Haiku **91,7 %**, Sonnet 94,4 %, **0 action non sûre** pour les deux ; Haiku est ~20 fois moins cher |

## Limites, dites franchement
- Les jeux de test sont **synthétiques** et écrits par l'auteur : les pourcentages indiquent une
  tendance, pas une garantie sur des documents réels.
- Le juge de l'évaluation de l'agent est **mécanique** : une bonne réponse reformulée peut être comptée fausse.
- L'audio utilise des **voix de synthèse** ; des voix humaines seront plus difficiles.
- **Pas d'interface finale** : l'API est complète, mais les écrans Angular (story 06b) attendent
  leur design. Une page de test sommaire existe (`/test-page`).
- Le parcours Docker complet n'a pas encore été vérifié de bout en bout sur une machine neuve.
- Base SQLite et un seul utilisateur (V1) ; PostgreSQL, authentification et déploiement sont en V2
  ([`docs/roadmap.md`](docs/roadmap.md)).

## Architecture en bref
Monorepo : `backend/` (FastAPI, Python 3.12), `frontend/` (Angular 21), `demo-data/`, `docs/`.
Le backend est organisé **par domaine** (`extraction`, `review`, `search`, `agent`, `llm`,
`costs`…) avec des **ports et adaptateurs** : le modèle de langage, la transcription, les
embeddings et la recherche sont des interfaces, remplaçables et testables avec des faux. Les
décisions sont consignées dans [`docs/architecture.md`](docs/architecture.md).

## Lancer le projet
Prérequis : Docker.

```bash
cp .env.example .env          # puis renseigner ANTHROPIC_API_KEY pour les fonctions payantes
docker compose up --build
```

- API : http://localhost:8010/health — documentation interactive : http://localhost:8010/docs
- Page de test (pour essayer chaque fonction) : http://localhost:8010/test-page
- Interface Angular (squelette) : http://localhost:4200
- Exemples de requêtes prêts à lancer : dossier [`http/`](http/)

Les fonctions locales (recherche, revue, coûts) ne coûtent rien. Une extraction ou une question
à l'agent coûte environ 0,0005 $ avec Haiku 5.5.

## Développement sans Docker
```bash
# Backend (Python 3.12)
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
black app tests && ruff check app tests
uvicorn app.main:app --port 8010

# Frontend
cd frontend
npm install
npx ng test --watch=false
```
Les tests n'appellent jamais l'API payante : ils utilisent des faux fournisseurs. L'évaluation
réelle se lance à part (`python -m app.evaluation --help`, qui annonce le coût avant d'exécuter).

## Documentation
- Parcours pédagogique (Python, FastAPI, tests, LLM, RAG, agent…) : [`docs/apprentissage/`](docs/apprentissage/README.md)
- Pratiques d'intégration d'IA couvertes et restantes : [`docs/standards-ia.md`](docs/standards-ia.md)
- Cadrage produit : [`docs/produit.md`](docs/produit.md) — suivi des stories : [`docs/suivi-stories.md`](docs/suivi-stories.md)
- Audit avant publication : [`docs/securite-publication.md`](docs/securite-publication.md)

## Licence
[MIT](LICENSE).
