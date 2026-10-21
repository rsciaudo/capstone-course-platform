import { Button, Stack, Title } from '@mantine/core'
import { useParams } from 'react-router-dom'
import UserCard from '../components/UserCard.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

export default function GroupDetailPage() {
  const { number } = useParams()
  const { groups, addUser } = useGroups()
  const group = groups.find((item) => item.number === Number(number))
  const users = group?.users ?? []

  return (
    <Stack>
      <Title order={1}>group {number}</Title>
      <Button onClick={() => addUser(number)} w="fit-content">
        add user
      </Button>
      {users.map((user) => (
        <UserCard
          key={user.number}
          groupNumber={number}
          userNumber={user.number}
        />
      ))}
    </Stack>
  )
}
