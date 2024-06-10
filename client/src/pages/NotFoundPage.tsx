import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="py-16 text-center">
      <h1 className="text-xl font-semibold">Page not found</h1>
      <Link to="/dashboard" className="mt-4 inline-block text-indigo-600 hover:underline">
        Back to dashboard
      </Link>
    </div>
  )
}
