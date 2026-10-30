import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import React, { useState } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { useAuth } from '../features/auth/AuthContext';
import { LoginScreen } from '../features/auth/screens/LoginScreen';
import { RegisterScreen } from '../features/auth/screens/RegisterScreen';
import { DashboardScreen } from '../features/dashboard/DashboardScreen';
import { GroceryListDetailScreen } from '../features/groceries/GroceryListDetailScreen';
import { GroceryListsScreen } from '../features/groceries/GroceryListsScreen';
import { RemindersScreen } from '../features/reminders/RemindersScreen';
import { OnboardingScreen } from '../features/families/screens/OnboardingScreen';
import type { AuthStackParamList, MainStackParamList } from './types';

const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const MainStack = createNativeStackNavigator<MainStackParamList>();

function MainApp({ membership }: { membership: NonNullable<ReturnType<typeof useAuth>['user']>['memberships'][0] }) {
  return (
    <MainStack.Navigator screenOptions={{ headerShown: false }}>
      <MainStack.Screen name="Dashboard">
        {({ navigation }) => (
          <DashboardScreen
            membership={membership}
            onOpenGroceries={() => navigation.navigate('GroceryLists')}
            onOpenReminders={() => navigation.navigate('Reminders')}
          />
        )}
      </MainStack.Screen>
      <MainStack.Screen name="GroceryLists">
        {({ navigation }) => (
          <GroceryListsScreen
            membership={membership}
            onBack={() => navigation.goBack()}
            onOpenList={listId => navigation.navigate('GroceryListDetail', { listId })}
          />
        )}
      </MainStack.Screen>
      <MainStack.Screen name="GroceryListDetail">
        {({ navigation, route }) => (
          <GroceryListDetailScreen
            membership={membership}
            listId={route.params.listId}
            onBack={() => navigation.goBack()}
          />
        )}
      </MainStack.Screen>
      <MainStack.Screen name="Reminders">
        {({ navigation }) => (
          <RemindersScreen membership={membership} onBack={() => navigation.goBack()} />
        )}
      </MainStack.Screen>
    </MainStack.Navigator>
  );
}

export function RootNavigator() {
  const { user, loading } = useAuth();
  const [showRegister, setShowRegister] = useState(false);

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  const membership = user?.memberships[0];

  return (
    <NavigationContainer>
      {!user ? (
        <AuthStack.Navigator screenOptions={{ headerShown: false }}>
          <AuthStack.Screen name="Login">
            {() =>
              showRegister ? (
                <RegisterScreen onBack={() => setShowRegister(false)} />
              ) : (
                <LoginScreen onRegister={() => setShowRegister(true)} />
              )
            }
          </AuthStack.Screen>
        </AuthStack.Navigator>
      ) : !membership ? (
        <OnboardingScreen />
      ) : (
        <MainApp membership={membership} />
      )}
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  loading: { flex: 1, justifyContent: 'center' },
});
