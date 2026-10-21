import { Button, Stack, Title } from '@mantine/core'
import GroupCard from '../components/GroupCard.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

export default function GroupsPage() {
  const { groups, addGroup } = useGroups()

  return (
    <Stack>
      <Title order={1}>groups</Title>
      <Button onClick={addGroup} w="fit-content">
        add group
      </Button>
      {groups.map((group) => (
        <GroupCard key={group.number} number={group.number} />
      ))}
    </Stack>
  )
}
