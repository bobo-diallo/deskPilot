import { TestBed } from '@angular/core/testing';
import { TranslocoTestingModule } from '@jsverse/transloco';
import { App } from './app';
import en from '../../public/i18n/en.json';
import fr from '../../public/i18n/fr.json';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        App,
        TranslocoTestingModule.forRoot({
          langs: { fr, en },
          translocoConfig: { availableLangs: ['fr', 'en'], defaultLang: 'fr', reRenderOnLangChange: true },
          preloadLangs: true,
        }),
      ],
    }).compileComponents();
  });

  it('shows the title in French by default', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const root = fixture.nativeElement as HTMLElement;

    expect(root.querySelector('h1')?.textContent).toContain('Bureau IA');
  });

  it('shows three empty named zones', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const zones = (fixture.nativeElement as HTMLElement).querySelectorAll('section h2');

    expect(Array.from(zones).map((zone) => zone.textContent?.trim())).toEqual([
      'Conversation',
      'Modules',
      'Galerie',
    ]);
  });

  it('switches the title to English', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const root = fixture.nativeElement as HTMLElement;

    root.querySelector<HTMLButtonElement>('button[data-lang="en"]')?.click();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(root.querySelector('h1')?.textContent).toContain('AI Desk');
  });
});
