import { Badge, Button, Card, Group, Text } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { Link } from 'react-router-dom'
import { useUsers } from '../../users/UsersContext.jsx'
import DeleteButton from '../buttons/DeleteButton.jsx'
import EditButton from '../buttons/EditButton.jsx'
import ConfirmRemoveAccessModal from '../modals/ConfirmRemoveAccessModal.jsx'
import EditUserModal from '../modals/EditUserModal.jsx'

export default function UserCard({
  groupId,
  userId,
  name,
  role,
  courseName,
  removeLabel,
  onRemove,
}) {
  const { deleteUser } = useUsers()
  const [removing, { open: openRemove, close: closeRemove }] = useDisclosure(false)
  const [editing, { open: openEdit, close: closeEdit }] = useDisclosure(false)

  return (
    <>
      <Card withBorder flex={1}>
        <Group wrap="nowrap">
          <Card
            component={Link}
            to={`/groups/${groupId}/users/${userId}`}
            padding="md"
            flex={1}
          >
            <Group justify="space-between">
              <Text>{name}</Text>
              <Badge>{role}</Badge>
            </Group>
          </Card>
          {removeLabel ? (
            <Button color="red" variant="light" onClick={openRemove}>
              {removeLabel}
            </Button>
          ) : null}
          <EditButton onClick={openEdit} />
          <DeleteButton name={name} onDelete={() => deleteUser(userId)} />
        </Group>
      </Card>
      {removeLabel ? (
        <ConfirmRemoveAccessModal
          opened={removing}
          onClose={closeRemove}
          userName={name}
          courseName={courseName}
          onConfirm={onRemove}
        />
      ) : null}
      <EditUserModal
        opened={editing}
        onClose={closeEdit}
        userId={userId}
        name={name}
        role={role}
        groupId={groupId}
      />
    </>
  )
}
