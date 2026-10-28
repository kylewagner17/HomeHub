import React from 'react';
import { Button, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';

import type { FamilyMembershipSummary } from '@homehub/shared';

import { useAuth } from '../auth/AuthContext';
import { modulesForRole } from './dashboardModules';

type Props = {
  membership: FamilyMembershipSummary;
  onOpenGroceries: () => void;
};

export function DashboardScreen({ membership, onOpenGroceries }: Props) {
  const { user, signOut } = useAuth();
  const modules = modulesForRole(membership.role);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{membership.family_name}</Text>
      <Text style={styles.subtitle}>
        {user?.display_name} · {membership.role === 'admin' ? 'Parent (admin)' : 'Member'}
      </Text>
      <Text style={styles.hint}>Invite code: {membership.invite_code}</Text>
      <FlatList
        data={modules}
        keyExtractor={item => item.id}
        renderItem={({ item }) => {
          const isGroceries = item.id === 'groceries';
          return (
            <Pressable
              style={styles.card}
              disabled={!isGroceries}
              onPress={isGroceries ? onOpenGroceries : undefined}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <Text style={styles.cardMeta}>
                {isGroceries ? 'Tap to open (offline sync)' : 'Coming in a later milestone'}
              </Text>
            </Pressable>
          );
        }}
      />
      <Button title="Sign out" onPress={signOut} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, paddingTop: 48 },
  title: { fontSize: 26, fontWeight: '600' },
  subtitle: { fontSize: 16, color: '#444', marginBottom: 8 },
  hint: { fontSize: 14, color: '#666', marginBottom: 16 },
  card: {
    padding: 16,
    borderRadius: 8,
    backgroundColor: '#f4f4f4',
    marginBottom: 8,
  },
  cardTitle: { fontSize: 16, fontWeight: '500' },
  cardMeta: { fontSize: 12, color: '#777', marginTop: 4 },
});
