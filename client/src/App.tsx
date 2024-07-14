import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import DashboardPage from './pages/DashboardPage'
import KnowledgeDocumentPage from './pages/KnowledgeDocumentPage'
import KnowledgePage from './pages/KnowledgePage'
import LoginPage from './pages/LoginPage'
import NewTicketPage from './pages/NewTicketPage'
import NotFoundPage from './pages/NotFoundPage'
import RegisterPage from './pages/RegisterPage'
import TicketDetailPage from './pages/TicketDetailPage'
import TicketsPage from './pages/TicketsPage'
import AnalyticsPage from './pages/admin/AnalyticsPage'
import SettingsPage from './pages/admin/SettingsPage'
import UsersPage from './pages/admin/UsersPage'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/tickets" element={<TicketsPage />} />
            <Route path="/tickets/:id" element={<TicketDetailPage />} />
            <Route element={<ProtectedRoute roles={['CUSTOMER']} />}>
              <Route path="/tickets/new" element={<NewTicketPage />} />
            </Route>
            <Route element={<ProtectedRoute roles={['AGENT', 'ADMIN']} />}>
              <Route path="/knowledge" element={<KnowledgePage />} />
              <Route path="/knowledge/:id" element={<KnowledgeDocumentPage />} />
            </Route>
            <Route element={<ProtectedRoute roles={['ADMIN']} />}>
              <Route path="/admin" element={<AnalyticsPage />} />
              <Route path="/admin/users" element={<UsersPage />} />
              <Route path="/admin/settings" element={<SettingsPage />} />
            </Route>
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  )
}
