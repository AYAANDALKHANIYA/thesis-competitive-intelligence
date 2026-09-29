import { Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigurationProvider, useConfiguration } from './context/ConfigurationContext'
import AppShell from './components/layout/AppShell'
import Setup from './pages/Setup'
import Overview from './pages/Overview'
import Competitors from './pages/Competitors'
import Trends from './pages/Trends'
import SentimentTopics from './pages/SentimentTopics'
import Predictions from './pages/Predictions'
import Intelligence from './pages/Intelligence'
import Evidence from './pages/Evidence'
import Sources from './pages/Sources'
import Collection from './pages/Collection'
import Dashboard from './pages/Dashboard'
import { Skeleton } from './components/ui/skeleton'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
    },
  },
})

function DashboardRoutes() {
  return (
    <AppShell>
      <Routes>
        <Route path="/overview" element={<Overview />} />
        <Route path="/competitors" element={<Competitors />} />
        <Route path="/trends" element={<Trends />} />
        <Route path="/sentiment-topics" element={<SentimentTopics />} />
        <Route path="/predictions" element={<Predictions />} />
        <Route path="/intelligence" element={<Intelligence />} />
        <Route path="/evidence" element={<Evidence />} />
        <Route path="/sources" element={<Sources />} />
        <Route path="/collection" element={<Collection />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  )
}

function AppRouter() {
  const { configured, isLoading } = useConfiguration()

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Skeleton className="h-32 w-32 rounded-full" />
      </div>
    )
  }

  return (
    <Routes>
      {/* Route the root to the new dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<Dashboard />} />
      
      {/* Legacy routes kept until verified */}
      <Route path="/setup" element={configured ? <Navigate to="/overview" replace /> : <Setup />} />
      <Route path="/*" element={!configured ? <Navigate to="/setup" replace /> : <DashboardRoutes />} />
    </Routes>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigurationProvider>
        <AppRouter />
      </ConfigurationProvider>
    </QueryClientProvider>
  )
}

export default App
