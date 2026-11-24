# 16 — Survivre aux pannes du fournisseur (story 07)

## Pourquoi
Un service qui appelle un fournisseur externe (ici Anthropic) en dépend : limite de débit (429),
panne ou surcharge (5xx), réponse trop lente, clé invalide. Avant cette story, toutes ces
situations remontaient en **erreur 500 brute** et le SDK retentait deux fois **en silence**. Un
service de production doit, face à une panne : retenter quand c'est utile, abandonner quand c'est
inutile, et répondre à son client avec un message clair.

## Les notions
| Notion | En une phrase | Où dans le projet |
|---|---|---|
| Erreur passagère ou définitive | Une panne qui peut disparaître (429, 5xx, délai) se retente ; une requête invalide ou une clé fausse non | `LLMProviderError.retryable` |
| Délai croissant (*exponential backoff*) | On attend 1 s, puis 2 s, puis 4 s… : on laisse au fournisseur le temps de se rétablir | `RetryingProvider._delay` |
| Hasard (*jitter*) | On raccourcit le délai de 0 à 50 % au hasard, pour que mille clients en échec ne retentent pas tous à la même seconde | `jitter` |
| `retry-after` | Le fournisseur dit lui-même combien attendre ; on lui obéit, sauf si c'est plus long que notre maximum | `LLMRateLimitedError.retry_after` |
| Enrobage (*wrapper*, décorateur) | Une classe qui respecte le même contrat que celle qu'elle contient et ajoute un comportement | `RetryingProvider` |
| Couche anticorruption | Une seule classe connaît le SDK et traduit ses erreurs en erreurs à nous | `translate_error` |
| Idempotence | Rejouer une opération donne le même résultat sans effet de bord | voir plus bas |

## Les fichiers
- `app/domains/llm/errors.py` : la hiérarchie `LLMProviderError` avec ses cinq sous-classes
  (`LLMRateLimitedError`, `LLMUnavailableError`, `LLMTimeoutError` : retentables ;
  `LLMAuthenticationError`, `LLMRequestRejectedError` : définitives).
- `app/domains/llm/providers/anthropic.py` : `translate_error`, seul endroit qui connaît les
  erreurs du SDK. Le reste du code n'importe jamais `anthropic.RateLimitError`.
- `app/domains/llm/providers/retrying.py` : `RetryingProvider`, qui enrobe n'importe quel
  `LLMProvider`.
- `app/domains/llm/providers/factory.py` : assemble le tout (SDK sans retentatives propres, délai
  maximum, `RetryingProvider` autour).
- `app/api/llm_errors.py` : **un seul** gestionnaire qui transforme ces erreurs en réponses HTTP
  pour toutes les routes (extraction, agent, `/llm/complete`…).

## Ce qui se passe, pas à pas
```
route ─► LLMService ─► RetryingProvider ─► AnthropicProvider ─► SDK ─► Anthropic
                              │                    │
                   retente si retryable      traduit l'erreur du SDK
```
1. Le SDK lève par exemple `RateLimitError`. `AnthropicProvider` la traduit en `LLMRateLimitedError`
   (en gardant l'original attaché : `raise … from error`).
2. `RetryingProvider` voit `retryable = True`, attend, et réessaie, jusqu'à `LLM_MAX_RETRIES` fois.
3. Si tout échoue, l'erreur remonte jusqu'au gestionnaire FastAPI, qui répond en français sans
   détail technique (adresses, noms de classes).

| Panne | Retentée ? | Réponse HTTP |
|---|---|---|
| Limite de débit (429) | oui | 503 + en-tête `Retry-After` s'il est connu |
| Panne ou surcharge (5xx, 529, connexion) | oui | 502 |
| Délai dépassé | oui | 504 |
| Clé absente ou refusée (401, 403) | non | 503 (« vérifiez la clé ») |
| Requête rejetée (400, 404…) | non | 502 |

Pourquoi 503 pour la clé : c'est un problème de configuration du service, pas une faute du client.

## Pourquoi ne pas retenter une requête invalide
Retenter un 400 ne le répare pas et **coûte de l'argent** : chaque essai est facturé s'il part. Même
logique pour un refus du modèle (`LLMRefusedError`) : la réponse sera la même.

## Choix et alternatives écartées
- **Enrobage plutôt que réglages du SDK.** Le SDK sait retenter, mais en silence, avec ses propres
  règles, et on ne le teste pas facilement. On le coupe (`max_retries=0`) : deux couches de
  retentatives se multiplieraient (3 × 3 essais).
- **Le temps est injecté.** `RetryingProvider` reçoit `sleep` et `jitter` en paramètres : les tests
  passent de faux (`sleeps.append`) et s'exécutent en quelques millisecondes, sans dormir. Comparaison
  PHP : on injecte une horloge (`ClockInterface`) au lieu d'appeler `sleep()` directement.
- **Pas de repli vers un autre modèle ici.** Remplacer Haiku par Sonnet en cas de panne change la
  qualité et le coût : c'est une décision à mesurer par l'évaluation, donc une autre story.
- **Pas de coupe-circuit** (cesser d'appeler un fournisseur manifestement en panne) : utile sous
  trafic réel, inutile pour une démo.

## Idempotence : pourquoi on peut retenter sans danger
Un appel au modèle est **sans effet de bord** : il renvoie du texte, il n'écrit rien chez le
fournisseur. Le rejouer est donc sûr. Ce n'est pas vrai de tout : un outil d'agent qui exporte un
fichier ne doit pas être rejoué à l'aveugle. C'est pourquoi les retentatives vivent **au niveau du
fournisseur** (l'appel au modèle) et jamais autour de l'exécution des outils.

## Limites connues
- Un appel qui échoue **après** avoir consommé des jetons (coupure en cours de réponse) n'est pas
  journalisé dans `api_calls` : le journal ne compte que les appels réussis. Le coût réel peut donc
  être légèrement plus élevé que le coût affiché.
- La latence mesurée par le journal inclut les attentes entre tentatives : après une panne, un
  appel « lent » peut simplement avoir été retenté.
- Les relances ont lieu en direct dans la requête : pendant l'attente, le client attend aussi. Une
  file de tâches en arrière-plan est une autre pratique (pipeline asynchrone), prévue plus tard.

## À essayer
1. Lancer `pytest tests/llm/test_retrying_provider.py -v` et lire les noms des tests : ils décrivent
   le comportement.
2. Dans `backend/`, mettre `LLM_MAX_RETRIES=0` dans `.env`, recréer le conteneur, puis refaire un
   appel : une panne remonte tout de suite.
3. Mettre une fausse clé (`ANTHROPIC_API_KEY=x`) : `/llm/complete` répond 503 avec le message « vérifiez
   la clé », sans nouvelle tentative.
4. Lire dans les journaux du conteneur (`docker compose logs backend`) les lignes « nouvelle tentative ».

## Exercices
1. Ajouter à `RetryingProvider` un plafond de temps total (par exemple 30 s toutes tentatives
   comprises). Écrire le test d'abord.
2. Pourquoi `retry_after` n'est-il pas passé dans le hasard (`jitter`) ? (Indice : qui décide du
   bon moment, le fournisseur ou nous ?)
3. Que se passerait-il si on enrobait aussi l'exécution des outils de l'agent ? Donner un exemple
   où cela fait mal.
