import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AgentDashboard from '../pages/AgentDashboard'
import * as categoryService from '../services/categories'
import * as ticketService from '../services/tickets'
import * as userService from '../services/users'
import { agent, makeTicket, page } from './fixtures'
import { renderPage } from './render'

vi.mock('../services/auth')
vi.mock('../services/tickets')
vi.mock('../services/users')
vi.mock('../services/categories')

beforeEach(() => {
  vi.mocked(categoryService.listCategories).mockResolvedValue([
    { id: 1, code: 'BILLING', name: 'Billing', description: null, is_active: true },
  ])
  vi.mocked(userService.listAgents).mockResolvedValue([])
  vi.mocked(ticketService.getTicketStats).mockResolvedValue({
    by_status: { OPEN: 3, IN_PROGRESS: 1, WAITING_FOR_CUSTOMER: 2, RESOLVED: 0, CLOSED: 0 },
    assigned_to_me: 2,
    unassigned: 1,
    urgent: 1,
  })
  vi.mocked(ticketService.listTickets).mockResolvedValue(page([makeTicket({ category: 'BILLING' })]))
})

const lastQuery = () => vi.mocked(ticketService.listTickets).mock.lastCall?.[0]

describe('AgentDashboard', () => {
  it('starts on the open queue and shows counts', async () => {
    renderPage(<AgentDashboard />, { user: agent, route: '/dashboard', path: '/dashboard' })

    expect(await screen.findByRole('tab', { name: /Open tickets\s*4/ })).toHaveAttribute('aria-selected', 'true')
    expect(await within(await screen.findByRole('table')).findByText('Billing')).toBeInTheDocument()
    expect(lastQuery()).toMatchObject({ status: ['OPEN', 'IN_PROGRESS'], sort: 'updated_at' })
  })

  it('switches to my tickets', async () => {
    renderPage(<AgentDashboard />, { user: agent, route: '/dashboard', path: '/dashboard' })
    await screen.findByRole('link', { name: /Cannot log in/ })

    await userEvent.click(screen.getByRole('tab', { name: /My tickets/ }))

    await waitFor(() => expect(lastQuery()).toMatchObject({ assigned_agent: 'me' }))
  })

  it('combines filters with the selected queue', async () => {
    renderPage(<AgentDashboard />, { user: agent, route: '/dashboard', path: '/dashboard' })
    await screen.findByRole('link', { name: /Cannot log in/ })

    await userEvent.selectOptions(screen.getByLabelText('Priority'), 'URGENT')
    await userEvent.selectOptions(screen.getByLabelText('Category'), 'BILLING')

    await waitFor(() =>
      expect(lastQuery()).toMatchObject({
        status: ['OPEN', 'IN_PROGRESS'],
        priority: ['URGENT'],
        category: 'BILLING',
      }),
    )
  })

  it('shows an empty state for a queue with no tickets', async () => {
    vi.mocked(ticketService.listTickets).mockResolvedValue(page([]))
    renderPage(<AgentDashboard />, { user: agent, route: '/dashboard?queue=waiting', path: '/dashboard' })

    expect(await screen.findByText('Nothing here')).toBeInTheDocument()
    expect(lastQuery()).toMatchObject({ status: ['WAITING_FOR_CUSTOMER'] })
  })
})
