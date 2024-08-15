import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginPage from '../pages/LoginPage'
import * as authService from '../services/auth'
import { apiError, customer } from './fixtures'
import { renderPage } from './render'

vi.mock('../services/auth')

describe('LoginPage', () => {
  it('requires email and password', async () => {
    renderPage(<LoginPage />, { route: '/login', path: '/login' })

    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Email is required')).toBeInTheDocument()
    expect(screen.getByText('Password is required')).toBeInTheDocument()
    expect(authService.login).not.toHaveBeenCalled()
  })

  it('signs in and goes to the dashboard', async () => {
    vi.mocked(authService.login).mockResolvedValue({ access_token: 'token', token_type: 'bearer', user: customer })
    renderPage(<LoginPage />, { route: '/login', path: '/login' })

    await userEvent.type(screen.getByLabelText('Email'), 'jane@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'password123')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByTestId('location')).toHaveTextContent('/dashboard')
    expect(authService.login).toHaveBeenCalledWith('jane@example.com', 'password123')
    expect(localStorage.getItem('support_token')).toBe('token')
  })

  it('shows the error returned by the API', async () => {
    vi.mocked(authService.login).mockRejectedValue(apiError(401, 'Incorrect email or password'))
    renderPage(<LoginPage />, { route: '/login', path: '/login' })

    await userEvent.type(screen.getByLabelText('Email'), 'jane@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'wrong-password')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect email or password')
    expect(screen.queryByTestId('location')).not.toBeInTheDocument()
  })
})
