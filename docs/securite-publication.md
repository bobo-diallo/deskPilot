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
- L'adresse e-mail personnelle de l'auteur figure dans 71 commits (auteur et validateur). C'est
  courant sur les dépôts publics ; le risque (spam, hameçonnage) est modéré et accepté.
  **Décision de l'auteur : on la garde.** Une réécriture de l'historique avait été préparée et
  vérifiée, puis abandonnée : GitHub conserve une référence cachée par pull request qui aurait
  gardé l'ancienne adresse, ce qui aurait imposé un second dépôt à maintenir.
- Pour les futurs commits, GitHub propose une adresse `noreply` (Settings > Emails).

## Nettoyage
- Le dossier `experiments/` (essai Docling) est supprimé ; ses résultats sont conservés dans
  `docs/evaluation/2026-11-17-docling-spike.md`.

## Rappel
Une clé qui a fuité se **révoque** : réécrire l'historique ne suffit pas, car elle a pu être copiée
dès sa publication.
