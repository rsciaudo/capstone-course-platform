import { Button, Loader, Modal, Select, Stack, Text, TextInput, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import UserCard from '../components/UserCard.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

const roles = [
  { value: 'student', label: 'student' },
  { value: 'educator', label: 'educator' },
]

export default function GroupDetailPage() {
  const { id } = useParams()
  const { groups, loading, error, addUser } = useGroups()
  const [opened, { open, close }] = useDisclosure(false)
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

  return (
    <Stack>
      <Title order={1}>{group?.name}</Title>
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
