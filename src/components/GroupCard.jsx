import { Card, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function GroupCard({ id, name }) {
  return (
    <Card component={Link} to={`/groups/${id}`} withBorder padding="md">
      <Text>{name}</Text>
    </Card>
  )
}
