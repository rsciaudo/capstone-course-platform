import { Center, Loader } from '@mantine/core'
import { createContext, useContext, useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'

const AuthContext = createContext(null)

async function readError(response) {
  const body = await response.json().catch(() => null)
  if (body && typeof body.detail === 'string') {
    return body.detail
  }
  return 'Login failed'
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true

    fetch('/api/auth/me', { credentials: 'include' })
      .then(async (response) => {
        if (!active) {
          return
        }
        if (!response.ok) {
          setUser(null)
          return
        }
        setUser(await response.json())
      })
      .catch(() => {
        if (active) {
          setUser(null)
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [])

  async function login(username, password) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    })
    if (!response.ok) {
      throw new Error(await readError(response))
    }
    setUser(await response.json())
  }

  async function logout() {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    })
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (value === null) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return value
}

export function RequireAuth() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
