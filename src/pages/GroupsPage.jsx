import { Button, Loader, Stack, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import GroupCard from '../components/cards/GroupCard.jsx'
import CreateGroupModal from '../components/modals/CreateGroupModal.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

export default function GroupsPage() {
  const { groups, loading, error } = useGroups()
  const [opened, { open, close }] = useDisclosure(false)

  return (
    <Stack>
      <Title order={1}>groups</Title>
      <Button onClick={open} w="fit-content">
        add group
      </Button>
      {loading ? <Loader /> : null}
      {error ? <Text c="red">{error}</Text> : null}
      {groups.map((group) => (
        <GroupCard key={group.id} id={group.id} name={group.name} />
      ))}
      <CreateGroupModal opened={opened} onClose={close} />
    </Stack>
  )
}
