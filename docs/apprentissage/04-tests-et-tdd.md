# 04 — Tests et TDD

## Le cycle
1. **Rouge** : écrire un test pour un comportement qui n'existe pas encore, le lancer, le voir
   échouer (pour de bonnes raisons).
2. **Vert** : écrire le code le plus simple qui le fait passer.
3. **Nettoyage** : améliorer le code sans casser les tests.

C'est exactement ce qu'on a fait pour `/health`, les modèles et le démarrage de l'application.
Un test qui n'a jamais été rouge ne prouve pas qu'il teste quelque chose.

## pytest (Python)
Un test est une fonction dont le nom commence par `test_`. `backend/tests/test_health.py` :

```python
def test_health_returns_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```
- Structure **Arrange / Act / Assert** : préparer, agir, vérifier (séparés par des lignes vides).
- `assert` : si l'expression est fausse, le test échoue.
- `TestClient` simule des requêtes sans lancer de vrai serveur.

### Outils de pytest utilisés
- `tmp_path` : un dossier temporaire neuf, fourni automatiquement à un test.
- `monkeypatch` : modifier temporairement une variable d'environnement le temps d'un test.
- Base `sqlite://` (sans fichier) : une base en mémoire, qui disparaît après le test.

### Détail utile : `with TestClient(...)`
Le démarrage de l'application (`lifespan`) ne s'exécute **que** dans un bloc `with`.
Le test `test_startup_creates_database_tables` l'utilise donc pour vérifier que le fichier
de base est créé. Sans `with`, rien ne démarre.

## Vitest (Angular)
Côté frontend, les tests sont dans `frontend/src/app/app.spec.ts` (`describe` / `it`,
comme Jest). Ils montent le composant, cliquent sur le bouton « EN » et vérifient que le titre
passe à « AI Desk ».

Piège rencontré : le titre ne se mettait pas à jour dans le test. Cause : la configuration
de test n'avait pas `reRenderOnLangChange: true`, que l'application avait. Moralité : un
test doit reproduire la configuration réelle.

## Commandes
```bash
cd backend && source .venv/bin/activate && pytest          # tout
pytest tests/test_health.py -v                             # un fichier, détaillé
cd frontend && npx ng test --watch=false
```

## Pourquoi on teste autant
Avec des LLM, les erreurs sont silencieuses : une réponse plausible mais fausse. Les tests
et, plus tard, l'évaluation (story 03) sont ce qui rend le projet digne de confiance.

## Exercice
Dans `test_health.py`, change `"ok"` en `"nok"` et lance `pytest`. Lis le message d'erreur
en entier : repère la ligne du test, la valeur attendue et la valeur reçue. Remets ensuite
`"ok"`.
