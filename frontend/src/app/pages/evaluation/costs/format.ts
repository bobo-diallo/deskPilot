import { Period } from '../../../api/costs.service';

export type PeriodPreset = 'all' | '7' | '30';

/** Montant en dollars : au moins 2 décimales, jusqu'à 4 pour ne pas écraser un coût minuscule. */
export function formatUsd(value: number, lang: string): string {
  return new Intl.NumberFormat(lang, {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(value);
}

export function formatInt(value: number, lang: string): string {
  return new Intl.NumberFormat(lang).format(value);
}

/** Latence : en millisecondes sous une seconde, en secondes (1 décimale) au-delà. */
export function formatMs(ms: number, lang: string): string {
  if (ms < 1000) {
    return `${formatInt(ms, lang)} ms`;
  }
  const seconds = new Intl.NumberFormat(lang, {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(ms / 1000);
  return `${seconds} s`;
}

/** « claude-haiku-5-5 » devient « Claude Haiku 5.5 » ; un identifiant inconnu reste tel quel. */
export function modelLabel(id: string): string {
  const match = /^claude-([a-z]+)-(\d+)-(\d+)$/.exec(id);
  if (!match) {
    return id;
  }
  const [, family, major, minor] = match;
  return `Claude ${family[0].toUpperCase()}${family.slice(1)} ${major}.${minor}`;
}

/** Période en jours UTC, aujourd'hui inclus (« 7 » = les 7 derniers jours). */
export function periodOf(preset: PeriodPreset, today: Date): Period {
  if (preset === 'all') {
    return {};
  }
  const to = new Date(today);
  const from = new Date(today);
  from.setUTCDate(from.getUTCDate() - (Number(preset) - 1));
  return { from: isoDay(from), to: isoDay(to) };
}

function isoDay(date: Date): string {
  return date.toISOString().slice(0, 10);
}
