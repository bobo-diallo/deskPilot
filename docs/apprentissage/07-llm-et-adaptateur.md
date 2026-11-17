# 07 — Appeler un LLM proprement (story 01)

## Le problème qu'on résout
Appeler Claude, c'est facile : quelques lignes avec le SDK. Mais si tout le code appelle
directement le SDK, on ne peut plus changer de modèle, tester sans payer, ni savoir ce que ça
coûte. La story 01 met un **adaptateur** entre l'application et les modèles.

```
route /llm/complete → LLMService → LLMProvider (interface)
                          │             ├─ AnthropicProvider (vrai Claude)
                          │             └─ FakeProvider (tests)
                          └→ api_calls (coût, tokens, latence)
```

## Les fichiers (`backend/app/domains/llm/`)
| Fichier | Rôle |
|---|---|
| `schemas.py` | `LLMRequest` et `LLMResponse` : le format commun, indépendant du fournisseur |
| `ports.py` | `LLMProvider` : le contrat que tout fournisseur doit respecter |
| `providers/anthropic.py` | Implémentation qui appelle Claude via le SDK `anthropic` |
| `providers/fake.py` | Fausse implémentation : répond toujours pareil, sans réseau |
| `pricing.py` | Tarifs par modèle et calcul du coût d'un appel |
| `router.py` | Choisit le modèle selon la tâche (extraction → Sonnet, simple → Haiku) |
| `service.py` | Appelle le fournisseur, calcule le coût, écrit dans `api_calls` |
| `errors.py` | `LLMRefusedError` : le modèle a refusé de répondre |
| `backend/app/api/llm.py` | La route `POST /llm/complete` |

## Notions Python et architecture

### `dataclass`
```python
@dataclass(frozen=True)
class LLMResponse:
    text: str
    ...
```
Une classe qui sert juste à transporter des données : Python écrit le constructeur pour
toi. `frozen=True` la rend non modifiable (comme un objet valeur en DDD).

### `Protocol` : une interface sans héritage
```python
class LLMProvider(Protocol):
    name: str
    def complete(self, request: LLMRequest) -> LLMResponse: ...
```
Toute classe qui a un `name` et une méthode `complete` compatible **est** un `LLMProvider`,
sans avoir à déclarer `implements` comme en PHP. C'est le principe SOLID « D » (dépendre
d'abstractions) : `LLMService` ne connaît que le contrat.

### Injection de dépendances
`LLMService(provider, session)` reçoit ses collaborateurs au lieu de les créer lui-même.
Les tests lui passent un `FakeProvider` et une base en mémoire : aucun réseau, aucun coût.
FastAPI fait pareil pour les routes avec `Depends(...)` :

```python
provider: Annotated[LLMProvider, Depends(get_llm_provider)]
```
« Pour ce paramètre, appelle `get_llm_provider` et donne-moi le résultat. » Dans les
tests, `app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()` le remplace.

### Pourquoi une fausse implémentation plutôt qu'un « mock »
Le `FakeProvider` est du vrai code simple et lisible, réutilisable partout (tests, démos
hors-ligne). Pour le fournisseur Anthropic, le test utilise un faux client minuscule qui imite
`client.messages.create`, afin de vérifier la traduction des paramètres sans réseau.

### Enum
```python
class Task(Enum):
    EXTRACTION = "extraction"
    SIMPLE = "simple"
```
Un ensemble fermé de valeurs. FastAPI l'utilise pour valider l'entrée : une tâche inconnue
donne automatiquement une erreur 422.

## Les coûts
Un modèle facture au **token** (un morceau de mot), séparément en entrée et en sortie :

```
coût = (tokens_entrée × tarif_entrée + tokens_sortie × tarif_sortie) / 1 000 000
```
Tarifs (novembre 2026, $ par million de tokens) : Sonnet 5.5 à 2 / 10, Haiku 5.5 à 0,10 / 0,50.
Un modèle sans tarif connu lève une erreur : on préfère échouer que facturer 0 sans le dire.
Simplifications assumées : pas de tarif pour le cache ni pour les très longs prompts.

## Le routage
Le plus gros levier de coût est de ne pas utiliser le grand modèle pour tout. Ici, Haiku coûte
20 fois moins que Sonnet. Quand on aura des données (story 03), on mesurera si Haiku suffit
pour certaines extractions.

## Le refus
Claude peut renvoyer `stop_reason == "refusal"` quand un filtre de sécurité se déclenche. Ce
n'est pas une erreur HTTP : la réponse arrive, mais sans contenu utile. On la transforme en
`LLMRefusedError`, que la route traduit en réponse 422.

## À essayer
1. Ouvre http://localhost:8010/docs, déplie `POST /llm/complete`, clique « Try it out »
   et envoie `{"task": "simple", "prompt": "Bonjour"}`. Sans clé, tu obtiens un 503 clair.
2. Avec une clé dans `.env` (`ANTHROPIC_API_KEY=...`), relance `docker compose up -d`,
   refais l'essai et observe `cost_usd`.
3. Regarde le journal : `sqlite3 backend/data/deskpilot.db "select * from api_calls;"`.
4. Lance le test réel : `ANTHROPIC_API_KEY=... pytest tests/llm/test_anthropic_provider.py`.

## Exercice
Ajoute une tâche `Task.SUMMARY` envoyée vers Haiku. Écris d'abord le test dans
`test_router.py`. Le test paramétré `test_every_chosen_model_has_a_known_price` vérifiera
tout seul que le modèle choisi a un tarif.
