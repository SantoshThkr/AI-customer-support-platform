import type { ReactNode } from 'react'

export default function AuthCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="card w-full max-w-sm p-6">
        <p className="mb-1 text-center text-sm font-semibold text-indigo-700">Support Desk</p>
        <h1 className="mb-6 text-center text-xl font-semibold">{title}</h1>
        {children}
      </div>
    </div>
  )
}
