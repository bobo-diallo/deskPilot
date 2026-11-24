# 15 — L'écran « Évaluation et coûts » (story 06b)

## Pourquoi
Jusqu'ici, les chiffres du projet vivaient dans des fichiers Markdown (rapports d'évaluation) et
dans une table SQL (journal des coûts). Cette story les rend **lisibles dans un navigateur** :
c'est l'écran qu'un recruteur ou un client regarde en deux minutes. Le frontend n'invente aucun
chiffre : il affiche ce que l'API lui donne.

## Vue d'ensemble
```
navigateur ──/api/costs/…──────────► proxy Angular ──► FastAPI /costs/…       (journal SQLite)
           └─/api/evaluations/…────►               └─► FastAPI /evaluations/… (docs/evaluation/*.md)
```

## Côté backend : lire les rapports (`/evaluations`)
| Fichier | Rôle |
|---|---|
| `app/domains/evaluations/library.py` | `ReportLibrary` : liste les `.md` d'un dossier et les transforme en données (titre, introduction, avertissement, sections, tableaux) |
| `app/api/evaluations.py` | `GET /evaluations/reports` et `GET /evaluations/reports/{id}` |
| `docker-compose.yml` | monte `docs/evaluation/` **en lecture seule** dans le conteneur |

- **Le fichier Markdown reste la source de vérité** : l'API le relit à chaque demande, aucun
  chiffre n'est copié ailleurs. Écarté : stocker les rapports en base (doublon à maintenir).
- **Sécurité** : on ne construit jamais un chemin à partir de ce que le navigateur envoie. L'identifiant
  doit figurer dans la liste des fichiers existants, sinon c'est un 404. Ainsi `../../etc/passwd`
  ne mène nulle part (une attaque « path traversal »). Il y a un test pour ça.
- **Une leçon de données réelles** : le rapport `baseline-v1` commence par un avertissement
  (« jeu de données défectueux ») en citation Markdown. Mon premier analyseur le noyait dans
  l'introduction. Il est maintenant exposé à part (`note`) pour que l'écran le mette en avant.
- Python : une `dataclass` est une classe de données sans constructeur à écrire (comme un DTO PHP) ;
  `Path.glob("*.md")` liste les fichiers (comme `glob()` en PHP).

## Côté frontend : les notions Angular
| Notion | En une phrase | Comparaison | Où |
|---|---|---|---|
| Composant autonome (*standalone*) | Une classe TypeScript + un gabarit HTML + des styles, qui déclare ses propres dépendances | un composant Vue ou React | `costs-block.ts` |
| Service injectable | Une classe partagée, demandée avec `inject(...)` | un service du conteneur Symfony | `CostsService`, `EvaluationsService` |
| `Observable` (RxJS) | Un flux de valeurs dans le temps ; on l'« écoute » | une `Promise` qui peut émettre plusieurs fois | retours de `HttpClient` |
| `switchMap` | À chaque nouvelle valeur, abandonne le flux précédent et en lance un nouveau | `AbortController` + nouveau `fetch` | période, rapport choisi |
| Signal (`signal`, `computed`) | Une valeur réactive ; `computed` se recalcule seul | `ref` / `computed` de Vue | `selectedId`, `cards` |
| `toSignal` | Transforme un flux RxJS en signal lisible par le gabarit | — | `state`, `list`, `report` |
| Routage et chargement à la demande | Une adresse affiche un composant ; `loadComponent` ne le télécharge qu'à l'ouverture | `React.lazy` | `app.routes.ts` |
| Proxy de développement | Le serveur Angular transmet `/api/...` au backend | un `proxy_pass` Nginx | `proxy.conf.js` |
| Angular Material | Bibliothèque de composants accessibles (cartes, tableaux, boutons, champ) | Bootstrap, en plus soigné | partout |
| Transloco | Textes FR/EN lus dans `public/i18n/*.json` ; jamais de texte en dur dans un gabarit | `trans()` de Symfony | `t('costs.title')` |

### Le motif « quatre états »
Chaque bloc est une machine à états : **chargement → erreur | vide | succès**. Le type TypeScript
l'impose :
```ts
type CostsState =
  | { status: 'loading' } | { status: 'error' } | { status: 'empty' }
  | { status: 'ready'; summary: CostSummary; daily: DailyCost[] };
```
Le gabarit ne peut pas afficher des données qui n'existent pas encore, parce que le compilateur
vérifie chaque cas. Comparaison PHP : une union de types plutôt que plusieurs booléens
(`isLoading`, `hasError`…) qui peuvent se contredire.

### Pourquoi `switchMap`
Tu cliques « 7 jours » puis « Tout » très vite. La réponse « 7 jours », plus lente, pourrait arriver
après et écraser « Tout ». `switchMap` abandonne la requête devenue inutile : seule la dernière
demande compte.

### L'histogramme en SVG
Un SVG est du dessin décrit en texte : un `<rect>` par jour, sa hauteur proportionnelle au coût.
Sans bibliothèque de graphiques (écartées : Chart.js, ngx-charts, lourdes pour une seule courbe).
Trois points d'attention, tous appris avec de vraies captures d'écran :
- les positions horizontales sont en **pourcentage** et les hauteurs en pixels fixes : le graphique
  s'étire sans agrandir le texte (ma première version, en `viewBox`, agrandissait les dates) ;
- une **largeur de barre plafonnée** : un seul jour ne doit pas remplir tout le cadre ;
- une **alternative textuelle** : `role="img"` + `aria-label` pour le graphique entier, et un
  `<title>` par barre (jour, coût, appels).

## Accessibilité (WCAG 2.2 AA)
- L'information ne repose jamais sur la couleur seule : la période choisie et la page courante sont
  en gras avec un soulignement ou une bordure ; l'avertissement d'un rapport porte l'étiquette « À noter ».
- Focus clavier visible (contour de 3 px), états annoncés aux lecteurs d'écran
  (`role="status"` pendant le chargement, `role="alert"` en cas d'erreur).
- Thème clair et sombre : **aucune couleur écrite en dur**, uniquement des variables Material
  (`var(--mat-sys-…)`). Un `#fff` oublié rend un texte illisible en mode sombre, c'est arrivé.
- Jamais de valeur technique à l'écran : `claude-haiku-5-5` devient « Claude Haiku 5.5 », une tâche
  inconnue devient « Non renseignée ».

## Tester un composant Angular
- `HttpTestingController` intercepte les appels HTTP : le test dit « cette requête part » puis y
  répond (`flush`) avec des données ou une erreur. Aucun serveur, aucun réseau.
- Le test d'erreur vérifie aussi que « Réessayer » relance bien la requête.
- Piège rencontré : quand deux appels sont lancés ensemble (`forkJoin`) et que le premier échoue,
  le second est **annulé** : le test doit le prévoir.

## Un piège Docker à connaître
L'image du frontend **copie le code au moment du build**. Modifier un fichier ne change donc rien
dans le navigateur tant qu'on n'a pas relancé `docker compose up -d --build frontend`. Mes premières
captures montraient l'ancien code. Pour travailler en direct, on lance `ng serve` hors Docker.

## Fichiers à lire dans l'ordre
1. `frontend/src/app/api/costs.service.ts` : types et appels HTTP.
2. `frontend/src/app/pages/evaluation/costs/format.ts` : montants, durées, noms lisibles (fonctions pures, faciles à tester).
3. `costs-block.ts` / `.html` : l'état et le gabarit du bloc Coûts.
4. `daily-cost-chart.*` : le graphique SVG.
5. `report/evaluation-block.*` et `report-table.*` : le bloc Évaluation, dont les colonnes viennent des en-têtes du rapport.

## À essayer
1. Lancer `docker compose up --build`, ouvrir http://localhost:4200/evaluation.
2. Cliquer EN : les textes de l'interface changent, le contenu des rapports reste en français (un
   message le dit).
3. Passer le système en mode sombre : l'écran suit.
4. Arrêter le backend (`docker compose stop backend`) et recharger : l'état « erreur » apparaît ;
   redémarrer et cliquer « Réessayer ».
5. Tabuler dans la page : le focus doit toujours se voir.

## Exercices
1. Ajouter une période « 90 derniers jours » (écrire d'abord le test de `periodOf`).
2. Afficher le coût moyen par appel dans une cinquième carte.
3. Pourquoi `modelLabel` renvoie-t-il l'identifiant tel quel quand il ne le reconnaît pas ?
   (Indice : que vaut-il mieux montrer, un identifiant brut ou rien ?)
