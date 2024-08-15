import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TicketDetailPage from '../pages/TicketDetailPage'
import * as aiService from '../services/ai'
import * as categoryService from '../services/categories'
import * as knowledgeService from '../services/knowledge'
import * as ticketService from '../services/tickets'
import * as userService from '../services/users'
import type { User } from '../types/user'
import { agent, apiError, customer, makeMessage, makeTicket } from './fixtures'
import { renderPage } from './render'

vi.mock('../services/auth')
vi.mock('../services/tickets')
vi.mock('../services/users')
vi.mock('../services/categories')
vi.mock('../services/ai')
vi.mock('../services/knowledge')

const ticket = makeTicket({ ai_summary: 'Customer cannot log in after a reset.', ai_sentiment: 'NEGATIVE' })

beforeEach(() => {
  vi.mocked(ticketService.getTicket).mockResolvedValue(ticket)
  vi.mocked(ticketService.listMessages).mockResolvedValue([
    makeMessage({ id: 1, message: 'Could you try a private window?' }),
    makeMessage({ id: 2, message: 'Probably the SSO cache', is_internal: true }),
  ])
  vi.mocked(ticketService.listTicketEvents).mockResolvedValue([])
  vi.mocked(categoryService.listCategories).mockResolvedValue([])
  vi.mocked(userService.listAgents).mockResolvedValue([{ id: agent.id, name: agent.name, email: agent.email, role: 'AGENT' }])
  vi.mocked(aiService.getAIStatus).mockResolvedValue({ available: true, reason: null })
  vi.mocked(knowledgeService.searchKnowledge).mockResolvedValue({ mode: 'keyword', results: [] })
})

const renderTicket = (user: User) => renderPage(<TicketDetailPage />, { user, route: '/tickets/7', path: '/tickets/:id' })

describe('TicketDetailPage for agents', () => {
  it('shows the ticket, AI summary and the conversation with internal notes marked', async () => {
    renderTicket(agent)

    expect(await screen.findByRole('heading', { name: /Cannot log in/ })).toBeInTheDocument()
    expect(screen.getByText('Customer cannot log in after a reset.')).toBeInTheDocument()
    const conversation = screen.getByRole('list', { name: 'Conversation' })
    expect(within(conversation).getByText('I reset my password but still get an error.')).toBeInTheDocument()
    const note = within(conversation).getByTestId('internal-note')
    expect(note).toHaveTextContent('Probably the SSO cache')
    expect(note).toHaveTextContent('Internal note')
  })

  it('sends a reply to the customer', async () => {
    vi.mocked(ticketService.addMessage).mockResolvedValue(makeMessage({ id: 3, message: 'Please clear your cache.' }))
    renderTicket(agent)
    await screen.findByRole('heading', { name: /Cannot log in/ })

    await userEvent.type(screen.getByLabelText('Reply'), 'Please clear your cache.')
    await userEvent.click(screen.getByRole('button', { name: 'Send reply' }))

    expect(ticketService.addMessage).toHaveBeenCalledWith(7, 'Please clear your cache.', false)
    expect(await screen.findByText('Please clear your cache.')).toBeInTheDocument()
    expect(screen.getByLabelText('Reply')).toHaveValue('')
  })

  it('adds an internal note', async () => {
    vi.mocked(ticketService.addMessage).mockResolvedValue(
      makeMessage({ id: 4, message: 'Escalating to engineering', is_internal: true }),
    )
    renderTicket(agent)
    await screen.findByRole('heading', { name: /Cannot log in/ })

    await userEvent.click(screen.getByRole('tab', { name: 'Internal note' }))
    await userEvent.type(screen.getByLabelText('Internal note'), 'Escalating to engineering')
    await userEvent.click(screen.getByRole('button', { name: 'Add note' }))

    expect(ticketService.addMessage).toHaveBeenCalledWith(7, 'Escalating to engineering', true)
    await waitFor(() => expect(screen.getAllByTestId('internal-note')).toHaveLength(2))
  })

  it('shows an error when sending fails', async () => {
    vi.mocked(ticketService.addMessage).mockRejectedValue(apiError(403, 'This ticket is assigned to another agent'))
    renderTicket(agent)
    await screen.findByRole('heading', { name: /Cannot log in/ })

    await userEvent.type(screen.getByLabelText('Reply'), 'Hello')
    await userEvent.click(screen.getByRole('button', { name: 'Send reply' }))

    expect(await screen.findByText('This ticket is assigned to another agent')).toBeInTheDocument()
    expect(screen.getByLabelText('Reply')).toHaveValue('Hello')
  })

  it('streams an AI suggestion that the agent can use and edit', async () => {
    vi.mocked(aiService.streamSuggestion).mockImplementation(async (_id, _instructions, handlers) => {
      handlers.onSources?.([{ document_id: 3, document_title: 'Password Reset Guide', section: null }])
      handlers.onText('Hi Jane, ')
      handlers.onText('please request a new reset link.')
    })
    renderTicket(agent)
    await screen.findByRole('heading', { name: /Cannot log in/ })

    await userEvent.click(await screen.findByRole('button', { name: 'Suggest reply' }))

    expect(await screen.findByTestId('suggestion')).toHaveTextContent('Hi Jane, please request a new reset link.')
    expect(screen.getByRole('link', { name: 'Password Reset Guide' })).toBeInTheDocument()
    expect(ticketService.addMessage).not.toHaveBeenCalled()

    await userEvent.click(screen.getByRole('button', { name: 'Use suggestion' }))

    const reply = screen.getByLabelText('Reply')
    expect(reply).toHaveValue('Hi Jane, please request a new reset link.')
    expect(screen.getByText(/written by AI/)).toBeInTheDocument()
    expect(screen.queryByTestId('suggestion')).not.toBeInTheDocument()

    await userEvent.type(reply, ' Thanks!')
    expect(reply).toHaveValue('Hi Jane, please request a new reset link. Thanks!')
  })

  it('discards a suggestion without touching the reply box', async () => {
    vi.mocked(aiService.streamSuggestion).mockImplementation(async (_id, _instructions, handlers) => {
      handlers.onText('A draft reply')
    })
    renderTicket(agent)

    await userEvent.click(await screen.findByRole('button', { name: 'Suggest reply' }))
    await screen.findByTestId('suggestion')
    await userEvent.click(screen.getByRole('button', { name: 'Discard' }))

    expect(screen.queryByTestId('suggestion')).not.toBeInTheDocument()
    expect(screen.getByLabelText('Reply')).toHaveValue('')
  })

  it('shows AI errors without breaking the page', async () => {
    vi.mocked(aiService.streamSuggestion).mockRejectedValue(new Error('The AI service timed out. Please try again.'))
    renderTicket(agent)

    await userEvent.click(await screen.findByRole('button', { name: 'Suggest reply' }))

    expect(await screen.findByText('The AI service timed out. Please try again.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Send reply' })).toBeInTheDocument()
  })

  it('hides AI tools when AI is unavailable', async () => {
    vi.mocked(aiService.getAIStatus).mockResolvedValue({
      available: false,
      reason: 'AI features are not configured on this server',
    })
    renderTicket(agent)

    expect(await screen.findByText(/AI features are not configured/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Suggest reply' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Send reply' })).toBeInTheDocument()
  })
})

describe('TicketDetailPage for customers', () => {
  it('has no internal note option and can close the ticket', async () => {
    vi.mocked(ticketService.listMessages).mockResolvedValue([makeMessage({ id: 1, message: 'Could you try a private window?' })])
    vi.mocked(ticketService.updateTicket).mockResolvedValue({ ...ticket, status: 'CLOSED' })
    renderTicket(customer)

    expect(await screen.findByText('Could you try a private window?')).toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Internal note' })).not.toBeInTheDocument()
    expect(screen.queryByText('Customer cannot log in after a reset.')).not.toBeInTheDocument()
    expect(aiService.getAIStatus).not.toHaveBeenCalled()

    await userEvent.click(screen.getByRole('button', { name: 'Close ticket' }))

    expect(ticketService.updateTicket).toHaveBeenCalledWith(7, { status: 'CLOSED' })
    expect(await screen.findByText(/This ticket is closed/)).toBeInTheDocument()
  })

  it('shows an error when the ticket cannot be loaded', async () => {
    vi.mocked(ticketService.getTicket).mockRejectedValue(apiError(404, 'Ticket not found'))
    renderTicket(customer)

    expect(await screen.findByRole('alert')).toHaveTextContent('Ticket not found')
  })
})
