# Essai Docling (story 03)

Question : Docling (extraction de documents open source, hébergé par la LF AI & Data) peut-il
remplacer ou compléter la lecture directe par Claude ? Essai limité dans le temps, réalisé
le 2026-11-17 sur le jeu d'évaluation de 24 factures. Aucun appel à un modèle : coût nul.

## Lancer l'essai
```bash
docker build -t deskpilot-docling-spike experiments/docling      # ~2 min, image de 2,9 Go
docker run --rm -v "$PWD/demo-data/eval:/data:ro" -v /tmp/docling-out:/out \
  -v docling-cache:/root/.cache deskpilot-docling-spike
```
Nettoyage : `docker rmi deskpilot-docling-spike && docker volume rm docling-cache`.

## Pourquoi dans Docker
Docling dépend de PyTorch. Sur Mac Intel, la dernière version de PyTorch disponible est la
2.2.2, incompatible avec NumPy 2 (`Numpy is not available`), que Docling exige. Dans un
conteneur Linux, les paquets actuels existent et tout fonctionne.

## Résultats
| Mesure | Résultat |
|---|---|
| Rappel de texte (fournisseur, numéro, totaux retrouvés dans le Markdown) | 100 % sur les 24 factures |
| Tableaux | Reconstitués proprement en tableaux Markdown |
| Temps par PDF numérique | 1 à 6 s (la première facture : 69 s, chargement des modèles) |
| Temps par image (OCR) | 13 à 109 s, médiane 28 s, sur CPU Intel |
| Poids | Image Docker de 2,9 Go, téléchargement de modèles au premier lancement |

## Décision : non retenu pour la V1
- Docling produit du **texte**, il reste à faire structurer ce texte par un LLM. Pour les PDF
  numériques, `pypdf` fait déjà aussi bien (100 % sur 14 PDF) en moins d'une seconde.
- Pour les scans, la lecture directe par Claude coûte 0,0005 à 0,009 $ et 3 s ; Docling prend
  une trentaine de secondes de CPU, puis un appel LLM reste nécessaire.
- L'avantage de confidentialité est faible tant que le texte part de toute façon vers l'API :
  il faudrait aussi un LLM local, impraticable sur 16 Go de RAM sans GPU.

À reconsidérer si : un LLM local devient possible (autre matériel), si des documents à mise
en page complexe (tableaux sur plusieurs pages) font échouer la lecture directe, ou si les
volumes justifient d'héberger un service d'extraction.
