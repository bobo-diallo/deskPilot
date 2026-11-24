import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { TranslocoTestingModule } from '@jsverse/transloco';
import en from '../../../../public/i18n/en.json';
import fr from '../../../../public/i18n/fr.json';
import { EvaluationPage } from './evaluation-page';

describe('EvaluationPage', () => {
  it('shows its title', async () => {
    await TestBed.configureTestingModule({
      imports: [
        EvaluationPage,
        TranslocoTestingModule.forRoot({
          langs: { fr, en },
          translocoConfig: { availableLangs: ['fr', 'en'], defaultLang: 'fr' },
          preloadLangs: true,
        }),
      ],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    const fixture = TestBed.createComponent(EvaluationPage);
    await fixture.whenStable();

    expect((fixture.nativeElement as HTMLElement).querySelector('h2')?.textContent).toContain(
      'Évaluation et coûts',
    );
  });
});
