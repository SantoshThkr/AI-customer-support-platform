import type { ReactNode } from 'react'

const styles = {
  error: 'border-red-200 bg-red-50 text-red-700',
  info: 'border-sky-200 bg-sky-50 text-sky-800',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
}

export default function Alert({
  kind = 'error',
  children,
}: {
  kind?: keyof typeof styles
  children: ReactNode
}) {
  return (
    <div role={kind === 'error' ? 'alert' : 'status'} className={`rounded-md border px-3 py-2 text-sm ${styles[kind]}`}>
      {children}
    </div>
  )
}
