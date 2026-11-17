# 09 — Évaluer un système d'IA (story 03)

## Pourquoi c'est la compétence qui compte le plus
Un LLM répond toujours avec aplomb, y compris quand il se trompe. Sans mesure, on choisit un
modèle, un prompt ou un coût « au feeling ». L'évaluation transforme ces choix en décisions
chiffrées et rejouables. C'est ce qui sépare un intégrateur d'un ingénieur IA.

## Les ingrédients
| Notion | En une phrase | Où dans le projet |
|---|---|---|
| Vérité terrain | La bonne réponse, connue d'avance | `demo-data/eval/*.expected.json` |
| Jeu d'évaluation | Des cas variés, étiquetés par difficulté | 24 factures, générées avec une graine fixe |
| Métrique | Un nombre qui résume la qualité | exactitude par champ, factures parfaites |
| Répétitions | Un LLM varie d'un appel à l'autre : on rejoue chaque cas | `--runs` |
| Intervalle de confiance | La marge d'erreur d'un pourcentage | Wilson (`wilson_interval`) |
| Comparaison appariée | Comparer deux variantes **cas par cas** | bootstrap (`paired_bootstrap`) |
| Jeu de validation | Des cas que le réglage n'a jamais vus | `--seed 7` |
| Version de prompt | Un prompt se versionne comme du code | `prompts.py` |

## Fichiers (`backend/app/evaluation/`)
`synthetic.py` (génère les cas) · `render.py` (dessine PDF et images) · `dataset.py` (charge) ·
`metrics.py` (mesures pures) · `runner.py` (exécute et relit coût et latence) ·
`report.py` (rapport Markdown) · `variants.py` (les variantes à comparer) · `cli.py` (la commande).

## Commandes
```bash
cd backend
.venv/bin/python -m app.evaluation --variants sonnet-vision,haiku-vision --runs 3
#   -> affiche l'estimation du coût et s'arrête : rien n'est dépensé sans --yes
.venv/bin/python -m app.evaluation --variants haiku-vision,haiku-vision-v2 --runs 2 --yes
.venv/bin/python scripts/generate_eval_dataset.py --seed 7 --out data/eval-holdout   # jeu neuf
```
Les rapports vont dans `docs/evaluation/`. La clé est lue dans `.env` (ou la variable d'environnement).

## L'histoire de la mesure (ce qui s'est vraiment passé)
1. **Première mesure :** Sonnet 75 %, Haiku 73,6 %. Tous les champs à 100 % sauf la date.
2. **Le jeu avait tort, pas le modèle.** Les erreurs venaient de factures en dollars US avec
   libellés français et date américaine : `05/07/2026` est le 7 mai pour mon générateur, le
   5 juillet pour n'importe quel lecteur. Corrigé, et le rapport v1 est conservé avec un
   avertissement. *Un jeu d'évaluation se vérifie.*
3. **Mesure corrigée :** Sonnet 93,8 %, Haiku 81,2 %. Écart apparié −12,5 pts, intervalle
   [−25,0 ; −2,1] qui exclut 0 : l'écart est réel. Règle posée **avant** (moins de 5 points)
   non satisfaite : Haiku n'est pas adopté tel quel.
4. **Hypothèse :** les erreurs restantes sont des dates américaines lues à l'envers. Un prompt
   v2 ajoute la consigne « mois/jour/année sur une facture américaine ». Haiku passe de 87,5 %
   à 100 % (+12,5 pts, intervalle [+4,2 ; +25,0]).
5. **Piège : la fuite de réglage.** J'ai écrit le prompt v2 en regardant les erreurs de ce
   jeu, puis je l'ai mesuré sur le même jeu. Vérification sur un jeu neuf (graine 7) : v1
   83,3 % contre v2 100 % (+16,7 pts, intervalle [+6,2 ; +29,2]). Le prompt généralise.
6. **Décision :** le routeur envoie l'extraction à Haiku avec le prompt v2 : environ 18 fois
   moins cher (0,0006 $ contre 0,0091 $ par facture), à qualité mesurée supérieure.
   Provisoire : à 100 %, le jeu ne discrimine plus ; il faudra des factures plus difficiles.

## Autres enseignements
- **La réflexion du modèle domine le coût.** Sonnet en texte seul coûte 0,0063 $ contre
  0,0091 $ en vision : −31 % seulement, alors que les tokens d'entrée baissent d'environ 80 %.
  Les tokens de sortie (qui incluent la réflexion) coûtent 5 fois plus cher que ceux d'entrée.
  Piste d'optimisation suivante : régler l'effort de réflexion.
- **Le statut « validé » ne suffit pas.** Avec Haiku v1, de 3 à 5 essais sur 48 selon la
  mesure étaient faux mais marqués « validés » (erreurs silencieuses) : les recoupements de montants ne voient
  pas une date fausse. L'évaluation est le seul filet qui les attrape.
- **Le texte seul égale la vision sur les PDF numériques** (100 % sur 14 cas) pour un coût
  plus bas, mais ne marche pas pour les scans.
- **Docling** (open source) fonctionne dans Docker mais n'apporte rien ici : voir
  `experiments/docling/README.md`.
- **Variance d'une mesure à l'autre :** Haiku v1 a obtenu 81,2 % puis 87,5 % sur le même jeu.
  C'est pourquoi on regarde les intervalles et les comparaisons appariées, pas un seul chiffre.

## Budget réel
Environ 460 appels pour 1,35 $ au total, dont 1,13 $ pour les deux mesures complètes.
La commande demande toujours confirmation avant de dépenser.

## À essayer
1. Ouvre `docs/evaluation/2026-11-17-baseline-v1.md` puis `…-baseline-v2.md` : compare les
   tableaux « Factures parfaites par difficulté ».
2. `.venv/bin/python -m app.evaluation --variants haiku-vision --runs 1 --limit 2` : lis
   l'estimation, puis ce que fait (ou ne fait pas) la commande sans `--yes`.
3. `pytest tests/evaluation -v` : repère les tests de `metrics.py`, ils décrivent chaque règle.

## Exercices
1. Ajoute une variante `sonnet-vision-v2` dans `variants.py` (test d'abord) et estime son coût
   avec la commande avant de la lancer.
2. Une erreur de date n'est pas détectée par `validate_invoice`. Écris une règle qui signale
   une date postérieure à aujourd'hui, avec son test. Que changerait-elle aux « erreurs
   silencieuses » ?
3. Le jeu est trop facile (100 %). Propose trois types de factures plus difficiles à ajouter.
