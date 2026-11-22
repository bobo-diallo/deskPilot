import { TestBed } from '@angular/core/testing';
import { TranslocoTestingModule } from '@jsverse/transloco';
import en from '../../../../../public/i18n/en.json';
import fr from '../../../../../public/i18n/fr.json';
import { DailyCostChart } from './daily-cost-chart';

async function render(days: { day: string; calls: number; cost_usd: number }[]) {
  await TestBed.configureTestingModule({
    imports: [
      DailyCostChart,
      TranslocoTestingModule.forRoot({
        langs: { fr, en },
        translocoConfig: { availableLangs: ['fr', 'en'], defaultLang: 'fr' },
        preloadLangs: true,
      }),
    ],
  }).compileComponents();
  const fixture = TestBed.createComponent(DailyCostChart);
  fixture.componentRef.setInput('days', days);
  await fixture.whenStable();
  return fixture.nativeElement as HTMLElement;
}

describe('DailyCostChart', () => {
  it('draws one bar per day', async () => {
    const root = await render([
      { day: '2026-11-01', calls: 2, cost_usd: 0.01 },
      { day: '2026-11-02', calls: 4, cost_usd: 0.02 },
    ]);

    expect(root.querySelectorAll('rect.bar').length).toBe(2);
  });

  it('makes the tallest bar the full height and scales the others', async () => {
    const root = await render([
      { day: '2026-11-01', calls: 2, cost_usd: 0.01 },
      { day: '2026-11-02', calls: 4, cost_usd: 0.02 },
    ]);
    const [small, tall] = Array.from(root.querySelectorAll('rect.bar')).map((bar) =>
      Number(bar.getAttribute('height')),
    );

    expect(small).toBeCloseTo(tall / 2);
  });

  it('gives each bar a text alternative with the day, the cost and the calls', async () => {
    const root = await render([{ day: '2026-11-01', calls: 2, cost_usd: 0.01 }]);

    expect(root.querySelector('rect.bar title')?.textContent).toContain('2026-11-01');
    expect(root.querySelector('rect.bar title')?.textContent).toContain('2');
  });

  it('describes the whole chart for screen readers', async () => {
    const root = await render([{ day: '2026-11-01', calls: 2, cost_usd: 0.01 }]);

    expect(root.querySelector('svg')?.getAttribute('role')).toBe('img');
    expect(root.querySelector('svg')?.getAttribute('aria-label')).toContain('Coût par jour');
  });

  it('draws no bar when every cost is zero', async () => {
    const root = await render([{ day: '2026-11-01', calls: 0, cost_usd: 0 }]);

    expect(root.querySelectorAll('rect.bar').length).toBe(1);
    expect(Number(root.querySelector('rect.bar')?.getAttribute('height'))).toBe(0);
  });
});
