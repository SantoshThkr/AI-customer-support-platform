import { useAuth } from '../context/AuthContext'

export default function DashboardPage() {
  const { user } = useAuth()
  return (
    <div>
      <h1 className="text-xl font-semibold">Welcome, {user?.name}</h1>
    </div>
  )
}
