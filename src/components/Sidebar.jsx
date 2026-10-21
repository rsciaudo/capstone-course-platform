import { NavLink, Stack } from '@mantine/core'
import { Link, useLocation } from 'react-router-dom'

const links = [
  { to: '/', label: 'Home' },
  { to: '/courses', label: 'Courses' },
  { to: '/groups', label: 'Groups' },
]

export default function Sidebar() {
  const { pathname } = useLocation()

  return (
    <Stack gap="xs">
      {links.map((link) => (
        <NavLink
          key={link.to}
          component={Link}
          to={link.to}
          label={link.label}
          active={pathname === link.to}
        />
      ))}
    </Stack>
  )
}
