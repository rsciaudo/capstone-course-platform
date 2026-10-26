import { Card, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function GroupCard({ number, name }) {
  return (
    <Card component={Link} to={`/groups/${number}`} withBorder padding="md">
      <Text>{name}</Text>
    </Card>
  )
}
