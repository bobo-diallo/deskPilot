/** Retire les marques Markdown (gras, code) des textes lus dans les rapports. */
export function plainText(text: string): string {
  return text.replace(/\*\*/g, '').replace(/`/g, '');
}
