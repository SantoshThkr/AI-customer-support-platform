import { useAuth } from '../context/AuthContext'
import AgentDashboard from './AgentDashboard'
import CustomerDashboard from './CustomerDashboard'

export default function DashboardPage() {
  const { user } = useAuth()
  return user?.role === 'CUSTOMER' ? <CustomerDashboard /> : <AgentDashboard />
}
