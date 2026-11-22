import { routes } from './app.routes';

describe('routes', () => {
  it('serves the evaluation screen at /evaluation', () => {
    expect(routes.some((route) => route.path === 'evaluation')).toBe(true);
  });

  it('redirects unknown addresses to the home page', () => {
    expect(routes.at(-1)).toEqual({ path: '**', redirectTo: '' });
  });
});
