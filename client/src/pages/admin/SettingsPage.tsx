import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'
import { getSystemSettings, updateSystemSettings } from '../../services/admin'
import { createCategory, listCategories, updateCategory } from '../../services/categories'
import type { SystemSettings } from '../../types/ai'
import type { Category } from '../../types/ticket'
import { getErrorMessage } from '../../utils/errors'

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Settings</h1>
      <AISettings />
      <CategorySettings />
    </div>
  )
}

function Toggle({
  label,
  description,
  checked,
  disabled,
  onChange,
}: {
  label: string
  description: string
  checked: boolean
  disabled?: boolean
  onChange: (value: boolean) => void
}) {
  return (
    <label className="flex items-start gap-3">
      <input
        type="checkbox"
        className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span>
        <span className="block text-sm font-medium">{label}</span>
        <span className="block text-sm text-slate-500">{description}</span>
      </span>
    </label>
  )
}

function AISettings() {
  const [settings, setSettings] = useState<SystemSettings | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getSystemSettings()
      .then(setSettings)
      .catch((err) => setError(getErrorMessage(err)))
  }, [])

  const save = async (changes: Partial<SystemSettings>) => {
    setSaving(true)
    setError(null)
    try {
      setSettings(await updateSystemSettings(changes))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="card space-y-4 p-4">
      <h2 className="font-semibold">AI assistance</h2>
      {error && <Alert>{error}</Alert>}
      {!settings && !error && <Spinner />}
      {settings && (
        <>
          <Toggle
            label="Enable AI features"
            description="Ticket analysis, summaries, suggested replies and the agent copilot. Ticketing keeps working when this is off."
            checked={settings.ai_enabled}
            disabled={saving}
            onChange={(value) => save({ ai_enabled: value })}
          />
          <Toggle
            label="Analyze new tickets automatically"
            description="Classify category, priority and sentiment as soon as a customer submits a ticket."
            checked={settings.auto_analyze_tickets}
            disabled={saving || !settings.ai_enabled}
            onChange={(value) => save({ auto_analyze_tickets: value })}
          />
        </>
      )}
    </section>
  )
}

interface CategoryForm {
  code: string
  name: string
  description: string
}

function CategorySettings() {
  const [categories, setCategories] = useState<Category[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CategoryForm>()

  useEffect(() => {
    listCategories(true)
      .then(setCategories)
      .catch((err) => setError(getErrorMessage(err)))
  }, [])

  const replace = (updated: Category) =>
    setCategories((current) => current?.map((item) => (item.id === updated.id ? updated : item)) ?? null)

  const toggleActive = async (category: Category) => {
    setError(null)
    try {
      replace(await updateCategory(category.id, { is_active: !category.is_active }))
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const onCreate = async (values: CategoryForm) => {
    setError(null)
    try {
      const created = await createCategory({
        code: values.code.trim().toUpperCase(),
        name: values.name.trim(),
        description: values.description.trim() || null,
      })
      setCategories((current) => [...(current ?? []), created])
      reset()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <section className="card space-y-4 p-4">
      <div>
        <h2 className="font-semibold">Ticket categories</h2>
        <p className="text-sm text-slate-500">
          Descriptions are shown to the AI classifier, so keep them specific. Codes can't be changed once created.
        </p>
      </div>
      {error && <Alert>{error}</Alert>}
      {!categories && !error && <Spinner />}
      {categories && (
        <ul className="divide-y divide-slate-100">
          {categories.map((category) => (
            <li key={category.id} className="flex flex-wrap items-center justify-between gap-3 py-2">
              <div className="min-w-0">
                <p className="text-sm font-medium">
                  {category.name} <span className="font-mono text-xs text-slate-400">{category.code}</span>
                  {!category.is_active && <span className="ml-2 text-xs text-red-600">inactive</span>}
                </p>
                <p className="text-sm text-slate-500">{category.description}</p>
              </div>
              <button type="button" className="btn-secondary py-1" onClick={() => toggleActive(category)}>
                {category.is_active ? 'Deactivate' : 'Activate'}
              </button>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={handleSubmit(onCreate)} className="grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-3" noValidate>
        <div>
          <label htmlFor="category-code" className="label">
            Code
          </label>
          <input
            id="category-code"
            className="input font-mono uppercase"
            placeholder="ONBOARDING"
            {...register('code', {
              required: 'Code is required',
              pattern: { value: /^[A-Za-z][A-Za-z0-9_]+$/, message: 'Letters, numbers and underscores' },
            })}
          />
          {errors.code && <p className="field-error">{errors.code.message}</p>}
        </div>
        <div>
          <label htmlFor="category-name" className="label">
            Name
          </label>
          <input id="category-name" className="input" {...register('name', { required: 'Name is required' })} />
          {errors.name && <p className="field-error">{errors.name.message}</p>}
        </div>
        <div>
          <label htmlFor="category-description" className="label">
            Description
          </label>
          <input id="category-description" className="input" {...register('description')} />
        </div>
        <div className="sm:col-span-3">
          <button type="submit" className="btn-primary" disabled={isSubmitting}>
            Add category
          </button>
        </div>
      </form>
    </section>
  )
}
