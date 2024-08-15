import { AxiosError } from 'axios'
import { getErrorMessage } from '../utils/errors'
import { parseSSE } from '../utils/sse'
import { apiError } from './fixtures'

describe('parseSSE', () => {
  it('parses complete events and keeps the incomplete remainder', () => {
    const { events, rest } = parseSSE(
      'event: sources\ndata: {"sources":[]}\n\nevent: delta\ndata: {"text":"Hi"}\n\nevent: delta\ndata: {"te',
    )

    expect(events).toEqual([
      { event: 'sources', data: { sources: [] } },
      { event: 'delta', data: { text: 'Hi' } },
    ])
    expect(rest).toBe('event: delta\ndata: {"te')
  })

  it('handles CRLF line endings', () => {
    expect(parseSSE('event: done\r\ndata: {}\r\n\r\n').events).toEqual([{ event: 'done', data: {} }])
  })
})

describe('getErrorMessage', () => {
  it('uses the API detail message', () => {
    expect(getErrorMessage(apiError(409, 'An account with this email already exists'))).toBe(
      'An account with this email already exists',
    )
  })

  it('joins validation errors', () => {
    const error = apiError(422, [{ loc: ['body', 'email'], msg: 'value is not a valid email address' }])

    expect(getErrorMessage(error)).toBe('email: value is not a valid email address')
  })

  it('explains network failures', () => {
    expect(getErrorMessage(new AxiosError('Network Error'))).toMatch(/Unable to reach the server/)
  })
})
