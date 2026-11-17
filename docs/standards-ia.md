# Pratiques standard de l'intégration d'IA

Objectif d'apprentissage : à la fin du projet, savoir intégrer des modèles d'IA dans une
application réelle **comme le font les équipes en entreprise**. Ce document liste ces
pratiques, où elles se trouvent dans deskPilot, et ce qui reste à faire. Il est tenu à jour à
chaque story. Légende : ✅ fait, 🔄 en cours, 📋 prévu, ❌ pas encore planifié.

| # | Pratique courante | Dans deskPilot | État |
|---|---|---|---|
| 1 | Appeler le modèle via le SDK officiel, derrière une interface (changer de fournisseur sans refonte) | `LLMProvider`, `AnthropicProvider` (story 01) | ✅ |
| 2 | Sorties structurées : schéma contraint et validé, jamais du texte libre à parser | `messages.parse` + Pydantic (story 02) | ✅ |
| 3 | Suivre tokens, coût et latence de chaque appel | `api_calls`, `LLMService` (story 01) | ✅ |
| 4 | Router les tâches vers le modèle adapté (coût contre qualité) | `router.py` ; décision pilotée par la mesure (story 03) | 🔄 |
| 5 | Évaluer sur un jeu annoté avec des métriques, avant de changer de modèle ou de prompt | module `evaluation` (story 03) | 🔄 |
| 6 | Tests sans réseau avec des faux, tests réels séparés et ignorés sans clé | `FakeProvider`, tests `skipif` | ✅ |
| 7 | Humain dans la boucle pour les cas douteux | statut `needs_review` (story 02), écran Revue (story 05) | 🔄 |
| 8 | Validation métier du résultat du modèle (le modèle peut se tromper avec aplomb) | `validation.py` (story 02) | ✅ |
| 9 | Gérer les refus du modèle | `LLMRefusedError` (story 01) | ✅ |
| 10 | Gérer pannes, timeouts, limites de débit (429), nouvelles tentatives | réglages par défaut du SDK ; pas de traduction en erreur 502 propre | 📋 |
| 11 | Secrets et configuration hors du code | `.env`, `pydantic-settings` | ✅ |
| 12 | Confidentialité : choix API contre modèle local, pas de données réelles dans les démos | ADR 005, données factices | 🔄 |
| 13 | Traitement en masse à moitié prix (Batch API) pour les évaluations | à envisager pour l'évaluation (story 03) | 📋 |
| 14 | Versionner les prompts et relier chaque résultat à la version utilisée | prompts en constantes, sans version | 📋 |
| 15 | Réduire le coût d'un contexte répété (prompt caching) | non étudié | 📋 |
| 16 | Observabilité : journaux structurés, traces (OpenTelemetry) | journal des coûts seulement | ❌ |
| 17 | Agents : boucle d'outils typés, limites de pas, validation des arguments | story 05 | 📋 |
| 18 | RAG : découpage, embeddings, recherche, évaluation de la recherche | mini-RAG, story 05 | 📋 |
| 19 | Garde-fous : injection de prompt, données personnelles | roadmap V2 | ❌ |
| 20 | Intégration continue : tests et lint à chaque PR | pas de pipeline | ❌ |

## Niveau avancé : ce qui distingue un profil senior

Le tableau précédent est le socle que tout projet sérieux doit avoir. Ce second tableau
liste les compétences plus pointues, celles qui font la différence en entretien et sur de
vrais produits. Chacune est rattachée à une story où elle sera réellement pratiquée.

| # | Compétence avancée | Ce qu'on apprend | Où | État |
|---|---|---|---|---|
| A1 | Évaluation rigoureuse : répétitions, intervalles de confiance, seuils décidés avant la mesure, éviter de conclure sur du bruit | Savoir si une différence de score est réelle | story 03 | 🔄 |
| A2 | Évaluation en régression : un score minimal qui bloque une PR (qualité traitée comme les tests) | Éviter qu'un changement de prompt dégrade en silence | story 03 puis CI | 📋 |
| A3 | Analyse d'erreurs par catégorie (étiquettes de difficulté), pas seulement une moyenne | Trouver où le système échoue vraiment | story 03 | 🔄 |
| A4 | Ingénierie des coûts : Batch API, prompt caching, texte extrait au lieu d'images, choix du plus petit modèle suffisant | Diviser la facture sans perdre en qualité | story 03 | 🔄 |
| A5 | Prompts versionnés, comparés par l'évaluation, reliés à chaque résultat | Traiter les prompts comme du code | story 03 | 📋 |
| A6 | Modèles ouverts et inférence locale (Hugging Face, quantification), mesurés contre l'API | Savoir quand « local » est justifié | stories 03 et 04 | 📋 |
| A7 | Résilience : replis entre modèles, coupe-circuit, relances avec délai croissant, idempotence | Un service qui survit aux pannes du fournisseur | à planifier | ❌ |
| A8 | Pipeline asynchrone : file de tâches, traitement en arrière-plan, statut consultable | Les documents lourds ne bloquent pas la requête | à planifier | ❌ |
| A9 | Voix : transcription (Whisper), découpage par locuteur, extraction depuis la transcription | Multimodalité de bout en bout | story 04 | 📋 |
| A10 | Agents avancés : outils typés, limites de pas, validation des arguments, approbation humaine des actions sensibles, évaluation des trajectoires | Un agent fiable, pas une démo | story 05 | 📋 |
| A11 | Protocole MCP : exposer des outils à un agent de façon standard | Interopérabilité des outils | story 05 | 📋 |
| A12 | RAG avancé : recherche hybride (mots-clés plus embeddings), reranking, découpage adapté, métriques de recherche (rappel@k, MRR) | Un RAG mesuré, pas intuitif | story 05 (mini-RAG) | 📋 |
| A13 | Sécurité des LLM : injection de prompt, tests d'attaque (red teaming), masquage des données personnelles | Savoir attaquer et protéger son propre système | V2 | ❌ |
| A14 | Observabilité : traces OpenTelemetry par appel, tableaux de bord de coût et de qualité | Déboguer une chaîne d'IA en production | V2 | ❌ |
| A15 | Gouvernance : piste d'audit, rétention des données, résidence des données | Exigences des clients réglementés (finance) | V2 | ❌ |
| A16 | Distillation / affinage d'un petit modèle à partir des sorties d'un grand | Réduire le coût à grande échelle | V2 | ❌ |
| A17 | Déploiement : intégration continue, conteneurs, configuration par environnement | Livrer comme en entreprise | à planifier | ❌ |

## Comment s'en servir
- Avant une story, regarder quelles lignes elle fait avancer.
- Un entretien d'AI engineer parle de la plupart de ces points : savoir expliquer chaque
  ligne ✅ avec un exemple de ce projet est un bon objectif de fin de parcours.
