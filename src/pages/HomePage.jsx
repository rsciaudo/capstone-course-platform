import { Anchor, Stack, Text, Title } from '@mantine/core'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'

const homes = {
  'super-user': {
    title: 'platform',
    description: 'You can see every group and course.',
    links: [
      { to: '/groups', label: 'Groups' },
      { to: '/courses', label: 'Courses' },
    ],
  },
  admin: {
    title: 'your groups',
    description: 'Groups you manage.',
    links: [{ to: '/groups', label: 'Groups' }],
  },
  educator: {
    title: 'your courses',
    description: 'Courses you teach.',
    links: [{ to: '/courses', label: 'Courses' }],
  },
  student: {
    title: 'your courses',
    description: 'Courses you are enrolled in.',
    links: [{ to: '/courses', label: 'Courses' }],
  },
}

export default function HomePage() {
  const { user } = useAuth()
  const home = homes[user.role] ?? {
    title: 'home',
    description: '',
    links: [],
  }

  return (
    <Stack>
      <Title order={1}>{home.title}</Title>
      {home.description ? <Text>{home.description}</Text> : null}
      {home.links.map((link) => (
        <Anchor key={link.to} component={Link} to={link.to}>
          {link.label}
        </Anchor>
      ))}
    </Stack>
  )
}
