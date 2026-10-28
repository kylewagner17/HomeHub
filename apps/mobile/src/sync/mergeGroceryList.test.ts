import { mergeServerList } from './mergeGroceryList';

describe('mergeServerList', () => {
  it('applies server when revision is newer', () => {
    const server = {
      id: '1',
      family_id: 'f',
      name: 'Server name',
      selected_store_id: null,
      revision: 3,
      updated_at: '2026-01-02T00:00:00Z',
      deleted_at: null,
    };
    const local = {
      id: '1',
      familyId: 'f',
      name: 'Local',
      selectedStoreId: null,
      revision: 2,
      updatedAt: '2026-01-01T00:00:00Z',
      deleted: false,
    };
    expect(mergeServerList(local, server).name).toBe('Server name');
  });

  it('keeps local when revision is newer', () => {
    const server = {
      id: '1',
      family_id: 'f',
      name: 'Server',
      selected_store_id: null,
      revision: 1,
      updated_at: '2026-01-01T00:00:00Z',
      deleted_at: null,
    };
    const local = {
      id: '1',
      familyId: 'f',
      name: 'Local newer',
      selectedStoreId: null,
      revision: 5,
      updatedAt: '2026-01-02T00:00:00Z',
      deleted: false,
    };
    expect(mergeServerList(local, server).name).toBe('Local newer');
  });
});
