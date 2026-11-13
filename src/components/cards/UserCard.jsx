import { Badge, Button, Card, Group, Text } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { Link } from 'react-router-dom'
import ConfirmRemoveAccessModal from '../modals/ConfirmRemoveAccessModal.jsx'

export default function UserCard({
  groupId,
  userId,
  name,
  role,
  courseName,
  removeLabel,
  onRemove,
}) {
  const [opened, { open, close }] = useDisclosure(false)
  const link = (
    <Card
      component={Link}
      to={`/groups/${groupId}/users/${userId}`}
      withBorder={!removeLabel}
      padding="md"
      flex={1}
    >
      <Group justify="space-between">
        <Text>{name}</Text>
        <Badge>{role}</Badge>
      </Group>
    </Card>
  )

  if (!removeLabel) {
    return link
  }

  return (
    <>
      <Card withBorder>
        <Group wrap="nowrap">
          {link}
          <Button color="red" variant="light" onClick={open}>
            {removeLabel}
          </Button>
        </Group>
      </Card>
      <ConfirmRemoveAccessModal
        opened={opened}
        onClose={close}
        userName={name}
        courseName={courseName}
        onConfirm={onRemove}
      />
    </>
  )
}
