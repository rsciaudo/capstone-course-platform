import { Card, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function GroupCard({ number }) {
  return (
    <Card component={Link} to={`/groups/${number}`} withBorder padding="md">
      <Text>group {number}</Text>
    </Card>
  )
}
