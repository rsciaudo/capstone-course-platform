import { Button, Group, Loader, Modal, PasswordInput, Select, Stack, Text, TextInput, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import DeleteButton from '../components/buttons/DeleteButton.jsx'
import EditButton from '../components/buttons/EditButton.jsx'
import UserCard from '../components/cards/UserCard.jsx'
import EditGroupModal from '../components/modals/EditGroupModal.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'
import { useUsers } from '../users/UsersContext.jsx'

const roles = [
  { value: 'student', label: 'student' },
  { value: 'educator', label: 'educator' },
]

export default function GroupDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { groups, loading: groupsLoading, error: groupsError, deleteGroup } = useGroups()
  const { users, loading: usersLoading, error: usersError, addUser } = useUsers()
  const [opened, { open, close }] = useDisclosure(false)
  const [editing, { open: openEdit, close: closeEdit }] = useDisclosure(false)
  const [name, setName] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState(null)
  const [groupId, setGroupId] = useState(String(id))
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const group = groups.find((item) => item.id === Number(id))
  const groupUsers = users.filter((user) => user.groupId === Number(id))
  const groupOptions = groups.map((item) => ({
    value: String(item.id),
    label: item.name,
  }))

  function openModal() {
    setName('')
    setUsername('')
    setPassword('')
    setRole(null)
    setGroupId(String(id))
    setFormError('')
    open()
  }

  async function submit() {
    setFormError('')
    setSubmitting(true)
    try {
      await addUser({
        name: name.trim(),
        username: username.trim(),
        password,
        role,
        groupId,
      })
      close()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setSubmitting(false)
    }
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
      {groupsLoading || usersLoading ? <Loader /> : null}
      {groupsError ? <Text c="red">{groupsError}</Text> : null}
      {usersError ? <Text c="red">{usersError}</Text> : null}
      <Button onClick={openModal} w="fit-content">
        add user
      </Button>
      {groupUsers.map((user) => (
        <UserCard
          key={user.id}
          groupId={id}
          userId={user.id}
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
          <TextInput
            label="username"
            value={username}
            onChange={(event) => setUsername(event.currentTarget.value)}
            autoComplete="off"
          />
          <PasswordInput
            label="password"
            value={password}
            onChange={(event) => setPassword(event.currentTarget.value)}
            autoComplete="new-password"
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
          {formError ? <Text c="red">{formError}</Text> : null}
          <Button
            onClick={submit}
            loading={submitting}
            disabled={
              name.trim() === '' ||
              username.trim() === '' ||
              password === '' ||
              !role ||
              !groupId
            }
          >
            add user
          </Button>
        </Stack>
      </Modal>
    </Stack>
  )
}
