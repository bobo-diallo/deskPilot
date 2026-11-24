import { Component } from '@angular/core';
import { TranslocoPipe } from '@jsverse/transloco';
import { CostsBlock } from './costs/costs-block';
import { EvaluationBlock } from './report/evaluation-block';

@Component({
  selector: 'app-evaluation-page',
  imports: [TranslocoPipe, CostsBlock, EvaluationBlock],
  template: `
    <h2>{{ 'evaluation.title' | transloco }}</h2>
    <app-costs-block />
    <app-evaluation-block />
  `,
})
export class EvaluationPage {}
