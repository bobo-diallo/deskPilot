import { Component, computed, inject, input } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { TranslocoService } from '@jsverse/transloco';
import { DailyCost } from '../../../api/costs.service';
import { formatUsd } from './format';

const WIDTH = 600;
const PLOT_HEIGHT = 160; // hauteur de la zone des barres
const LABEL_HEIGHT = 24; // place sous les barres pour les dates
const GAP = 4;

/** Histogramme SVG du coût par jour (sans bibliothèque de graphiques). */
@Component({
  selector: 'app-daily-cost-chart',
  templateUrl: './daily-cost-chart.html',
  styleUrl: './daily-cost-chart.scss',
})
export class DailyCostChart {
  readonly days = input.required<DailyCost[]>();

  private readonly transloco = inject(TranslocoService);
  // Relit la langue active : le texte et les montants se mettent à jour quand elle change.
  private readonly lang = toSignal(this.transloco.langChanges$, {
    initialValue: this.transloco.getActiveLang(),
  });

  readonly width = WIDTH;
  readonly height = PLOT_HEIGHT + LABEL_HEIGHT;
  readonly baseline = PLOT_HEIGHT;

  readonly bars = computed(() => {
    const days = this.days();
    const lang = this.lang();
    const max = Math.max(...days.map((d) => d.cost_usd), 0);
    const slot = days.length ? WIDTH / days.length : WIDTH;
    return days.map((d, i) => {
      const height = max > 0 ? (d.cost_usd / max) * PLOT_HEIGHT : 0;
      return {
        x: i * slot + GAP / 2,
        width: Math.max(slot - GAP, 1),
        height,
        y: PLOT_HEIGHT - height,
        title: this.transloco.translate('costs.barTitle', {
          day: d.day,
          cost: formatUsd(d.cost_usd, lang),
          calls: d.calls,
        }),
      };
    });
  });

  readonly firstDay = computed(() => this.days().at(0)?.day ?? '');
  readonly lastDay = computed(() => this.days().at(-1)?.day ?? '');

  readonly label = computed(() => {
    const total = this.days().reduce((sum, d) => sum + d.cost_usd, 0);
    return this.transloco.translate('costs.chartLabel', {
      from: this.firstDay(),
      to: this.lastDay(),
      total: formatUsd(total, this.lang()),
    });
  });
}
