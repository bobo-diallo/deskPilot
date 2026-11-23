/** Retire les marques Markdown (gras, code) des textes lus dans les rapports. */
export function plainText(text: string): string {
  return text
    .replace(/\*\*/g, '')
    .replace(/`/g, '')
    .replace(/(^|[\s(])_([^_]+)_(?=$|[\s).,:;])/g, '$1$2'); // _italique_ (pas invoice_number)
}
