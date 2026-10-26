import { Button, Stack, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import CreateGroupModal from '../components/CreateGroupModal.jsx'
import GroupCard from '../components/GroupCard.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

export default function GroupsPage() {
  const { groups } = useGroups()
  const [opened, { open, close }] = useDisclosure(false)

  return (
    <Stack>
      <Title order={1}>groups</Title>
      <Button onClick={open} w="fit-content">
        add group
      </Button>
      {groups.map((group) => (
        <GroupCard key={group.number} number={group.number} name={group.name} />
      ))}
      <CreateGroupModal opened={opened} onClose={close} />
    </Stack>
  )
}
