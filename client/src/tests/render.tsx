import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { vi } from 'vitest'
import { AuthProvider } from '../context/AuthContext'
import * as authService from '../services/auth'
import { tokenStorage } from '../services/api'
import type { User } from '../types/user'

interface Options {
  user?: User | null
  route?: string
  path?: string
}

function LocationDisplay() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}

/**
 * Render a page inside the real AuthProvider and a router.
 * Test files must call vi.mock('../services/auth') so the signed-in user can be faked.
 */
export function renderPage(element: ReactElement, { user = null, route = '/', path = '/' }: Options = {}) {
  if (user) {
    tokenStorage.set('test-token')
    vi.mocked(authService.fetchCurrentUser).mockResolvedValue(user)
  } else {
    tokenStorage.clear()
  }
  return render(
    <MemoryRouter initialEntries={[route]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <Routes>
          <Route path={path} element={element} />
          <Route path="*" element={<LocationDisplay />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}
