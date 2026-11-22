import { Component } from '@angular/core';
import { TranslocoPipe } from '@jsverse/transloco';

@Component({
  selector: 'app-evaluation-page',
  imports: [TranslocoPipe],
  template: `<h2>{{ 'evaluation.title' | transloco }}</h2>`,
})
export class EvaluationPage {}
