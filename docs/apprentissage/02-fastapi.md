# 02 — FastAPI

## Qu'est-ce que c'est
FastAPI est une bibliothèque pour écrire des API web en Python. Elle valide les données avec
des types, et génère **automatiquement une documentation interactive**.
Autres choix possibles : Flask (plus ancien, plus manuel), Django (complet, plus lourd).
On a pris FastAPI parce qu'il est devenu la référence pour les services IA.

## Les fichiers

### `backend/app/api/health.py` — une route
```python
router = APIRouter()

@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```
Un `APIRouter` regroupe des routes. Le décorateur `@router.get("/health")` dit : « les
requêtes GET sur `/health` appellent cette fonction ». Le dictionnaire renvoyé devient du JSON.

### `backend/app/main.py` — construire l'application
```python
def create_app() -> FastAPI:
    ...
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(health.router)
    return app

app = create_app()
```
`create_app()` est une **fabrique** : elle construit une application neuve à chaque appel.
Pourquoi ? Pour les tests, qui peuvent ainsi créer une application avec une autre
configuration. La ligne `app = create_app()` est celle que le serveur (uvicorn) utilise.

### Le démarrage et l'arrêt : `lifespan`
```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    engine = build_engine(settings.database_url)
    init_database(engine)     # exécuté au démarrage : crée les tables
    yield                     # l'application tourne pendant ce temps
    engine.dispose()          # exécuté à l'arrêt : ferme proprement
```
Tout ce qui précède `yield` s'exécute au démarrage, tout ce qui suit à l'arrêt.
`async` / `await` signifient « fonction asynchrone » : elle peut attendre (réseau, disque)
sans bloquer le reste. On les approfondira avec les appels au LLM.

### `backend/app/config.py` — la configuration
```python
class Settings(BaseSettings):
    app_name: str = "Bureau IA"
    database_url: str = "sqlite:///./data/deskpilot.db"
    anthropic_api_key: str = ""
```
`pydantic-settings` lit les variables d'environnement et le fichier `.env`, vérifie leur
type, et applique la valeur par défaut sinon. Le nom `DATABASE_URL` dans `.env`
correspond à `database_url` dans la classe (la casse est ignorée).
Les secrets (clés d'API) vivent dans `.env`, jamais dans le code ni dans git.

## La documentation automatique
Quand l'application tourne, ouvre http://localhost:8010/docs : tu y vois toutes les routes et
tu peux les essayer depuis le navigateur. C'est généré à partir du code (Swagger UI).

## À essayer
1. `docker compose up --build`, puis ouvre `/docs` et exécute `GET /health`.
2. Dans `.env`, change `BACKEND_PORT`, relance, observe.

## Exercice (TDD, on le fera ensemble)
Ajoute une route `GET /version` qui renvoie `{"version": "0.1.0"}`. Écris d'abord le test
dans `backend/tests/`, constate qu'il est rouge, puis écris la route.
