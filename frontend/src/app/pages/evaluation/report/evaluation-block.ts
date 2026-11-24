import { Component, computed, inject, signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { TranslocoDirective, TranslocoService } from '@jsverse/transloco';
import { BehaviorSubject, catchError, combineLatest, map, of, startWith, switchMap } from 'rxjs';
import { EvaluationsService, Report, ReportSummary } from '../../../api/evaluations.service';
import { plainText } from './plain-text';
import { ReportTable } from './report-table';

type ListState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'empty' }
  | { status: 'ready'; reports: ReportSummary[] };

type ReportState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'ready'; report: Report };

@Component({
  selector: 'app-evaluation-block',
  imports: [
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressBarModule,
    TranslocoDirective,
    ReportTable,
  ],
  templateUrl: './evaluation-block.html',
  styleUrl: './evaluation-block.scss',
})
export class EvaluationBlock {
  private readonly evaluations = inject(EvaluationsService);
  private readonly transloco = inject(TranslocoService);

  readonly plainText = plainText;

  private readonly lang = toSignal(this.transloco.langChanges$, {
    initialValue: this.transloco.getActiveLang(),
  });

  private readonly reloadList$ = new BehaviorSubject<void>(undefined);
  private readonly reloadReport$ = new BehaviorSubject<void>(undefined);

  readonly list = toSignal(
    this.reloadList$.pipe(
      switchMap(() =>
        this.evaluations.listReports().pipe(
          map((reports): ListState =>
            reports.length ? { status: 'ready', reports } : { status: 'empty' },
          ),
          catchError(() => of<ListState>({ status: 'error' })),
          startWith<ListState>({ status: 'loading' }),
        ),
      ),
    ),
    { initialValue: { status: 'loading' } as ListState },
  );

  /** Le rapport choisi par l'utilisateur ; sans choix, le plus récent (premier de la liste). */
  private readonly chosenId = signal<string | null>(null);
  readonly selectedId = computed(() => {
    const list = this.list();
    return this.chosenId() ?? (list.status === 'ready' ? list.reports[0].id : null);
  });

  /** `switchMap` abandonne la requête précédente : un rapport lent n'écrase pas le suivant. */
  readonly report = toSignal(
    combineLatest([toObservable(this.selectedId), this.reloadReport$]).pipe(
      switchMap(([id]) =>
        id === null
          ? of<ReportState>({ status: 'idle' })
          : this.evaluations.getReport(id).pipe(
              map((report): ReportState => ({ status: 'ready', report })),
              catchError(() => of<ReportState>({ status: 'error' })),
              startWith<ReportState>({ status: 'loading' }),
            ),
      ),
    ),
    { initialValue: { status: 'idle' } as ReportState },
  );

  readonly options = computed(() => {
    const list = this.list();
    const lang = this.lang();
    return list.status === 'ready'
      ? list.reports.map((summary) => ({
          id: summary.id,
          label: this.labelOf(summary, lang),
        }))
      : [];
  });

  readonly contentIsTranslated = computed(() => this.lang() === 'fr');

  choose(id: string): void {
    this.chosenId.set(id);
  }

  retryList(): void {
    this.reloadList$.next();
  }

  retryReport(): void {
    this.reloadReport$.next();
  }

  /** Nom lisible du rapport (traduit) suivi de sa date ; à défaut, le titre du fichier. */
  private labelOf(summary: ReportSummary, lang: string): string {
    const slug = summary.id.replace(/^\d{4}-\d{2}-\d{2}-/, '');
    const key = `evaluation.reportNames.${slug}`;
    const name = this.transloco.translate(key);
    const label = name === key ? plainText(summary.title) : name;
    if (!summary.date) {
      return label;
    }
    const date = new Intl.DateTimeFormat(lang, { dateStyle: 'long', timeZone: 'UTC' }).format(
      new Date(`${summary.date}T00:00:00Z`),
    );
    return `${label} — ${date}`;
  }
}
