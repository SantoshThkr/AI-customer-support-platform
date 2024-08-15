import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import NewTicketPage from '../pages/NewTicketPage'
import * as ticketService from '../services/tickets'
import { apiError, customer, makeTicket } from './fixtures'
import { renderPage } from './render'

vi.mock('../services/auth')
vi.mock('../services/tickets')

const renderForm = () => renderPage(<NewTicketPage />, { user: customer, route: '/tickets/new', path: '/tickets/new' })

describe('NewTicketPage', () => {
  it('validates the form before submitting', async () => {
    renderForm()

    await userEvent.type(screen.getByLabelText('Subject'), 'Hi')
    await userEvent.type(screen.getByLabelText('Description'), 'short')
    await userEvent.click(screen.getByRole('button', { name: 'Submit ticket' }))

    expect(await screen.findByText('Subject is too short')).toBeInTheDocument()
    expect(screen.getByText(/at least 10 characters/)).toBeInTheDocument()
    expect(ticketService.createTicket).not.toHaveBeenCalled()
  })

  it('creates the ticket and opens it', async () => {
    vi.mocked(ticketService.createTicket).mockResolvedValue(makeTicket({ id: 42 }))
    renderForm()

    await userEvent.type(screen.getByLabelText('Subject'), 'Export is empty')
    await userEvent.type(screen.getByLabelText('Description'), 'The CSV export only has headers.')
    await userEvent.click(screen.getByRole('button', { name: 'Submit ticket' }))

    expect(await screen.findByTestId('location')).toHaveTextContent('/tickets/42')
    expect(ticketService.createTicket).toHaveBeenCalledWith({
      subject: 'Export is empty',
      description: 'The CSV export only has headers.',
    })
  })

  it('keeps the form and shows an error when the API fails', async () => {
    vi.mocked(ticketService.createTicket).mockRejectedValue(apiError(500, 'Internal server error'))
    renderForm()

    await userEvent.type(screen.getByLabelText('Subject'), 'Export is empty')
    await userEvent.type(screen.getByLabelText('Description'), 'The CSV export only has headers.')
    await userEvent.click(screen.getByRole('button', { name: 'Submit ticket' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Internal server error')
    expect(screen.getByLabelText('Subject')).toHaveValue('Export is empty')
  })
})
