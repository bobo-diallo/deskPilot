import { plainText } from './plain-text';

describe('plainText', () => {
  it('removes bold markers', () => {
    expect(plainText('**Rapport conservé** pour mémoire')).toBe('Rapport conservé pour mémoire');
  });

  it('removes code backticks', () => {
    expect(plainText('lu comme `05/07/2026`')).toBe('lu comme 05/07/2026');
  });

  it('leaves ordinary text alone', () => {
    expect(plainText('87,5 % (IC 95 % : 75,3 % à 94,1 %)')).toBe(
      '87,5 % (IC 95 % : 75,3 % à 94,1 %)',
    );
  });
});
