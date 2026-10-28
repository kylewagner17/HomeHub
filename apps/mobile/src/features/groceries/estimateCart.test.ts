import { estimateCartTotalCents } from './estimateCart';

describe('estimateCartTotalCents', () => {
  it('includes checked items and uses zero for missing prices', () => {
    const result = estimateCartTotalCents(
      [
        { name: 'Milk', quantity: '2', checked: false },
        { name: 'Bread', quantity: '1', checked: true },
        { name: 'Eggs', quantity: '1', checked: false },
      ],
      [{ itemName: 'Milk', priceCents: 100, revision: 1 }],
    );
    expect(result.totalCents).toBe(200);
    expect(result.missingNames).toEqual([]);
  });
});
