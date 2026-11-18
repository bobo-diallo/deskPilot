# Rapport d'évaluation — 2026-11-17

Jeu de 12 factures, 2 répétition(s) par facture et par variante.

## Résumé

| Variante | Factures parfaites | Montants et date exacts | Coût par facture | Latence médiane (p90) | Erreurs sur les mots | Temps de calcul / durée audio | Valeurs inventées | Échecs |
|---|---|---|---|---|---|---|---|---|
| whisper-tiny-haiku | 0,0 % (IC 95 % : 0,0 % à 13,8 %) | 0,0 % | 0,0005 $ | 19,4 s (41,7 s) | 90,8 % | 0,47 | 0 | 13 |
| whisper-base-haiku | 0,0 % (IC 95 % : 0,0 % à 13,8 %) | 0,0 % | 0,0005 $ | 19,1 s (38,1 s) | 67,8 % | 0,53 | 0 | 11 |
| whisper-small-haiku | 0,0 % (IC 95 % : 0,0 % à 13,8 %) | 25,0 % | 0,0008 $ | 54,1 s (74,6 s) | 41,9 % | 1,30 | 0 | 2 |

## Exactitude par champ

| Champ | whisper-tiny-haiku | whisper-base-haiku | whisper-small-haiku |
|---|---|---|---|
| Fournisseur | 16,7 % | 12,5 % | 54,2 % |
| Numéro de facture | 0,0 % | 8,3 % | 33,3 % |
| Date | 25,0 % | 20,8 % | 83,3 % |
| Devise | 33,3 % | 25,0 % | 91,7 % |
| Total hors taxes | 8,3 % | 20,8 % | 83,3 % |
| Taxes | 4,2 % | 25,0 % | 66,7 % |
| Total toutes taxes | 0,0 % | 25,0 % | 66,7 % |
| Nombre de lignes | 25,0 % | 45,8 % | 91,7 % |
| Montants des lignes | 0,0 % | 8,3 % | 41,7 % |
| Descriptions des lignes | 0,0 % | 8,3 % | 12,5 % |

## Factures parfaites par difficulté

| Difficulté | whisper-tiny-haiku | whisper-base-haiku | whisper-small-haiku |
|---|---|---|---|
| Voix à accent canadien | 0,0 % | 0,0 % | 0,0 % |
| Quantité décimale | 0,0 % | 0,0 % | 0,0 % |
| Débit rapide | 0,0 % | 0,0 % | 0,0 % |
| Plusieurs taxes | 0,0 % | 0,0 % | 0,0 % |
| Ligne de remise | 0,0 % | 0,0 % | 0,0 % |
| Bruité (scan ou enregistrement) | 0,0 % | 0,0 % | 0,0 % |
| Numéro épelé | 0,0 % | 0,0 % | 0,0 % |
| Montant de 1 000 ou plus | 0,0 % | 0,0 % | 0,0 % |

## Fiabilité du statut « validé »

Une extraction est « validée » quand les montants se recoupent. Mais une erreur cohérente passe entre les mailles.

| Variante | Part réellement parfaite parmi les « validées » | Erreurs détectées (à relire) | Erreurs silencieuses |
|---|---|---|---|
| whisper-tiny-haiku | — | 100,0 % | 0 essai(s) |
| whisper-base-haiku | — | 100,0 % | 0 essai(s) |
| whisper-small-haiku | 0,0 % | 63,6 % | 8 essai(s) |

_Erreurs silencieuses_ : extraction fausse, mais marquée « validée ».

## Comparaison avec la référence (whisper-tiny-haiku)

Écart apparié, calculé cas par cas, avec intervalle de confiance à 95 % obtenu en rééchantillonnant les cas. Si l'intervalle contient 0, l'écart peut être du hasard.

| Variante | Écart de factures parfaites | IC 95 % | Écart d'exactitude moyenne par champ | IC 95 % |
|---|---|---|---|---|
| whisper-base-haiku | +0,0 pts | +0,0 pts à +0,0 pts | +8,7 pts | -4,6 pts à +22,5 pts |
| whisper-small-haiku | +0,0 pts | +0,0 pts à +0,0 pts | +51,2 pts | +37,1 pts à +64,2 pts |

## Limites

- Factures synthétiques : plus propres que des documents réels ; le bruit des scans reste léger.

- Seulement 12 cas : les intervalles de confiance sont larges, conclure avec prudence.

- Les répétitions d'un même cas ne sont pas indépendantes : l'intervalle du résumé est indicatif, la comparaison appariée est plus fiable.

- Les réponses d'un modèle varient d'un appel à l'autre ; les coûts sont ceux du journal `api_calls`.

- Dictées en voix de synthèse (macOS) : plus nettes et régulières qu'une voix humaine ; le bruit ajouté est un bruit blanc léger, loin d'une vraie pièce bruyante.

- « Factures parfaites » exige aussi les noms propres et les descriptions, que l'oreille (donc Whisper) ne peut pas garantir. La colonne « Montants et date exacts » a été ajoutée après la première mesure, quand tous les scores sont tombés à 0 % : c'est une analyse a posteriori, à confirmer sur un jeu neuf.

- Le taux d'erreurs sur les mots compare la transcription au texte lu ; les nombres sont comparés après retrait de l'espace des milliers.
