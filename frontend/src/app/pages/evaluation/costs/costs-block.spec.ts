import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { TranslocoTestingModule } from '@jsverse/transloco';
import en from '../../../../../public/i18n/en.json';
import fr from '../../../../../public/i18n/fr.json';
import { CostSummary } from '../../../api/costs.service';
import { CostsBlock } from './costs-block';

const SUMMARY: CostSummary = {
  totals: { calls: 15, input_tokens: 45008, output_tokens: 4346, cost_usd: 0.0067 },
  by_model: [
    {
      key: 'claude-haiku-5-5',
      calls: 15,
      input_tokens: 45008,
      output_tokens: 4346,
      cost_usd: 0.0067,
      latency_p50_ms: 2600,
      latency_p95_ms: 3500,
    },
  ],
  by_task: [
    {
      key: null,
      calls: 10,
      input_tokens: 1,
      output_tokens: 1,
      cost_usd: 0.004,
      latency_p50_ms: 100,
      latency_p95_ms: 200,
    },
    {
      key: 'extraction',
      calls: 5,
      input_tokens: 1,
      output_tokens: 1,
      cost_usd: 0.002,
      latency_p50_ms: 100,
      latency_p95_ms: 200,
    },
  ],
};
const EMPTY: CostSummary = {
  totals: { calls: 0, input_tokens: 0, output_tokens: 0, cost_usd: 0 },
  by_model: [],
  by_task: [],
};

describe('CostsBlock', () => {
  let http: HttpTestingController;
  let root: HTMLElement;
  let fixture: ReturnType<typeof TestBed.createComponent<CostsBlock>>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        CostsBlock,
        TranslocoTestingModule.forRoot({
          langs: { fr, en },
          translocoConfig: { availableLangs: ['fr', 'en'], defaultLang: 'fr' },
          preloadLangs: true,
        }),
      ],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(CostsBlock);
    root = fixture.nativeElement as HTMLElement;
    fixture.detectChanges();
  });

  async function settle() {
    await fixture.whenStable();
    fixture.detectChanges();
  }

  function answer(summary: CostSummary, daily: unknown[] = []) {
    http.expectOne((r) => r.url === '/api/costs/summary').flush(summary);
    http.expectOne((r) => r.url === '/api/costs/daily').flush(daily);
  }

  it('shows a loading message while the data is on its way', () => {
    expect(root.querySelector('[role="status"]')?.textContent).toContain('Chargement');
    http.match(() => true);
  });

  it('asks for the last 30 days by default', () => {
    const request = http.expectOne((r) => r.url === '/api/costs/summary');

    expect(request.request.params.has('from')).toBe(true);
    expect(request.request.params.has('to')).toBe(true);
    http.match(() => true);
  });

  it('shows the totals and the percentiles', async () => {
    answer(SUMMARY, [{ day: '2026-11-20', calls: 15, cost_usd: 0.0067 }]);
    await settle();

    expect(root.textContent).toContain('15');
    expect(root.textContent).toContain('0,0067');
    expect(root.textContent).toContain('2,6 s');
  });

  it('shows readable names for the models and the tasks, never technical ids', async () => {
    answer(SUMMARY);
    await settle();

    expect(root.textContent).toContain('Claude Haiku 5.5');
    expect(root.textContent).toContain('Extraction');
    expect(root.textContent).toContain('Non renseignée');
    expect(root.textContent).not.toContain('claude-haiku-5-5');
    expect(root.textContent).not.toContain('null');
  });

  it('shows an empty message when nothing was called in the period', async () => {
    answer(EMPTY);
    await settle();

    expect(root.querySelector('.empty')?.textContent).toContain('Aucun appel');
  });

  it('shows an error with a retry button, and retries on click', async () => {
    http
      .expectOne((r) => r.url === '/api/costs/summary')
      .flush('x', { status: 500, statusText: 'Boom' });
    // forkJoin annule la seconde requête dès qu'une première échoue
    http.match((r) => r.url === '/api/costs/daily');
    await settle();

    expect(root.querySelector('[role="alert"]')?.textContent).toContain('Impossible');
    root.querySelector<HTMLButtonElement>('[role="alert"] button')?.click();
    await settle();

    answer(SUMMARY);
  });

  it('reloads with the chosen period', async () => {
    answer(SUMMARY);
    await settle();

    root.querySelector<HTMLButtonElement>('button[data-period="all"]')?.click();
    await settle();

    const request = http.expectOne((r) => r.url === '/api/costs/summary');
    expect(request.request.params.has('from')).toBe(false);
    http.match(() => true);
  });
});
