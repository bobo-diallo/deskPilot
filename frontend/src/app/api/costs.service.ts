import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

// Les noms des champs (cost_usd, by_model…) sont ceux de l'API : on ne les renomme pas,
// pour que le JSON reçu corresponde exactement à ces types.
export interface Totals {
  calls: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
}

export interface Breakdown extends Totals {
  key: string | null; // null : appels d'avant l'enregistrement de la tâche
  latency_p50_ms: number;
  latency_p95_ms: number;
}

export interface CostSummary {
  totals: Totals;
  by_model: Breakdown[];
  by_task: Breakdown[];
}

export interface DailyCost {
  day: string; // AAAA-MM-JJ
  calls: number;
  cost_usd: number;
}

/** Période en jours inclus (AAAA-MM-JJ) ; une borne absente laisse la période ouverte. */
export interface Period {
  from?: string;
  to?: string;
}

@Injectable({ providedIn: 'root' })
export class CostsService {
  private readonly http = inject(HttpClient);

  getSummary(period: Period = {}): Observable<CostSummary> {
    return this.http.get<CostSummary>('/api/costs/summary', { params: toParams(period) });
  }

  getDaily(period: Period = {}): Observable<DailyCost[]> {
    return this.http.get<DailyCost[]>('/api/costs/daily', { params: toParams(period) });
  }
}

function toParams(period: Period): HttpParams {
  let params = new HttpParams();
  if (period.from) params = params.set('from', period.from);
  if (period.to) params = params.set('to', period.to);
  return params;
}
