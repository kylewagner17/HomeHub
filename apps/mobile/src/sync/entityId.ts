/** Server sync requires RFC 4122 UUIDs for entity_id and FK fields in push payloads. */

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

type CryptoLike = {
  randomUUID?: () => string;
  getRandomValues?: (array: Uint8Array) => Uint8Array;
};

function randomUuidFromBytes(bytes: Uint8Array): string {
  bytes[6] = (bytes[6] % 16) + 64;
  bytes[8] = (bytes[8] % 64) + 128;
  const hex = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function randomUuidV4Fallback(): string {
  const bytes = new Uint8Array(16);
  for (let i = 0; i < bytes.length; i += 1) {
    bytes[i] = Math.floor(Math.random() * 256);
  }
  return randomUuidFromBytes(bytes);
}

export function newEntityId(): string {
  const crypto = (globalThis as { crypto?: CryptoLike }).crypto;
  if (crypto?.randomUUID) {
    return crypto.randomUUID();
  }
  if (crypto?.getRandomValues) {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return randomUuidFromBytes(bytes);
  }
  return randomUuidV4Fallback();
}

export function isEntityIdUuid(id: string): boolean {
  return UUID_RE.test(id);
}
