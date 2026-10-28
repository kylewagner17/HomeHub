/* eslint-env jest */
global.fetch = jest.fn(async () => ({
  ok: false,
  status: 401,
  json: async () => ({ error: { code: 'UNAUTHORIZED', message: 'No session' } }),
  statusText: 'Unauthorized',
}));

jest.mock('@op-engineering/op-sqlite', () => ({
  open: () => ({
    executeSync: () => ({ rows: [] }),
    execute: async () => ({ rows: [] }),
  }),
}));

jest.mock('react-native-keychain', () => ({
  setGenericPassword: jest.fn(async () => true),
  getGenericPassword: jest.fn(async () => false),
  resetGenericPassword: jest.fn(async () => true),
}));
