import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface ReportSummary {
  id: string;
  title: string;
  date: string | null;
}

export interface ReportTable {
  headers: string[];
  rows: string[][];
}

export interface ReportSection {
  title: string;
  paragraphs: string[];
  tables: ReportTable[];
}

export interface Report extends ReportSummary {
  intro: string;
  sections: ReportSection[];
}

@Injectable({ providedIn: 'root' })
export class EvaluationsService {
  private readonly http = inject(HttpClient);

  listReports(): Observable<ReportSummary[]> {
    return this.http.get<ReportSummary[]>('/api/evaluations/reports');
  }

  getReport(id: string): Observable<Report> {
    return this.http.get<Report>(`/api/evaluations/reports/${encodeURIComponent(id)}`);
  }
}
