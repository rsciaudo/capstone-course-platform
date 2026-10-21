import { Card, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function UserCard({ groupNumber, userNumber }) {
  return (
    <Card
      component={Link}
      to={`/groups/${groupNumber}/users/${userNumber}`}
      withBorder
      padding="md"
    >
      <Text>user {userNumber}</Text>
    </Card>
  )
}
