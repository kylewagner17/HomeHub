import { AuthProvider } from './features/auth/AuthContext';
import { RootNavigator } from './navigation/RootNavigator';

function App() {
  return (
    <AuthProvider>
      <RootNavigator />
    </AuthProvider>
  );
}

export default App;
