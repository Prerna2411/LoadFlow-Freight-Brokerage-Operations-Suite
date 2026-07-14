export function money(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
}

export function shortDateTime(value: string) {
  return new Date(value).toLocaleString();
}
