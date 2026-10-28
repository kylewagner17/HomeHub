/** Persist JWT in Keychain so sessions survive app restarts (M1). */
import * as Keychain from 'react-native-keychain';

const SERVICE = 'homehub.auth';

export async function saveAccessToken(token: string): Promise<void> {
  await Keychain.setGenericPassword('access', token, { service: SERVICE });
}

export async function getAccessToken(): Promise<string | null> {
  const credentials = await Keychain.getGenericPassword({ service: SERVICE });
  if (!credentials) {
    return null;
  }
  return credentials.password;
}

export async function clearAccessToken(): Promise<void> {
  await Keychain.resetGenericPassword({ service: SERVICE });
}
