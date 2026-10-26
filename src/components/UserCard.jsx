import { Badge, Card, Group, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function UserCard({ groupNumber, userNumber, name, role }) {
  return (
    <Card
      component={Link}
      to={`/groups/${groupNumber}/users/${userNumber}`}
      withBorder
      padding="md"
    >
      <Group justify="space-between">
        <Text>{name}</Text>
        <Badge>{role}</Badge>
      </Group>
    </Card>
  )
}
