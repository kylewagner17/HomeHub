# ADR-004: Grocery realtime (M3)

## Status

Accepted

## Decision

- **Near realtime** on LAN uses **pull-based sync every 5 seconds** while the grocery list detail screen is focused and the device is online (`NetInfo`). No WebSocket/Redis in M3.
- Partners see changes after the next poll or manual sync; acceptable for household scale per architecture deferral of pub/sub.

## Pricing

- **Manual prices** per store: family enters item names and unit prices; stored in `grocery_store_prices` and synced like other grocery entities.
- Cart **estimate** sums unchecked line items for the selected store (name match, case-insensitive).

## Sync entities (M3)

`grocery_list`, `grocery_list_item`, `grocery_staple`, `grocery_store`, `grocery_store_price` — same revision/idempotency rules as ADR-003.
