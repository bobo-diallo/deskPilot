import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { TranslocoPipe, TranslocoService } from '@jsverse/transloco';

@Component({
  selector: 'app-root',
  imports: [TranslocoPipe, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly transloco = inject(TranslocoService);

  readonly languages = ['fr', 'en'] as const;

  setLanguage(lang: string): void {
    this.transloco.setActiveLang(lang);
  }

  isActive(lang: string): boolean {
    return this.transloco.getActiveLang() === lang;
  }
}
