# Produit — Bureau IA (deskPilot)

## Vision
Démonstrateur d'automatisation IA pour PME : transformer des documents non structurés
(PDF, images scannées, enregistrements audio) en données structurées validées, avec un
agent IA qui utilise des outils (dont le mini-RAG). Projet d'apprentissage orienté
« AI engineer » : il doit montrer des compétences recherchées, avec des chiffres.

## Public
- Employé de PME (comptabilité, juridique, administration) : utilisateur non technique.
- Recruteurs et clients potentiels : jugent la qualité du projet en quelques minutes.

## Constat du marché (benchmark de novembre 2026)
- Socle des offres AI engineer : Python, LLM, RAG, cloud (analyse de 3 449 offres).
- Plus de la moitié des offres demandant des compétences IA sont hors IT (finance, santé, RH).
- Pas de donnée fiable sur la part des offres citant l'extraction de documents ou les
  agents : hypothèse à vérifier en lisant 20 à 30 offres de la cible (finance, Québec).
- Pour l'extraction de documents, le consensus est une architecture hybride : parsing
  dédié pour les documents structurés, LLM pour le sémantique, revue humaine pour le doute.
- Il n'existe pas de classement indépendant des LLM sur factures et contrats : un banc
  d'évaluation reproductible est un livrable de valeur.

## Périmètre V1
Domaine de démonstration : factures et contrats de PME.

| Capacité | Contenu |
|---|---|
| Ingestion | PDF, image/scan, audio |
| Extraction | Schéma par type de document, sortie JSON validée |
| Contrôle | Règles métier, score de confiance par champ, file de revue humaine |
| Agent | Outils : recherche dans les documents (mini-RAG), vérification, export |
| Évaluation | Jeu annoté, précision par champ, coût et latence, comparaison de modèles |

## Écrans
Dépôt, Résultat, Revue, Agent, Évaluation et coûts. Libellés en français, bascule FR/EN.

## Hors périmètre V1 (voir roadmap.md)
Multi-utilisateurs, authentification, PostgreSQL, fine-tuning, orchestration multi-agents.
