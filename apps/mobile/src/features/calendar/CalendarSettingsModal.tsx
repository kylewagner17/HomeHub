import React, { useEffect, useState } from 'react';
import { Button, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import type { CalendarEventKind, FamilyMemberDto } from '@homehub/shared';

import { fetchFamilyMembers } from '../../sync/apiClient';
import { getCalendarUiPrefs, saveCalendarUiPrefs } from '../../db/calendarPrefsStore';
import {
  CALENDAR_KINDS,
  DEFAULT_OWNER_PALETTE,
  defaultCalendarUiPrefs,
  type CalendarColorMode,
  type CalendarUiPrefs,
} from './calendarTypes';

type Props = {
  visible: boolean;
  familyId: string;
  onClose: () => void;
  onSaved: () => void;
};

const COLOR_MODE_LABELS: Record<CalendarColorMode, string> = {
  by_owner: 'Color by creator',
  by_kind: 'Color by event type',
};

export function CalendarSettingsModal({ visible, familyId, onClose, onSaved }: Props) {
  const [prefs, setPrefs] = useState<CalendarUiPrefs>(() => defaultCalendarUiPrefs());
  const [members, setMembers] = useState<FamilyMemberDto[]>([]);

  useEffect(() => {
    if (!visible) {
      return;
    }
    setPrefs(getCalendarUiPrefs(familyId));
    fetchFamilyMembers(familyId)
      .then(setMembers)
      .catch(() => setMembers([]));
  }, [visible, familyId]);

  function save() {
    saveCalendarUiPrefs(familyId, prefs);
    onSaved();
    onClose();
  }

  function setSymbol(kind: CalendarEventKind, symbol: string) {
    setPrefs(prev => ({
      ...prev,
      kindSymbols: { ...prev.kindSymbols, [kind]: symbol.slice(0, 4) },
    }));
  }

  function setKindColor(kind: CalendarEventKind, color: string) {
    setPrefs(prev => ({
      ...prev,
      kindColors: { ...prev.kindColors, [kind]: color },
    }));
  }

  function setOwnerColor(userId: string, color: string) {
    setPrefs(prev => ({
      ...prev,
      ownerColors: { ...prev.ownerColors, [userId]: color },
    }));
  }

  return (
    <Modal visible={visible} animationType="slide">
      <View style={styles.container}>
        <Text style={styles.title}>Calendar display</Text>
        <ScrollView>
          <Text style={styles.section}>Colors</Text>
          <View style={styles.row}>
            {(Object.keys(COLOR_MODE_LABELS) as CalendarColorMode[]).map(mode => (
              <Pressable
                key={mode}
                style={[styles.chip, prefs.colorMode === mode && styles.chipActive]}
                onPress={() => setPrefs(prev => ({ ...prev, colorMode: mode }))}>
                <Text style={styles.chipText}>{COLOR_MODE_LABELS[mode]}</Text>
              </Pressable>
            ))}
          </View>

          <Text style={styles.section}>Symbols by type</Text>
          {CALENDAR_KINDS.map(kind => (
            <View key={kind} style={styles.kindRow}>
              <Text style={styles.kindLabel}>{kind}</Text>
              <TextInput
                style={styles.symbolInput}
                value={prefs.kindSymbols[kind]}
                onChangeText={text => setSymbol(kind, text)}
                maxLength={4}
              />
              {prefs.colorMode === 'by_kind' ? (
                <View style={styles.palette}>
                  {DEFAULT_OWNER_PALETTE.map(color => (
                    <Pressable
                      key={`${kind}-${color}`}
                      style={[
                        styles.swatch,
                        { backgroundColor: color },
                        prefs.kindColors[kind] === color && styles.swatchSelected,
                      ]}
                      onPress={() => setKindColor(kind, color)}
                    />
                  ))}
                </View>
              ) : null}
            </View>
          ))}

          {prefs.colorMode === 'by_owner' ? (
            <>
              <Text style={styles.section}>Creator colors</Text>
              {members.map(member => (
                <View key={member.user_id} style={styles.memberRow}>
                  <Text style={styles.memberName}>{member.display_name}</Text>
                  <View style={styles.palette}>
                    {DEFAULT_OWNER_PALETTE.map(color => (
                      <Pressable
                        key={`${member.user_id}-${color}`}
                        style={[
                          styles.swatch,
                          { backgroundColor: color },
                          (prefs.ownerColors[member.user_id] ??
                            DEFAULT_OWNER_PALETTE[0]) === color && styles.swatchSelected,
                        ]}
                        onPress={() => setOwnerColor(member.user_id, color)}
                      />
                    ))}
                  </View>
                </View>
              ))}
            </>
          ) : null}
        </ScrollView>
        <Button title="Save" onPress={save} />
        <Button title="Close" onPress={onClose} />
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, paddingTop: 48 },
  title: { fontSize: 20, fontWeight: '600', marginBottom: 12 },
  section: { fontWeight: '600', marginTop: 16, marginBottom: 8 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#eee',
    borderRadius: 8,
  },
  chipActive: { backgroundColor: '#cce5ff' },
  chipText: { fontSize: 13 },
  kindRow: { marginBottom: 12 },
  kindLabel: { textTransform: 'capitalize', marginBottom: 4 },
  symbolInput: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 8,
    width: 72,
    marginBottom: 6,
  },
  palette: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  swatch: { width: 28, height: 28, borderRadius: 14 },
  swatchSelected: { borderWidth: 2, borderColor: '#111' },
  memberRow: { marginBottom: 12 },
  memberName: { marginBottom: 6 },
});
