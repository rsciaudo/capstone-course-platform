import { Card, Group, Text } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { Link } from 'react-router-dom'
import { useGroups } from '../../groups/GroupsContext.jsx'
import DeleteButton from '../buttons/DeleteButton.jsx'
import EditButton from '../buttons/EditButton.jsx'
import EditGroupModal from '../modals/EditGroupModal.jsx'

export default function GroupCard({ id, name }) {
  const { deleteGroup } = useGroups()
  const [editing, { open, close }] = useDisclosure(false)

  return (
    <>
      <Card withBorder flex={1}>
        <Group wrap="nowrap">
          <Card component={Link} to={`/groups/${id}`} padding="md" flex={1}>
            <Text>{name}</Text>
          </Card>
          <EditButton onClick={open} />
          <DeleteButton name={name} onDelete={() => deleteGroup(id)} />
        </Group>
      </Card>
      <EditGroupModal opened={editing} onClose={close} groupId={id} name={name} />
    </>
  )
}
