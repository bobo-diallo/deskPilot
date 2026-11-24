import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { TranslocoTestingModule } from '@jsverse/transloco';
import en from '../../../../../public/i18n/en.json';
import fr from '../../../../../public/i18n/fr.json';
import { Report, ReportSummary } from '../../../api/evaluations.service';
import { EvaluationBlock } from './evaluation-block';

const LIST: ReportSummary[] = [
  { id: '2026-11-19-agent', title: 'Rapport agent', date: '2026-11-19' },
  { id: '2026-11-17-baseline-v1', title: 'Rapport 17', date: '2026-11-17' },
];

function report(id: string, overrides: Partial<Report> = {}): Report {
  return {
    id,
    title: 'Rapport',
    date: '2026-11-19',
    intro: 'Jeu de 24 factures, 2 répétition(s).',
    note: '',
    sections: [
      {
        title: 'Résumé',
        paragraphs: ['Un commentaire.'],
        tables: [{ headers: ['Variante', 'Réussite'], rows: [['haiku', '87,5 %']] }],
      },
    ],
    ...overrides,
  };
}

describe('EvaluationBlock', () => {
  let http: HttpTestingController;
  let root: HTMLElement;
  let fixture: ReturnType<typeof TestBed.createComponent<EvaluationBlock>>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        EvaluationBlock,
        TranslocoTestingModule.forRoot({
          langs: { fr, en },
          translocoConfig: { availableLangs: ['fr', 'en'], defaultLang: 'fr' },
          preloadLangs: true,
        }),
      ],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(EvaluationBlock);
    root = fixture.nativeElement as HTMLElement;
    fixture.detectChanges();
  });

  async function settle() {
    await fixture.whenStable();
    fixture.detectChanges();
  }

  async function loadFirstReport(r: Report = report('2026-11-19-agent')) {
    http.expectOne('/api/evaluations/reports').flush(LIST);
    await settle();
    http.expectOne('/api/evaluations/reports/2026-11-19-agent').flush(r);
    await settle();
  }

  it('shows a loading message while the list is on its way', () => {
    expect(root.querySelector('[role="status"]')?.textContent).toContain('Chargement');
    http.match(() => true);
  });

  it('opens the most recent report by default', async () => {
    await loadFirstReport();

    expect(root.querySelector('select')?.value).toBe('2026-11-19-agent');
    expect(root.textContent).toContain('Jeu de 24 factures');
  });

  it('shows the tables of the report with their headers and cells', async () => {
    await loadFirstReport();

    const headers = Array.from(root.querySelectorAll('th')).map((th) => th.textContent?.trim());
    const cells = Array.from(root.querySelectorAll('td')).map((td) => td.textContent?.trim());
    expect(headers).toEqual(['Variante', 'Réussite']);
    expect(cells).toEqual(['haiku', '87,5 %']);
    expect(root.textContent).toContain('Un commentaire.');
  });

  it('names the reports in the list, not by their file name', async () => {
    await loadFirstReport();

    const options = Array.from(root.querySelectorAll('option')).map((o) => o.textContent?.trim());
    expect(options[0]).toContain('Agent avec outils');
    expect(options.join(' ')).not.toContain('2026-11-19-agent');
  });

  it('shows the warning of a report apart, without markdown marks', async () => {
    await loadFirstReport(report('2026-11-19-agent', { note: '**Jeu défectueux.** À lire.' }));

    const note = root.querySelector('[role="note"]');
    expect(note?.textContent).toContain('Jeu défectueux. À lire.');
    expect(note?.textContent).not.toContain('**');
  });

  it('loads another report when the choice changes', async () => {
    await loadFirstReport();
    const select = root.querySelector('select') as HTMLSelectElement;

    select.value = '2026-11-17-baseline-v1';
    select.dispatchEvent(new Event('change'));
    await settle();

    http
      .expectOne('/api/evaluations/reports/2026-11-17-baseline-v1')
      .flush(report('2026-11-17-baseline-v1', { intro: 'Autre intro.' }));
    await settle();
    expect(root.textContent).toContain('Autre intro.');
  });

  it('shows an error with a retry when the list fails', async () => {
    http.expectOne('/api/evaluations/reports').flush('x', { status: 500, statusText: 'Boom' });
    await settle();

    expect(root.querySelector('[role="alert"]')?.textContent).toContain('Impossible');
    root.querySelector<HTMLButtonElement>('[role="alert"] button')?.click();
    await settle();

    http.expectOne('/api/evaluations/reports').flush(LIST);
    await settle();
    http.expectOne('/api/evaluations/reports/2026-11-19-agent').flush(report('2026-11-19-agent'));
  });

  it('keeps the list and shows an error when only the report fails', async () => {
    http.expectOne('/api/evaluations/reports').flush(LIST);
    await settle();
    http
      .expectOne('/api/evaluations/reports/2026-11-19-agent')
      .flush('x', { status: 404, statusText: 'Not found' });
    await settle();

    expect(root.querySelector('select')).not.toBeNull();
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('Impossible');
  });

  it('shows an empty message when there is no report', async () => {
    http.expectOne('/api/evaluations/reports').flush([]);
    await settle();

    expect(root.querySelector('.empty')?.textContent).toContain('Aucun rapport');
  });
});
