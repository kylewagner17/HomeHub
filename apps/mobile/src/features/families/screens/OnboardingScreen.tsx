import React, { useState } from 'react';
import { Button, StyleSheet, Text, TextInput, View } from 'react-native';

import { useAuth } from '../../auth/AuthContext';
import * as api from '../../../sync/apiClient';

export function OnboardingScreen() {
  const { refreshUser } = useAuth();
  const [familyName, setFamilyName] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState<string | null>(null);

  const create = async () => {
    setError(null);
    try {
      await api.createFamily(familyName.trim());
      await refreshUser();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not create family');
    }
  };

  const join = async () => {
    setError(null);
    try {
      await api.joinFamily(inviteCode.trim());
      await refreshUser();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not join family');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Join your family</Text>
      <Text style={styles.section}>Create a new family</Text>
      <TextInput
        style={styles.input}
        placeholder="Family name"
        value={familyName}
        onChangeText={setFamilyName}
      />
      <Button title="Create family" onPress={create} />
      <Text style={styles.section}>Or join with invite code</Text>
      <TextInput
        style={styles.input}
        autoCapitalize="characters"
        placeholder="Invite code"
        value={inviteCode}
        onChangeText={setInviteCode}
      />
      <Button title="Join family" onPress={join} />
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, justifyContent: 'center', gap: 12 },
  title: { fontSize: 24, fontWeight: '600' },
  section: { marginTop: 16, fontWeight: '500' },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12 },
  error: { color: '#b00020' },
});
