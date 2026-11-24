import { TestBed } from '@angular/core/testing';
import { TranslocoTestingModule } from '@jsverse/transloco';
import en from '../../../../public/i18n/en.json';
import fr from '../../../../public/i18n/fr.json';
import { HomePage } from './home-page';

describe('HomePage', () => {
  it('shows three empty named zones', async () => {
    await TestBed.configureTestingModule({
      imports: [
        HomePage,
        TranslocoTestingModule.forRoot({
          langs: { fr, en },
          translocoConfig: { availableLangs: ['fr', 'en'], defaultLang: 'fr' },
          preloadLangs: true,
        }),
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(HomePage);
    await fixture.whenStable();
    const zones = (fixture.nativeElement as HTMLElement).querySelectorAll('section h2');

    expect(Array.from(zones).map((zone) => zone.textContent?.trim())).toEqual([
      'Conversation',
      'Modules',
      'Galerie',
    ]);
  });
});
