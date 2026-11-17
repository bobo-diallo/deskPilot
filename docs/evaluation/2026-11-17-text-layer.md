# Rapport d'évaluation — 2026-11-17

Jeu de 14 factures, 1 répétition(s) par facture et par variante.

## Résumé

| Variante | Factures parfaites | Coût par facture | Latence médiane (p90) | Valeurs inventées | Échecs |
|---|---|---|---|---|---|
| sonnet-text | 100,0 % (IC 95 % : 78,5 % à 100,0 %) | 0,0063 $ | 2,5 s (4,2 s) | 0 | 0 |
| haiku-text | 100,0 % (IC 95 % : 78,5 % à 100,0 %) | 0,0004 $ | 2,8 s (3,4 s) | 0 | 0 |

## Exactitude par champ

| Champ | sonnet-text | haiku-text |
|---|---|---|
| Fournisseur | 100,0 % | 100,0 % |
| Numéro de facture | 100,0 % | 100,0 % |
| Date | 100,0 % | 100,0 % |
| Devise | 100,0 % | 100,0 % |
| Total hors taxes | 100,0 % | 100,0 % |
| Taxes | 100,0 % | 100,0 % |
| Total toutes taxes | 100,0 % | 100,0 % |
| Nombre de lignes | 100,0 % | 100,0 % |
| Montants des lignes | 100,0 % | 100,0 % |
| Descriptions des lignes | 100,0 % | 100,0 % |

## Factures parfaites par difficulté

| Difficulté | sonnet-text | haiku-text |
|---|---|---|
| Date ambiguë | 100,0 % | 100,0 % |
| Quantité décimale | 100,0 % | 100,0 % |
| PDF numérique | 100,0 % | 100,0 % |
| En anglais | 100,0 % | 100,0 % |
| Numéro absent | 100,0 % | 100,0 % |
| Plusieurs taxes | 100,0 % | 100,0 % |
| Ligne de remise | 100,0 % | 100,0 % |
| Montant de 1 000 ou plus | 100,0 % | 100,0 % |

## Fiabilité du statut « validé »

Une extraction est « validée » quand les montants se recoupent. Mais une erreur cohérente passe entre les mailles.

| Variante | Part réellement parfaite parmi les « validées » | Erreurs détectées (à relire) | Erreurs silencieuses |
|---|---|---|---|
| sonnet-text | 100,0 % | — | 0 essai(s) |
| haiku-text | 100,0 % | — | 0 essai(s) |

_Erreurs silencieuses_ : extraction fausse, mais marquée « validée ».

## Comparaison avec la référence (sonnet-text)

Écart apparié, calculé cas par cas, avec intervalle de confiance à 95 % obtenu en rééchantillonnant les cas. Si l'intervalle contient 0, l'écart peut être du hasard.

| Variante | Écart de factures parfaites | IC 95 % | Écart d'exactitude moyenne par champ | IC 95 % |
|---|---|---|---|---|
| haiku-text | +0,0 pts | +0,0 pts à +0,0 pts | +0,0 pts | +0,0 pts à +0,0 pts |

## Limites

- Factures synthétiques : plus propres que des documents réels ; le bruit des scans reste léger.

- Seulement 14 cas : les intervalles de confiance sont larges, conclure avec prudence.

- Les répétitions d'un même cas ne sont pas indépendantes : l'intervalle du résumé est indicatif, la comparaison appariée est plus fiable.

- Les réponses d'un modèle varient d'un appel à l'autre ; les coûts sont ceux du journal `api_calls`.
