import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import Alert from '../components/Alert'
import { createTicket } from '../services/tickets'
import type { CreateTicketInput } from '../services/tickets'
import { getErrorMessage } from '../utils/errors'

export default function NewTicketPage() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateTicketInput>()

  const onSubmit = async (values: CreateTicketInput) => {
    setError(null)
    try {
      const ticket = await createTicket(values)
      navigate(`/tickets/${ticket.id}`, { state: { created: true } })
    } catch (err) {
      setError(getErrorMessage(err, 'Could not create the ticket'))
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-1 text-xl font-semibold">New support ticket</h1>
      <p className="mb-6 text-sm text-slate-600">
        Describe the problem in as much detail as you can. Our support team usually replies within one business day.
      </p>
      <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4 p-6" noValidate>
        {error && <Alert>{error}</Alert>}
        <div>
          <label htmlFor="subject" className="label">
            Subject
          </label>
          <input
            id="subject"
            className="input"
            placeholder="e.g. I can't log in after resetting my password"
            {...register('subject', {
              required: 'Subject is required',
              minLength: { value: 3, message: 'Subject is too short' },
              maxLength: { value: 200, message: 'Keep the subject under 200 characters' },
            })}
          />
          {errors.subject && <p className="field-error">{errors.subject.message}</p>}
        </div>
        <div>
          <label htmlFor="description" className="label">
            Description
          </label>
          <textarea
            id="description"
            rows={8}
            className="input"
            placeholder="What happened? What did you expect? Any error messages?"
            {...register('description', {
              required: 'Description is required',
              minLength: { value: 10, message: 'Please add a bit more detail (at least 10 characters)' },
              maxLength: { value: 10000, message: 'Description is too long' },
            })}
          />
          {errors.description && <p className="field-error">{errors.description.message}</p>}
        </div>
        <div className="flex justify-end gap-2">
          <Link to="/dashboard" className="btn-secondary">
            Cancel
          </Link>
          <button type="submit" className="btn-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Submitting…' : 'Submit ticket'}
          </button>
        </div>
      </form>
    </div>
  )
}
