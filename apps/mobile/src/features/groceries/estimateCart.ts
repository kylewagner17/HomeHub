/** Cart estimate from manual store prices (ADR-004). */

export function buildUnitPriceMap(
  prices: { itemName: string; priceCents: number; revision: number }[],
): Record<string, number> {
  const map: Record<string, number> = {};
  for (const price of [...prices].sort(
    (a, b) => a.itemName.localeCompare(b.itemName) || a.revision - b.revision,
  )) {
    map[price.itemName.trim().toLowerCase()] = price.priceCents;
  }
  return map;
}

/** Missing prices are treated as $0.00 for display and totals. */
export function unitPriceCentsForItem(
  itemName: string,
  priceMap: Record<string, number>,
): number {
  const value = priceMap[itemName.trim().toLowerCase()];
  return value === undefined ? 0 : value;
}

export function formatMoney(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

export type EstimateLine = { name: string; quantity: string; checked: boolean };

function parseQuantity(raw: string): number {
  const value = Number.parseFloat(raw.trim());
  if (!Number.isFinite(value) || value <= 0) {
    return 1;
  }
  return value;
}

/** Includes checked and unchecked lines; unchecked-off does not change the total. */
export function estimateCartTotalCents(
  items: EstimateLine[],
  prices: { itemName: string; priceCents: number; revision: number }[],
): { totalCents: number; missingNames: string[] } {
  const priceMap = buildUnitPriceMap(prices);
  let totalCents = 0;
  for (const item of items) {
    const unit = unitPriceCentsForItem(item.name, priceMap);
    totalCents += Math.round(unit * parseQuantity(item.quantity));
  }
  return { totalCents, missingNames: [] };
}
