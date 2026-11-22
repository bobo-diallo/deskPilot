import { Routes } from '@angular/router';
import { EvaluationPage } from './pages/evaluation/evaluation-page';
import { HomePage } from './pages/home/home-page';

export const routes: Routes = [
  { path: '', component: HomePage, pathMatch: 'full' },
  { path: 'evaluation', component: EvaluationPage },
  { path: '**', redirectTo: '' },
];
