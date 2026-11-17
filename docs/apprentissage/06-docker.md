# 06 — Docker

## À quoi ça sert
Docker fait tourner chaque service dans une « boîte » (un **conteneur**) avec exactement
l'environnement voulu. « Ça marche sur ma machine » devient « ça marche partout ».
- **Image** : le modèle (recette figée). **Conteneur** : une instance qui tourne.
- **Dockerfile** : la recette pour construire une image.
- **docker compose** : lance plusieurs conteneurs ensemble, décrits dans un seul fichier.

## `backend/Dockerfile`, ligne par ligne
```dockerfile
FROM python:3.12-slim          # on part d'une image Python 3.12 allégée
WORKDIR /app                   # dossier de travail dans le conteneur
COPY pyproject.toml ./         # copie la liste des dépendances
COPY app ./app                 # copie le code
RUN pip install --no-cache-dir -e .   # installe les dépendances
EXPOSE 8000                    # le service écoute sur le port 8000 (documentation)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]   # commande de départ
```
`uvicorn` est le serveur qui fait tourner FastAPI. `app.main:app` signifie « dans le module
`app/main.py`, prends la variable `app` ». `--host 0.0.0.0` rend le service joignable depuis
l'extérieur du conteneur.

## `docker-compose.yml`
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "${BACKEND_PORT:-8010}:8000"      # port machine : port conteneur
    env_file: [.env]
    volumes:
      - ./backend/data:/app/data          # la base SQLite survit à l'arrêt
  frontend:
    build: ./frontend
    ports: ["4200:4200"]
    depends_on: [backend]
```
- **Ports** `8010:8000` : le port 8010 de ta machine est relié au port 8000 du conteneur.
  Nous utilisons 8010 car le 8000 est pris par un autre de tes projets.
- **Volume** : sans lui, la base disparaîtrait avec le conteneur. Le dossier `backend/data` de
  ta machine est monté dans le conteneur.
- `${BACKEND_PORT:-8010}` : lit la variable `BACKEND_PORT`, sinon 8010.

## Commandes utiles
```bash
docker compose up --build        # construit et lance (Ctrl+C pour arrêter)
docker compose up -d             # idem, en arrière-plan
docker compose ps                # état des services
docker compose logs -f backend   # suivre les journaux
docker compose down              # arrête et supprime les conteneurs
```

## Incident rencontré (à retenir)
`npm ci` a échoué dans l'image avec « package.json and package-lock.json are not in sync ».
Cause : le fichier `package-lock.json` avait été généré par un npm plus ancien que celui de
l'image. Solution : le régénérer avec le même npm.
Leçon : en cas d'erreur, lire le message en entier : il disait exactement ce qui manquait.

## Piège : modifier `.env` ne suffit pas
Compose lit `.env` **à la création** du conteneur. Si tu modifies `.env` pendant qu'il tourne,
`docker compose up -d` ne le recrée pas toujours et le conteneur garde l'ancienne valeur
(ex. : l'API répondait « ANTHROPIC_API_KEY n'est pas configurée » alors que la clé était dans
`.env`). Solution : `docker compose up -d --force-recreate backend`.
Pour vérifier sans afficher le secret : `docker compose exec backend sh -c 'echo ${#ANTHROPIC_API_KEY}'`
affiche la longueur de la valeur (0 = vide).

## Exercice
Lance `docker compose up -d`, puis `docker compose logs backend`. Repère la ligne qui indique
que uvicorn a démarré. Arrête ensuite avec `docker compose down`.
