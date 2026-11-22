import { Component } from '@angular/core';
import { TranslocoPipe } from '@jsverse/transloco';
import { CostsBlock } from './costs/costs-block';

@Component({
  selector: 'app-evaluation-page',
  imports: [TranslocoPipe, CostsBlock],
  template: `
    <h2>{{ 'evaluation.title' | transloco }}</h2>
    <app-costs-block />
  `,
})
export class EvaluationPage {}
