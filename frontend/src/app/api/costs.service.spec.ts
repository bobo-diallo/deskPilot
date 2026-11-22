import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { CostsService } from './costs.service';

describe('CostsService', () => {
  let service: CostsService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CostsService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('asks for the summary without a period by default', () => {
    service.getSummary().subscribe();

    const request = http.expectOne('/api/costs/summary');
    expect(request.request.method).toBe('GET');
    request.flush({ totals: {}, by_model: [], by_task: [] });
  });

  it('sends the period as from and to query parameters', () => {
    service.getSummary({ from: '2026-11-01', to: '2026-11-30' }).subscribe();

    const request = http.expectOne('/api/costs/summary?from=2026-11-01&to=2026-11-30');
    request.flush({ totals: {}, by_model: [], by_task: [] });
  });

  it('returns the daily costs sent by the API', () => {
    let result: unknown;
    service.getDaily({ from: '2026-11-01' }).subscribe((days) => (result = days));

    http
      .expectOne('/api/costs/daily?from=2026-11-01')
      .flush([{ day: '2026-11-01', calls: 3, cost_usd: 0.02 }]);

    expect(result).toEqual([{ day: '2026-11-01', calls: 3, cost_usd: 0.02 }]);
  });
});
