import { ThemeProvider } from './theme/ThemeProvider'
import { AuthProvider } from './contexts/AuthContext'
import { AppRouter } from './routes/AppRouter'

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
