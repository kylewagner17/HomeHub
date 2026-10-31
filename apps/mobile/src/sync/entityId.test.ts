import { isEntityIdUuid, newEntityId } from './entityId';

describe('entityId', () => {
  it('generates UUID v4 strings', () => {
    const id = newEntityId();
    expect(isEntityIdUuid(id)).toBe(true);
  });

  it('rejects legacy list- prefixed ids', () => {
    expect(isEntityIdUuid('list-123-abc')).toBe(false);
  });

  it('falls back when randomUUID is missing (React Native Android)', () => {
    const g = globalThis as { crypto?: CryptoLike };
    const original = g.crypto;
    g.crypto = {};
    try {
      const id = newEntityId();
      expect(isEntityIdUuid(id)).toBe(true);
    } finally {
      g.crypto = original;
    }
  });
});

type CryptoLike = {
  randomUUID?: () => string;
  getRandomValues?: (array: Uint8Array) => Uint8Array;
};
