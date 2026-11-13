import { Badge, Card, Group, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function UserCard({ groupId, userId, name, role }) {
  return (
    <Card
      component={Link}
      to={`/groups/${groupId}/users/${userId}`}
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
