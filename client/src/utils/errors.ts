import axios from 'axios'

interface ValidationIssue {
  loc?: (string | number)[]
  msg: string
}

export function getErrorMessage(error: unknown, fallback = 'Something went wrong. Please try again.') {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return 'Unable to reach the server. Check your connection and try again.'
    }
    const detail = error.response.data?.detail
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return (detail as ValidationIssue[])
        .map((issue) => {
          const field = issue.loc?.[issue.loc.length - 1]
          return field ? `${field}: ${issue.msg}` : issue.msg
        })
        .join(', ')
    }
    return fallback
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}
