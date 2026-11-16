# Bureau IA (deskPilot)

Démonstrateur d'automatisation IA pour PME : transformer des documents (PDF, images, audio)
en données structurées validées, avec un agent IA et une évaluation chiffrée.
Projet d'apprentissage en ingénierie IA, en cours de construction (V1).

## Lancer le projet

Prérequis : Docker.

```bash
cp .env.example .env
docker compose up --build
```

- Interface : http://localhost:4200 (français par défaut, bascule FR/EN en haut à droite)
- API : http://localhost:8010/health

## Développement sans Docker

```bash
# Backend (Python 3.12)
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest

# Frontend
cd frontend
npm install
npx ng test --watch=false
```

## Documentation

- Cahier des charges : `docs/cahier-des-charges.md` (à venir)
- Produit : `docs/produit.md`
- Architecture : `docs/architecture.md`
- Suivi des stories : `docs/suivi-stories.md`
