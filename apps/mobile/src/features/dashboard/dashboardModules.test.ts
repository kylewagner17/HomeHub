import { modulesForRole } from './dashboardModules';

describe('modulesForRole', () => {
  it('shows full modules for admin', () => {
    const modules = modulesForRole('admin');
    expect(modules.map(m => m.id)).toContain('groceries');
    expect(modules.length).toBeGreaterThan(2);
  });

  it('shows limited modules for member', () => {
    const modules = modulesForRole('member');
    expect(modules.map(m => m.id)).toEqual(['tasks', 'calendar']);
  });
});
