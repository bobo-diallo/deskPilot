import { formatInt, formatMs, formatUsd, modelLabel, periodOf } from './format';

describe('formatUsd', () => {
  it('keeps enough decimals to show a tiny cost', () => {
    expect(formatUsd(0.0006, 'en')).toBe('$0.0006');
  });

  it('uses the decimal comma and the dollar sign after the number in French', () => {
    expect(formatUsd(1.5, 'fr').replace(/\s/g, ' ')).toBe('1,50 $US');
  });
});

describe('formatInt', () => {
  it('groups thousands according to the language', () => {
    expect(formatInt(45008, 'en')).toBe('45,008');
  });
});

describe('formatMs', () => {
  it('shows milliseconds under one second', () => {
    expect(formatMs(850, 'en')).toBe('850 ms');
  });

  it('shows seconds from one second', () => {
    expect(formatMs(2700, 'en')).toBe('2.7 s');
  });
});

describe('modelLabel', () => {
  it('turns a technical model id into a readable name', () => {
    expect(modelLabel('claude-haiku-5-5')).toBe('Claude Haiku 5.5');
  });

  it('keeps an unknown id as it is', () => {
    expect(modelLabel('whisper-small')).toBe('whisper-small');
  });
});

describe('periodOf', () => {
  const today = new Date('2026-11-22T10:00:00Z');

  it('has no bounds for all', () => {
    expect(periodOf('all', today)).toEqual({});
  });

  it('covers the last 7 days including today', () => {
    expect(periodOf('7', today)).toEqual({ from: '2026-11-16', to: '2026-11-22' });
  });

  it('covers the last 30 days including today', () => {
    expect(periodOf('30', today)).toEqual({ from: '2026-10-24', to: '2026-11-22' });
  });
});
