import { Component, computed, inject, input } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { MatTableModule } from '@angular/material/table';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';
import { Breakdown } from '../../../api/costs.service';
import { formatInt, formatMs, formatUsd } from './format';

export interface BreakdownRow extends Breakdown {
  label: string; // nom lisible (jamais l'identifiant technique)
}

/** Tableau des coûts et des latences ventilés (par modèle ou par tâche). */
@Component({
  selector: 'app-breakdown-table',
  imports: [MatTableModule, TranslocoPipe],
  templateUrl: './breakdown-table.html',
  styleUrl: './breakdown-table.scss',
})
export class BreakdownTable {
  readonly rows = input.required<BreakdownRow[]>();
  readonly caption = input.required<string>();
  readonly firstColumn = input.required<string>();

  private readonly transloco = inject(TranslocoService);
  readonly lang = toSignal(this.transloco.langChanges$, {
    initialValue: this.transloco.getActiveLang(),
  });

  readonly columns = ['label', 'calls', 'tokens', 'cost', 'p50', 'p95'];

  readonly cells = computed(() => {
    const lang = this.lang();
    return this.rows().map((row) => ({
      label: row.label,
      calls: formatInt(row.calls, lang),
      tokens: `${formatInt(row.input_tokens, lang)} / ${formatInt(row.output_tokens, lang)}`,
      cost: formatUsd(row.cost_usd, lang),
      p50: formatMs(row.latency_p50_ms, lang),
      p95: formatMs(row.latency_p95_ms, lang),
    }));
  });
}
