import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TicketsPage from '../pages/TicketsPage'
import * as categoryService from '../services/categories'
import * as ticketService from '../services/tickets'
import { apiError, customer, makeTicket, page } from './fixtures'
import { renderPage } from './render'

vi.mock('../services/auth')
vi.mock('../services/tickets')
vi.mock('../services/categories')

const renderList = () => renderPage(<TicketsPage />, { user: customer, route: '/tickets', path: '/tickets' })

beforeEach(() => {
  vi.mocked(categoryService.listCategories).mockResolvedValue([])
})

describe('TicketsPage', () => {
  it('shows a loading state, then the customer tickets', async () => {
    vi.mocked(ticketService.listTickets).mockResolvedValue(
      page([makeTicket({ id: 1, subject: 'Cannot log in' }), makeTicket({ id: 2, subject: 'Refund request', status: 'RESOLVED' })]),
    )
    renderList()

    expect(await screen.findByRole('status')).toHaveTextContent(/loading/i)
    expect(await screen.findByRole('link', { name: /Cannot log in/ })).toHaveAttribute('href', '/tickets/1')
    expect(screen.getByRole('link', { name: /Refund request/ })).toBeInTheDocument()
    expect(within(screen.getByRole('table')).getByText('Resolved')).toBeInTheDocument()
  })

  it('shows an empty state', async () => {
    vi.mocked(ticketService.listTickets).mockResolvedValue(page([]))
    renderList()

    expect(await screen.findByText('No tickets found')).toBeInTheDocument()
    expect(screen.getByText('Tickets you create will show up here.')).toBeInTheDocument()
  })

  it('shows an error when tickets cannot be loaded', async () => {
    vi.mocked(ticketService.listTickets).mockRejectedValue(apiError(500, 'Internal server error'))
    renderList()

    expect(await screen.findByRole('alert')).toHaveTextContent('Internal server error')
  })

  it('filters by status', async () => {
    vi.mocked(ticketService.listTickets).mockResolvedValue(page([makeTicket()]))
    renderList()
    await screen.findByRole('link', { name: /Cannot log in/ })

    await userEvent.selectOptions(screen.getByLabelText('Status'), 'WAITING_FOR_CUSTOMER')

    await waitFor(() =>
      expect(ticketService.listTickets).toHaveBeenLastCalledWith({ page: 1, status: ['WAITING_FOR_CUSTOMER'] }),
    )
  })

  it('searches after the user stops typing', async () => {
    vi.mocked(ticketService.listTickets).mockResolvedValue(page([makeTicket()]))
    renderList()
    await screen.findByRole('link', { name: /Cannot log in/ })

    await userEvent.type(screen.getByLabelText('Search tickets'), 'invoice')

    await waitFor(() =>
      expect(ticketService.listTickets).toHaveBeenLastCalledWith({ page: 1, search: 'invoice' }),
    )
  })
})
