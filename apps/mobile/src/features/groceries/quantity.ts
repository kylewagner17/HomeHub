/** Quantity helpers aligned with API groceries/quantity.py */

export function parseQuantity(raw: string): number {
  const value = Number.parseFloat(String(raw).trim());
  if (!Number.isFinite(value) || value <= 0) {
    return 1;
  }
  return value;
}

export function formatQuantity(value: number): string {
  if (Math.abs(value - Math.round(value)) < 1e-9) {
    return String(Math.round(value));
  }
  return value.toFixed(2).replace(/\.?0+$/, '');
}

export function addQuantities(left: string, right: string): string {
  return formatQuantity(parseQuantity(left) + parseQuantity(right));
}

export function adjustQuantity(raw: string, delta: number): string | null {
  const next = parseQuantity(raw) + delta;
  if (next < 1) {
    return null;
  }
  return formatQuantity(next);
}
