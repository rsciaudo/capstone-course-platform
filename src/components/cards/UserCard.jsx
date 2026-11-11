import { Badge, Card, Group, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function UserCard({ groupId, userNumber, name, role }) {
  return (
    <Card
      component={Link}
      to={`/groups/${groupId}/users/${userNumber}`}
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
