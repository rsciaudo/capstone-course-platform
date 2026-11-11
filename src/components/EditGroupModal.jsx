import { Button, Modal, Stack, Text, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useGroups } from '../groups/GroupsContext.jsx'

export default function EditGroupModal({ opened, onClose, groupId, name }) {
  return (
    <Modal opened={opened} onClose={onClose} title="edit group">
      {opened ? (
        <EditGroupForm onClose={onClose} groupId={groupId} name={name} />
      ) : null}
    </Modal>
  )
}

function EditGroupForm({ onClose, groupId, name }) {
  const { updateGroup } = useGroups()
  const [nextName, setNextName] = useState(name)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submit() {
    setError('')
    setSubmitting(true)
    try {
      await updateGroup(groupId, { name: nextName.trim() })
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
      {error ? <Text c="red">{error}</Text> : null}
      <Button onClick={submit} loading={submitting} disabled={nextName.trim() === ''}>
        save
      </Button>
    </Stack>
  )
}
