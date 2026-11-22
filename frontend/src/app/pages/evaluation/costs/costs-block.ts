import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { TranslocoDirective, TranslocoService } from '@jsverse/transloco';
import { BehaviorSubject, catchError, forkJoin, map, of, startWith, switchMap } from 'rxjs';
import { CostSummary, CostsService, DailyCost } from '../../../api/costs.service';
import { BreakdownRow, BreakdownTable } from './breakdown-table';
import { DailyCostChart } from './daily-cost-chart';
import { formatInt, formatUsd, modelLabel, PeriodPreset, periodOf } from './format';

type CostsState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'empty' }
  | { status: 'ready'; summary: CostSummary; daily: DailyCost[] };

@Component({
  selector: 'app-costs-block',
  imports: [
    MatButtonModule,
    MatCardModule,
    MatProgressBarModule,
    TranslocoDirective,
    BreakdownTable,
    DailyCostChart,
  ],
  templateUrl: './costs-block.html',
  styleUrl: './costs-block.scss',
})
export class CostsBlock {
  private readonly costs = inject(CostsService);
  private readonly transloco = inject(TranslocoService);

  readonly presets: PeriodPreset[] = ['30', '7', 'all'];
  private readonly preset$ = new BehaviorSubject<PeriodPreset>('30');
  readonly preset = toSignal(this.preset$, { initialValue: '30' as PeriodPreset });

  private readonly lang = toSignal(this.transloco.langChanges$, {
    initialValue: this.transloco.getActiveLang(),
  });

  /**
   * Chaque changement de période (ou « Réessayer ») relance les deux appels. `switchMap`
   * abandonne la requête précédente : une réponse lente ne remplace pas une plus récente.
   */
  readonly state = toSignal(
    this.preset$.pipe(
      switchMap((preset) => {
        const period = periodOf(preset, new Date());
        return forkJoin({
          summary: this.costs.getSummary(period),
          daily: this.costs.getDaily(period),
        }).pipe(
          map(({ summary, daily }): CostsState =>
            summary.totals.calls === 0 ? { status: 'empty' } : { status: 'ready', summary, daily },
          ),
          catchError(() => of<CostsState>({ status: 'error' })),
          startWith<CostsState>({ status: 'loading' }),
        );
      }),
    ),
    { initialValue: { status: 'loading' } as CostsState },
  );

  readonly ready = computed(() => {
    const state = this.state();
    return state.status === 'ready' ? state : null;
  });

  readonly cards = computed(() => {
    const ready = this.ready();
    const lang = this.lang();
    if (!ready) {
      return [];
    }
    const { totals } = ready.summary;
    return [
      { key: 'cost', value: formatUsd(totals.cost_usd, lang) },
      { key: 'calls', value: formatInt(totals.calls, lang) },
      { key: 'inputTokens', value: formatInt(totals.input_tokens, lang) },
      { key: 'outputTokens', value: formatInt(totals.output_tokens, lang) },
    ];
  });

  readonly modelRows = computed<BreakdownRow[]>(() =>
    (this.ready()?.summary.by_model ?? []).map((row) => ({
      ...row,
      label: modelLabel(row.key ?? ''),
    })),
  );

  readonly taskRows = computed<BreakdownRow[]>(() => {
    this.lang(); // les libellés dépendent de la langue active
    return (this.ready()?.summary.by_task ?? []).map((row) => ({
      ...row,
      label: this.transloco.translate(`costs.tasks.${row.key ?? 'unknown'}`),
    }));
  });

  select(preset: PeriodPreset): void {
    this.preset$.next(preset);
  }

  retry(): void {
    this.preset$.next(this.preset$.value);
  }
}
