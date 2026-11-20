# Audit avant publication du dépôt (story 06c)

Réalisé le 2026-11-20, avant le passage du dépôt en public.

## Secrets
| Contrôle | Résultat |
|---|---|
| `gitleaks git .` (8.30.1) sur tout l'historique : 70 commits hors fusions | **Aucune fuite** |
| Recherche de motifs de clés (`sk-ant-`, `hf_`, `ghp_`) dans tous les commits | Aucune occurrence |
| Fichiers sensibles ou d'éditeur jamais suivis (`.env`, `.idea/`, `*.db`) dans l'historique | Aucun (`git log --all -- .env .idea` vide) |
| `gitleaks dir .` sur le dossier de travail | 1 alerte, dans `.idea/workspace.xml` : fichier **ignoré par git**, valeur vide, jamais commité |

La CI relance `gitleaks` sur tout l'historique à chaque pull request.

## Données personnelles et de démonstration
- Les jeux de démonstration (`demo-data/`) sont synthétiques : fournisseurs, contrats et
  dictées fictifs (voix de synthèse).
- Le compte Google de démonstration est cité dans `CLAUDE.md` ; le compte personnel ne l'est pas.
- L'adresse e-mail de l'auteur figure dans les métadonnées de la majorité des commits (voir la
  décision prise dans `docs/suivi-stories.md`, story 06c).

## Nettoyage
- Le dossier `experiments/` (essai Docling) est supprimé ; ses résultats sont conservés dans
  `docs/evaluation/2026-11-17-docling-spike.md`.

## Rappel
Une clé qui a fuité se **révoque** : réécrire l'historique ne suffit pas, car elle a pu être copiée
dès sa publication.
