import { Button, Modal, Select, Stack, Text, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useGroups } from '../../groups/GroupsContext.jsx'
import { useUsers } from '../../users/UsersContext.jsx'

const roles = [
  { value: 'student', label: 'student' },
  { value: 'educator', label: 'educator' },
]

export default function EditUserModal({ opened, onClose, userId, name, role, groupId }) {
  return (
    <Modal opened={opened} onClose={onClose} title="edit user">
      {opened ? (
        <EditUserForm
          onClose={onClose}
          userId={userId}
          name={name}
          role={role}
          groupId={groupId}
        />
      ) : null}
    </Modal>
  )
}

function EditUserForm({ onClose, userId, name, role, groupId }) {
  const { groups } = useGroups()
  const { updateUser } = useUsers()
  const [nextName, setNextName] = useState(name)
  const [nextRole, setNextRole] = useState(role)
  const [nextGroupId, setNextGroupId] = useState(groupId == null ? null : String(groupId))
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const groupOptions = groups.map((item) => ({
    value: String(item.id),
    label: item.name,
  }))

  async function submit() {
    setError('')
    setSubmitting(true)
    try {
      await updateUser(userId, {
        name: nextName.trim(),
        role: nextRole,
        groupId: nextGroupId,
      })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
      setSubmitting(false)
    }
  }

  return (
    <Stack>
      <TextInput
        label="name"
        value={nextName}
        onChange={(event) => setNextName(event.currentTarget.value)}
      />
      <Select
        label="role"
        data={roles}
        value={nextRole}
        onChange={setNextRole}
        allowDeselect={false}
      />
      <Select
        label="group"
        data={groupOptions}
        value={nextGroupId}
        onChange={setNextGroupId}
        allowDeselect={false}
      />
      {error ? <Text c="red">{error}</Text> : null}
      <Button
        onClick={submit}
        loading={submitting}
        disabled={nextName.trim() === '' || !nextRole || !nextGroupId}
      >
        save
      </Button>
    </Stack>
  )
}
