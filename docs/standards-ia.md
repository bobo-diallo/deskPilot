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

## Comment s'en servir
- Avant une story, regarder quelles lignes elle fait avancer.
- Un entretien d'AI engineer parle de la plupart de ces points : savoir expliquer chaque
  ligne ✅ avec un exemple de ce projet est un bon objectif de fin de parcours.
