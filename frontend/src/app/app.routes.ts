import { Routes } from '@angular/router';
import { HomePage } from './pages/home/home-page';

export const routes: Routes = [
  { path: '', component: HomePage, pathMatch: 'full' },
  // Chargé à la demande : Angular Material n'alourdit pas le premier affichage
  {
    path: 'evaluation',
    loadComponent: () => import('./pages/evaluation/evaluation-page').then((m) => m.EvaluationPage),
  },
  { path: '**', redirectTo: '' },
];
