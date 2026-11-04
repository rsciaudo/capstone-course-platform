import { Button, Group, Title } from '@mantine/core'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function onLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <Group justify="space-between" h="100%" wrap="nowrap">
      <Title order={3}>header</Title>
      <Group gap="sm" wrap="nowrap">
        <Title order={5}>{user.name}</Title>
        <Button size="xs" variant="default" onClick={onLogout}>
          log out
        </Button>
      </Group>
    </Group>
  )
}
