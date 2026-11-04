import { Button, Center, Paper, PasswordInput, Stack, Text, TextInput, Title } from '@mantine/core'
import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'

export default function LoginPage() {
  const { user, loading, login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (loading) {
    return null
  }

  if (user) {
    return <Navigate to="/" replace />
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(username, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Center h="100vh">
      <Paper withBorder p="lg" w={360}>
        <form onSubmit={submit}>
          <Stack>
            <Title order={2}>log in</Title>
            <TextInput
              label="username"
              name="username"
              value={username}
              onChange={(event) => setUsername(event.currentTarget.value)}
              autoComplete="username"
            />
            <PasswordInput
              label="password"
              name="password"
              value={password}
              onChange={(event) => setPassword(event.currentTarget.value)}
              autoComplete="current-password"
            />
            {error ? <Text c="red">{error}</Text> : null}
            <Button type="submit" loading={submitting} disabled={username.trim() === '' || password === ''}>
              log in
            </Button>
          </Stack>
        </form>
      </Paper>
    </Center>
  )
}
