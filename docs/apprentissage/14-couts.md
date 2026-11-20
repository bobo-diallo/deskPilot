# 14 — Lire le journal des coûts (story 06a)

## Pourquoi
Depuis la story 01, chaque appel au modèle est écrit dans la table `api_calls` (modèle, tokens,
coût, latence). Un journal que personne ne lit ne sert à rien : cette story le **transforme en
chiffres utiles** (combien ça coûte, quel modèle, quelle tâche, à quelle vitesse) pour l'écran
« Coûts » de la story 06b. C'est la base de l'observabilité en IA : on ne maîtrise que ce qu'on mesure.

## Les notions
| Notion | En une phrase | Où dans le projet |
|---|---|---|
| Agrégat SQL | Résumer plusieurs lignes en une : `COUNT`, `SUM` | `CostService.totals` |
| `GROUP BY` | Faire un résumé par groupe (par modèle, par jour) | `CostService._breakdown`, `daily` |
| Percentile (p50, p95) | p95 = la latence que 95 % des appels ne dépassent pas ; la moyenne cache les ratés | `percentile()` |
| Rang le plus proche | Méthode simple de percentile : trier, puis prendre la valeur au rang `ceil(p × n)` | `percentile()` |
| Borne incluse / exclue | Début inclus, fin exclue : deux périodes qui se suivent ne comptent jamais deux fois un appel | `Period` |
| Alias de paramètre | `?from=` est l'URL, mais `from` est un mot réservé de Python | `get_period` (`Query(alias="from")`) |

## Fichiers
- `app/domains/llm/models.py` : nouvelle colonne `task` (extraction, agent, simple). Vide pour
  les appels d'avant la story : ils ressortent avec la clé `null`, on ne les devine pas.
- `app/domains/llm/schemas.py` : `LLMRequest.task`. Les appelants (extracteurs, agent, `/llm/complete`)
  disent pourquoi ils appellent ; `LLMService` l'inscrit dans le journal.
- `app/domains/costs/service.py` : `CostService` (`totals`, `by_model`, `by_task`, `daily`).
- `app/api/costs.py` : `GET /costs/summary` et `GET /costs/daily`, filtrables par `from` et `to`.

## Pourquoi les percentiles sont calculés en Python
SQLite n'a pas de fonction `percentile`. On lit donc les latences par groupe et on les trie en
Python. Avec quelques milliers d'appels, c'est instantané ; avec des millions, on passerait à
PostgreSQL (`percentile_cont`) en V2. Comparaison PHP : c'est un `usort` suivi d'un index, là où
MySQL ne vous offre pas la fonction.

## Comparaison PHP / JavaScript
- `select(func.sum(...)).group_by(...)` ressemble au query builder de Doctrine
  (`->select('SUM(c.cost)')->groupBy('c.model')`).
- `Annotated[..., Depends(...)]` joue le rôle d'un service injecté dans un contrôleur Symfony.

## Changer le schéma sans Alembic
En V1 les tables se créent au démarrage (`create_all`), mais **cette commande n'ajoute pas une
colonne à une table qui existe déjà**. Après cette story, une ancienne base SQLite n'a pas la
colonne `task` : on la supprime et elle se recrée vide au démarrage. Quand le projet aura de vrais
utilisateurs, c'est le travail d'**Alembic** (migrations versionnées), prévu avec PostgreSQL en V2.
Écarté pour l'instant : écrire une mini-migration à la main, du code à maintenir pour un projet
qui n'a pas encore de données à garder.

## À essayer
1. Supprimer `backend/data/deskpilot.db`, relancer le backend, faire quelques appels.
2. Ouvrir `http/costs.http` et lancer `/costs/summary`, puis `/costs/daily`.
3. Regarder p50 et p95 d'une tâche : l'écart dit si quelques appels lents faussent la moyenne.

## Exercices
1. Ajouter `?model=claude-haiku-5-5` pour filtrer le résumé (écrire le test d'abord).
2. Pourquoi la fin de période est-elle exclue dans `Period`, mais incluse dans l'URL ?
   (Indice : regarder `get_period`.)
