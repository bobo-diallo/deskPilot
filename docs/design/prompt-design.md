# Prompt de design (à coller dans Claude)

Ce prompt sert à concevoir l'identité visuelle et les écrans de Bureau IA avec Claude
(claude.ai, ou Claude Design si tu y as accès). Colle le bloc ci-dessous, puis réponds à ses
questions. Quand le résultat te plaît, enregistre-le dans `docs/design/` (captures, charte,
lien du prototype) pour que Claude Code l'utilise dans l'implémentation Angular.

````
Tu es designer produit senior et spécialiste de l'accessibilité. Tu m'aides à concevoir
« Bureau IA », une application web de démonstration d'automatisation IA pour PME.

# 1. Le produit
Bureau IA transforme des documents non structurés (PDF, images scannées, enregistrements
audio) en données structurées validées. Un agent IA peut utiliser des outils (recherche
dans les documents, vérification d'un champ, export). Une page d'évaluation montre la
précision par champ, le coût et la latence de chaque modèle (modèles cloud et modèles
open source locaux).
Domaine de démonstration : factures et contrats de PME. Tout le contenu est fictif.

# 2. Les publics
- Employé de PME (comptabilité, juridique, administration) : non technique, veut gagner du
  temps et être sûr que les chiffres extraits sont justes.
- Recruteur ou client potentiel : regarde le projet 2 minutes et doit comprendre la valeur
  tout de suite. L'écran « Résultat » est celui qui doit l'impressionner.

# 3. Les cinq écrans (navigation latérale)
1. Dépôt : glisser-déposer PDF, image ou audio ; choix du type de document (facture,
   contrat, rapport, compte rendu) ; fichiers récents avec statut.
2. Résultat : document source à gauche, champs extraits à droite avec une puce de confiance
   (élevée, moyenne, faible) ; survoler un champ met en évidence sa zone dans le document ;
   exporter en CSV ou JSON.
3. Revue : file des extractions douteuses ; corriger, valider ou rejeter ; montrer l'ancienne
   et la nouvelle valeur.
4. Agent : conversation ; chaque outil appelé par l'agent s'affiche comme une étape
   dépliable (nom de l'outil, entrée, résultat).
5. Évaluation et coûts : précision par champ, comparaison de modèles, coût et latence par
   document, graphiques sobres.

# 4. Contraintes non négociables
- Interface en français, avec bascule FR/EN visible dans l'en-tête. Jamais de valeur
  technique brute à l'écran : « confidence_low » s'affiche « Confiance faible ».
- Accessible (WCAG 2.2 AA) : contrastes, navigation au clavier, états de focus visibles,
  l'information ne repose jamais sur la couleur seule (ajouter une icône ou un texte).
- Mode clair et sombre.
- Responsive : portable et grand écran (le tableau de bord peut passer en une colonne).
- Implémentable avec Angular Material : réutiliser ses composants (tableaux, cartes,
  onglets, boîtes de dialogue, puces, menus) plutôt qu'inventer des composants exotiques.
- Chaque écran montre quatre états : vide, chargement, erreur, succès.

# 5. Ton et style
Sobre, professionnel, rassurant, lisible. Pas de décoration gratuite. Données chiffrées
mises en valeur. Inspiration : outils de gestion modernes (Linear, Stripe Dashboard),
sans les copier.

# 6. Méthode de travail (suis cet ordre)
Étape A. Pose-moi jusqu'à 5 questions qui t'aideraient à mieux concevoir, puis attends
mes réponses.
Étape B. Propose le parcours utilisateur et l'arborescence des écrans en quelques lignes ;
attends mon accord.
Étape C. Propose une charte : palette (variables de couleur clair et sombre), typographie,
échelle d'espacement, rayons, ombres, et les composants récurrents (puce de confiance, carte
de champ, ligne de fichier, étape d'agent).
Étape D. Construis un prototype cliquable (HTML) des 5 écrans avec des données crédibles :
3 factures, 1 contrat, 1 enregistrement de réunion.
Étape E. Fais une revue critique de ton propre travail (accessibilité, cohérence, points
faibles) et propose les corrections.

# 7. Livrables finaux
- Le prototype navigable.
- La charte en variables CSS (couleurs, typographie, espacements).
- Pour chaque écran : la liste des composants et des états.
- Une courte liste de décisions de design, avec leur raison.
````

## Après le design

Rapporte-moi (dans Claude Code) le lien ou les fichiers produits. Je les rangerai dans
`docs/design/` et les transformerai en thème Angular, étape par étape, avec des tests.
