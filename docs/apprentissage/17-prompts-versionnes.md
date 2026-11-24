# 17 — Prompts versionnés et traçables (story 08)

## Pourquoi
Un prompt décide du comportement du modèle autant que du code décide de celui d'un programme.
Pourtant, on le modifie souvent « juste un peu », sans trace. Trois dangers :
1. **Plus de reproductibilité** : si le texte de `v1` change en place, le rapport d'évaluation de
   `v1` ne dit plus rien de vrai, et personne ne le voit.
2. **Plus de traçabilité** : une extraction enregistrée il y a un mois, quel prompt l'a produite ?
3. **Plus de comparaison** : sans versions, impossible de dire « v2 est meilleur que v1 » avec des chiffres.

Un prompt se traite donc **comme un artefact de livraison** : versionné, figé une fois mesuré, et
relié à chaque résultat qu'il a produit.

## Ce qu'il y avait avant
La story 03 avait déjà posé des versions (`v1`, `v2-date-convention`). Il manquait le lien avec les
résultats, un garde-fou contre la modification en place, et le prompt de l'agent n'était qu'une
constante.

## Les notions
| Notion | En une phrase | Où dans le projet |
|---|---|---|
| Version immuable | On ne modifie jamais une version publiée, on en ajoute une | `PromptSet.versions` |
| Empreinte (*fingerprint*, *hash*) | Un résumé court du texte qui change dès qu'un caractère change | `PromptSet.fingerprint` (SHA-256, 8 caractères) |
| Test « verrou » (*lock*) | Un test qui contient les empreintes connues et échoue si l'une change | `tests/test_prompt_lock.py` |
| Traçabilité | Chaque résultat sait quelle version l'a produit | colonnes `prompt_version` |
| Colonne nullable | Une colonne qui accepte « vide », donc compatible avec les anciennes lignes | `prompt_version: Mapped[str | None]` |

## Les fichiers
- `app/domains/llm/prompts.py` : `PromptSet`, un petit conteneur (nom, versions, version par défaut).
  Il refuse une version inconnue et un défaut qui n'existe pas.
- `app/domains/extraction/prompts.py` : `EXTRACTION_PROMPTS` (l'ancienne API `get_prompt` marche toujours).
- `app/domains/agent/prompts.py` : `AGENT_PROMPTS` (version `v1`).
- `tests/test_prompt_lock.py` : le verrou. Deux tests : aucune version verrouillée n'a changé, et
  **aucune version n'existe sans empreinte verrouillée** (on ne peut pas oublier de verrouiller).
- Extracteurs (`claude.py`, `text_layer.py`, `audio.py`) : renvoient `prompt_version` dans `ExtractionOutput`.
- `ExtractionService` : l'enregistre dans `extractions.prompt_version`.
- `AgentService` : l'enregistre dans `agent_runs.prompt_version`.
- API : `GET /extractions/{id}` et `GET /agent/runs/{id}` exposent `prompt_version`.
- Évaluation : chaque rapport a une section « Versions de prompt » (version et empreinte par variante).

## Le verrou en pratique
Comparaison avec PHP : c'est un `composer.lock` pour le texte des prompts.
```
FAILED test_a_published_prompt_has_not_been_edited_in_place[('extraction', 'v1')]
Le prompt extraction/v1 a changé. Ne le modifie pas : ajoute une nouvelle version, mesure-la avec
l'évaluation, puis verrouille son empreinte dans ce fichier.
```
**Pour modifier un prompt** : ajouter `v3-...` dans le registre, la mesurer (`python -m app.evaluation`),
et seulement alors ajouter son empreinte à `LOCKED` et changer le défaut. Même une faute de frappe
dans `v1` impose de créer une nouvelle version : c'est volontairement strict.

## Reprendre une exécution avec le bon prompt
L'agent peut s'arrêter pour demander une approbation, puis reprendre plus tard. Si le prompt par
défaut a changé entre-temps, reprendre avec le nouveau mélangerait deux consignes dans une même
conversation. `AgentService` relit donc `run.prompt_version` : **une exécution finit avec le prompt
qui l'a commencée**. Il y a un test pour ça.

## Les anciennes lignes
Les extractions et les exécutions d'avant cette story n'ont pas de version : la colonne vaut `null`
et l'API renvoie `null`. On ne devine pas (même règle que pour la colonne `task` de la story 06a).

## Changer le schéma à la main (sans Alembic)
Une colonne ajoutée dans le modèle n'apparaît pas toute seule dans une base qui existe déjà
(`create_all` ne modifie pas les tables existantes). Procédure faite pour cette story :
```bash
docker compose stop backend
cp backend/data/deskpilot.db backend/data/deskpilot.db.bak-before-08      # sauvegarde d'abord
sqlite3 backend/data/deskpilot.db \
  "ALTER TABLE extractions ADD COLUMN prompt_version VARCHAR;
   ALTER TABLE agent_runs  ADD COLUMN prompt_version VARCHAR;"
docker compose up -d backend
```
Une base neuve (tests, nouvelle installation) reçoit les colonnes automatiquement. Écarté :
supprimer la base (perd les données de test) et une mini-migration écrite dans le code (du code à
maintenir pour un cas provisoire). Alembic le fera proprement avec PostgreSQL en V2.

## Choix et alternatives
- **La version, pas le texte, dans la base.** Le texte vit dans Git (son historique) et le verrou
  garantit que « v2-date-convention » désigne toujours le même texte. Stocker le texte à chaque
  ligne gonflerait la base pour rien. Écarté aussi : un registre de prompts en base de données.
- **Sur les résultats, pas sur les appels.** On pourrait aussi mettre la version dans `api_calls`
  pour calculer un coût par version de prompt. C'est utile, mais c'est une autre fonctionnalité.
- **Les variantes d'évaluation déclarent leur version** (`VariantSpec.prompt_version`) et un test
  vérifie que l'extracteur construit utilise bien cette version : on ne peut plus recopier un nom
  de version qui ne correspond à rien. Les variantes audio sont épinglées comme les autres.

## À essayer
1. Lancer `pytest tests/test_prompt_lock.py -v`.
2. Ajouter un espace à la fin de `_V1` dans `extraction/prompts.py`, relancer : le test échoue avec
   le message ci-dessus. Annuler la modification.
3. Déposer une facture sur http://localhost:8010/test-page : la réponse contient
   `"prompt_version": "v2-date-convention"`. Relire une ancienne extraction : `null`.
4. Ouvrir un rapport d'évaluation récent : section « Versions de prompt ».

## Exercices
1. Ajouter une version `v3-...` du prompt d'extraction (par exemple une consigne sur les devises),
   la verrouiller, puis la comparer à `v2` avec `python -m app.evaluation --variants ...`
   (écrire d'abord la variante et son test).
2. Pourquoi l'empreinte ne fait-elle que 8 caractères ? Quel est le risque, et pourquoi est-il
   acceptable ici ? (Indice : on compare quelques versions, pas des millions de fichiers.)
3. Que se passerait-il si `AgentService` utilisait toujours le prompt par défaut en reprise ?
   Écrire le scénario qui poserait problème.
