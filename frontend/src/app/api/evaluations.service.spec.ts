import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { EvaluationsService } from './evaluations.service';

describe('EvaluationsService', () => {
  let service: EvaluationsService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(EvaluationsService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lists the reports', () => {
    let result: unknown;
    service.listReports().subscribe((reports) => (result = reports));

    http.expectOne('/api/evaluations/reports').flush([{ id: 'a', title: 'A', date: '2026-11-17' }]);

    expect(result).toEqual([{ id: 'a', title: 'A', date: '2026-11-17' }]);
  });

  it('reads one report by its id', () => {
    service.getReport('2026-11-18-search').subscribe();

    http.expectOne('/api/evaluations/reports/2026-11-18-search').flush({});
  });

  it('encodes the id so it cannot change the path', () => {
    service.getReport('../secret').subscribe();

    http.expectOne('/api/evaluations/reports/..%2Fsecret').flush({});
  });
});
