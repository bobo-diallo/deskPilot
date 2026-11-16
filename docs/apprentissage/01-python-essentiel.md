# 01 — Python essentiel (ce qui apparaît dans le projet)

## Environnement virtuel (`.venv`)
Python installe ses bibliothèques quelque part. Sans précaution, elles se mélangent entre
projets. Un **environnement virtuel** est un dossier à part pour un seul projet.

```bash
cd backend
python3.12 -m venv .venv          # crée le dossier .venv
source .venv/bin/activate         # active : « python » et « pip » pointent maintenant dedans
pip install -e ".[dev]"           # installe les dépendances de pyproject.toml
deactivate                        # sort de l'environnement
```
Équivalent PHP : le dossier `vendor/` de Composer, mais créé et activé explicitement.
Le dossier `.venv` n'est jamais commité (il est dans `.gitignore`).

## `pyproject.toml` : l'identité du projet
Fichier de configuration unique : nom, dépendances (`dependencies`), dépendances de
développement (`[project.optional-dependencies] dev`), et réglage des outils (pytest, Black,
Ruff). C'est le `composer.json` de Python.

## Modules et paquets
- Un fichier `.py` est un **module**. Un dossier avec un `__init__.py` est un **paquet**.
- On importe avec `from app.config import get_settings` : « du module `app/config.py`,
  prends `get_settings` ». Les points correspondent aux dossiers.

## Annotations de type
Python n'impose pas les types, mais on les écrit pour la lisibilité et les outils :

```python
def health() -> dict[str, str]:   # renvoie un dictionnaire texte -> texte
    return {"status": "ok"}

app_name: str = "Bureau IA"        # une variable de type texte
```
`dict` est un tableau associatif (comme un tableau PHP `['status' => 'ok']`).
`list[str]` est une liste de textes.

## Décorateurs
Une ligne qui commence par `@` modifie la fonction juste en dessous :

```python
@router.get("/health")       # « cette fonction répond aux requêtes GET sur /health »
def health(): ...
```
Pour toi : comme une annotation `#[Route('/health')]` en PHP.

## Indentation = structure
Pas d'accolades : le bloc est défini par l'indentation (4 espaces). Une erreur d'indentation
est une erreur de syntaxe.

## `with` : ouvrir puis fermer proprement
```python
with Session(engine) as session:
    ...                      # la session est fermée automatiquement à la sortie du bloc
```
Équivalent de `try/finally` avec fermeture garantie.

## `yield` et fonctions génératrices
`yield` renvoie une valeur sans terminer la fonction. FastAPI s'en sert pour le démarrage
et l'arrêt de l'application (voir guide 02).

## Outils de qualité du code
| Outil | Rôle | Commande |
|---|---|---|
| Black | Formate le code toujours de la même façon | `black app tests` |
| Ruff | Détecte erreurs, imports inutiles, mauvaises habitudes | `ruff check app tests` |

## À essayer
```bash
cd backend && source .venv/bin/activate
python --version
pip list | head
python -c "print('bonjour')"
```

## Exercice
Dans un fichier à part (hors dépôt), écris une fonction `add(a: int, b: int) -> int` puis
appelle-la avec `python`. Que se passe-t-il si tu lui passes du texte ? (Réponse : Python ne
l'empêche pas, c'est pourquoi on teste.)
