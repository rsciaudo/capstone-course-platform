import { Button, Modal, Select, Stack, TextInput, Title } from '@mantine/core'
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
  const { number } = useParams()
  const { groups, addUser } = useGroups()
  const [opened, { open, close }] = useDisclosure(false)
  const [name, setName] = useState('')
  const [role, setRole] = useState(null)
  const [groupNumber, setGroupNumber] = useState(String(number))
  const group = groups.find((item) => item.number === Number(number))
  const users = group?.users ?? []
  const groupOptions = groups.map((item) => ({
    value: String(item.number),
    label: item.name,
  }))

  function openModal() {
    setName('')
    setRole(null)
    setGroupNumber(String(number))
    open()
  }

  function submit() {
    addUser(groupNumber, { name: name.trim(), role })
    close()
  }

  return (
    <Stack>
      <Title order={1}>{group?.name}</Title>
      <Button onClick={openModal} w="fit-content">
        add user
      </Button>
      {users.map((user) => (
        <UserCard
          key={user.number}
          groupNumber={number}
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
            value={groupNumber}
            onChange={setGroupNumber}
            allowDeselect={false}
          />
          <Button
            onClick={submit}
            disabled={name.trim() === '' || !role || !groupNumber}
          >
            add user
          </Button>
        </Stack>
      </Modal>
    </Stack>
  )
}
