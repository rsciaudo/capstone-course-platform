import { Button, Group, Loader, Modal, Select, Stack, Text, TextInput, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import DeleteButton from '../components/DeleteButton.jsx'
import EditButton from '../components/EditButton.jsx'
import EditGroupModal from '../components/EditGroupModal.jsx'
import UserCard from '../components/UserCard.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

const roles = [
  { value: 'student', label: 'student' },
  { value: 'educator', label: 'educator' },
]

export default function GroupDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { groups, loading, error, addUser, deleteGroup } = useGroups()
  const [opened, { open, close }] = useDisclosure(false)
  const [editing, { open: openEdit, close: closeEdit }] = useDisclosure(false)
  const [name, setName] = useState('')
  const [role, setRole] = useState(null)
  const [groupId, setGroupId] = useState(String(id))
  const group = groups.find((item) => item.id === Number(id))
  const users = group?.users ?? []
  const groupOptions = groups.map((item) => ({
    value: String(item.id),
    label: item.name,
  }))

  function openModal() {
    setName('')
    setRole(null)
    setGroupId(String(id))
    open()
  }

  function submit() {
    addUser(groupId, { name: name.trim(), role })
    close()
  }

  async function removeGroup() {
    await deleteGroup(id)
    navigate('/groups')
  }

  return (
    <Stack>
      <Group justify="space-between" align="center">
        <Title order={1}>{group?.name}</Title>
        {group ? (
          <Group>
            <EditButton onClick={openEdit} />
            <DeleteButton name={group.name} onDelete={removeGroup} />
          </Group>
        ) : null}
      </Group>
      {loading ? <Loader /> : null}
      {error ? <Text c="red">{error}</Text> : null}
      <Button onClick={openModal} w="fit-content">
        add user
      </Button>
      {users.map((user) => (
        <UserCard
          key={user.number}
          groupId={id}
          userNumber={user.number}
          name={user.name}
          role={user.role}
        />
      ))}
      <EditGroupModal
        opened={editing}
        onClose={closeEdit}
        groupId={id}
        name={group?.name ?? ''}
      />
      <Modal opened={opened} onClose={close} title="add user">
        <Stack>
          <TextInput
            label="name"
            value={name}
            onChange={(event) => setName(event.currentTarget.value)}
          />
          <Select
            label="role"
            data={roles}
            value={role}
            onChange={setRole}
            allowDeselect={false}
          />
          <Select
            label="group"
            data={groupOptions}
            value={groupId}
            onChange={setGroupId}
            allowDeselect={false}
          />
          <Button
            onClick={submit}
            disabled={name.trim() === '' || !role || !groupId}
          >
            add user
          </Button>
        </Stack>
      </Modal>
    </Stack>
  )
}
