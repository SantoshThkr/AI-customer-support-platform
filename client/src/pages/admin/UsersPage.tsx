import { useCallback, useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import Alert from '../../components/Alert'
import EmptyState from '../../components/EmptyState'
import Pagination from '../../components/Pagination'
import Spinner from '../../components/Spinner'
import { useAuth } from '../../context/AuthContext'
import { createUser, listUsers, updateUser } from '../../services/users'
import type { CreateUserInput } from '../../services/users'
import type { Page, User, UserRole } from '../../types/user'
import { getErrorMessage } from '../../utils/errors'
import { formatDate } from '../../utils/format'

const ROLES: UserRole[] = ['CUSTOMER', 'AGENT', 'ADMIN']

export default function UsersPage() {
  const { user: currentUser } = useAuth()
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<UserRole | ''>('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<Page<User> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setData(await listUsers({ search, role, page }))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [search, role, page])

  useEffect(() => {
    const timer = setTimeout(load, 250)
    return () => clearTimeout(timer)
  }, [load])

  const saveChange = async (user: User, change: { role?: UserRole; is_active?: boolean }) => {
    setError(null)
    try {
      const updated = await updateUser(user.id, change)
      setData((current) =>
        current && { ...current, items: current.items.map((item) => (item.id === updated.id ? updated : item)) },
      )
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Users</h1>
        <button type="button" className="btn-primary" onClick={() => setShowForm((value) => !value)}>
          {showForm ? 'Cancel' : 'Add user'}
        </button>
      </div>

      {showForm && (
        <CreateUserForm
          onCreated={() => {
            setShowForm(false)
            load()
          }}
        />
      )}

      <div className="flex flex-wrap gap-3">
        <input
          className="input max-w-xs"
          placeholder="Search name or email"
          aria-label="Search users"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value)
            setPage(1)
          }}
        />
        <select
          className="input w-auto"
          aria-label="Filter by role"
          value={role}
          onChange={(event) => {
            setRole(event.target.value as UserRole | '')
            setPage(1)
          }}
        >
          <option value="">All roles</option>
          {ROLES.map((value) => (
            <option key={value} value={value}>
              {value.toLowerCase()}
            </option>
          ))}
        </select>
      </div>

      {error && <Alert>{error}</Alert>}

      {loading && !data ? (
        <Spinner />
      ) : data && data.items.length === 0 ? (
        <EmptyState title="No users found" />
      ) : (
        data && (
          <div className="card overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-2">Name</th>
                  <th className="px-4 py-2">Email</th>
                  <th className="px-4 py-2">Role</th>
                  <th className="px-4 py-2">Joined</th>
                  <th className="px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((user) => {
                  const isSelf = user.id === currentUser?.id
                  return (
                    <tr key={user.id}>
                      <td className="px-4 py-2 font-medium">{user.name}</td>
                      <td className="px-4 py-2 text-slate-600">{user.email}</td>
                      <td className="px-4 py-2">
                        <select
                          className="input w-auto py-1"
                          aria-label={`Role for ${user.email}`}
                          value={user.role}
                          disabled={isSelf}
                          onChange={(event) => saveChange(user, { role: event.target.value as UserRole })}
                        >
                          {ROLES.map((value) => (
                            <option key={value} value={value}>
                              {value.toLowerCase()}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-2 text-slate-600">{formatDate(user.created_at)}</td>
                      <td className="px-4 py-2">
                        <button
                          type="button"
                          className="btn-secondary py-1"
                          disabled={isSelf}
                          onClick={() => saveChange(user, { is_active: !user.is_active })}
                        >
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        {!user.is_active && <span className="ml-2 text-xs text-red-600">inactive</span>}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )
      )}

      {data && <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />}
    </div>
  )
}

function CreateUserForm({ onCreated }: { onCreated: () => void }) {
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateUserInput>({ defaultValues: { role: 'AGENT' } })

  const onSubmit = async (values: CreateUserInput) => {
    setError(null)
    try {
      await createUser(values)
      onCreated()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="card grid gap-4 p-4 sm:grid-cols-2" noValidate>
      {error && (
        <div className="sm:col-span-2">
          <Alert>{error}</Alert>
        </div>
      )}
      <div>
        <label htmlFor="new-name" className="label">
          Name
        </label>
        <input id="new-name" className="input" {...register('name', { required: 'Name is required' })} />
        {errors.name && <p className="field-error">{errors.name.message}</p>}
      </div>
      <div>
        <label htmlFor="new-email" className="label">
          Email
        </label>
        <input
          id="new-email"
          type="email"
          className="input"
          {...register('email', { required: 'Email is required' })}
        />
        {errors.email && <p className="field-error">{errors.email.message}</p>}
      </div>
      <div>
        <label htmlFor="new-password" className="label">
          Temporary password
        </label>
        <input
          id="new-password"
          type="password"
          className="input"
          {...register('password', { required: 'Password is required', minLength: { value: 8, message: 'Use at least 8 characters' } })}
        />
        {errors.password && <p className="field-error">{errors.password.message}</p>}
      </div>
      <div>
        <label htmlFor="new-role" className="label">
          Role
        </label>
        <select id="new-role" className="input" {...register('role')}>
          {ROLES.map((value) => (
            <option key={value} value={value}>
              {value.toLowerCase()}
            </option>
          ))}
        </select>
      </div>
      <div className="sm:col-span-2">
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Creating…' : 'Create user'}
        </button>
      </div>
    </form>
  )
}
