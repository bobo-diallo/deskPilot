# 05 — Frontend Angular et traduction FR/EN

## Angular en bref
Angular est un framework TypeScript complet pour interfaces web. Un écran est construit à
partir de **composants** : une classe TypeScript (comportement), un gabarit HTML (affichage)
et un fichier de style. Alternatives : React, Vue (plus légers, moins cadrés).
On a pris Angular parce qu'il est très demandé en entreprise et que c'est la cible de ta
future refonte d'InserJeune.

## Les fichiers de `frontend/src/app/`
| Fichier | Rôle |
|---|---|
| `app.ts` | Le composant racine : classe `App`, avec `setLanguage` et `isActive` |
| `app.html` | Le gabarit : en-tête, boutons FR/EN, trois zones |
| `app.scss` | Les styles |
| `app.config.ts` | La configuration globale : HTTP, Transloco |
| `transloco-loader.ts` | Charge `/i18n/fr.json` ou `/i18n/en.json` |
| `app.spec.ts` | Les tests |

## Composant « standalone »
```ts
@Component({
  selector: 'app-root',
  imports: [TranslocoPipe],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App { ... }
```
« Standalone » : le composant déclare lui-même ce dont il a besoin dans `imports`
(il n'y a plus de module séparé, comme dans l'ancien Angular).

## Le gabarit
```html
<h1>{{ 'app.title' | transloco }}</h1>

@for (lang of languages; track lang) {
  <button [attr.data-lang]="lang" (click)="setLanguage(lang)">{{ lang.toUpperCase() }}</button>
}
```
- `{{ ... }}` affiche une valeur.
- `| transloco` est un **pipe** : il transforme une clé (`app.title`) en texte traduit.
- `@for` est une boucle ; `(click)` écoute un clic ; `[attr.data-lang]` fixe un attribut.

## La traduction (i18n)
Les textes ne sont jamais écrits dans le HTML mais dans `frontend/public/i18n/fr.json` et
`en.json`, sous la même clé :

```json
{ "app": { "title": "Bureau IA" } }      // fr.json
{ "app": { "title": "AI Desk" } }        // en.json
```
**Choix : Transloco** plutôt que le mécanisme intégré `@angular/localize`. Ce dernier produit
une version compilée par langue, sans bascule en direct. Transloco charge les fichiers à
l'exécution : le clic sur « EN » change tout de suite la langue.

Règle du projet : tout texte affiché passe par une clé de traduction, et on ajoute la clé
dans les **deux** fichiers.

## Pourquoi Angular 21 et pas la toute dernière version
Le dernier Angular CLI demande Node 24.15 ou plus, et ta machine a la 24.10. Les deux versions
fonctionnent pareil pour ce qu'on fait ; on mettra à jour avec Node.

## À essayer
```bash
cd frontend
npm install
npx ng serve        # serveur de développement sur http://localhost:4200
```
Modifie un texte dans `fr.json`, enregistre : la page se recharge toute seule.

## Exercice
Ajoute une clé `zones.empty` plus précise, par exemple « Rien à afficher ici pour l'instant »,
dans les deux langues. Vérifie à l'écran que les deux versions s'affichent.
