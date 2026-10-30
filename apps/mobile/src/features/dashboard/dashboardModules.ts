/** Role-based dashboard placeholders; groceries and reminders wired in M2/M4. */
import type { FamilyRole } from '@homehub/shared';

export type DashboardModule = {
  id: string;
  title: string;
};

const ADMIN_MODULES: DashboardModule[] = [
  { id: 'calendar', title: 'Family calendar' },
  { id: 'groceries', title: 'Grocery lists' },
  { id: 'maintenance', title: 'Maintenance' },
  { id: 'planning', title: 'Planning' },
  { id: 'reminders', title: 'Reminders' },
];

const MEMBER_MODULES: DashboardModule[] = [
  { id: 'tasks', title: 'Your tasks' },
  { id: 'calendar', title: 'Your calendar' },
  { id: 'reminders', title: 'Reminders' },
];

export function modulesForRole(role: FamilyRole): DashboardModule[] {
  return role === 'admin' ? ADMIN_MODULES : MEMBER_MODULES;
}
