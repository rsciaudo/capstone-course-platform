import { Button, Modal, Stack, Text, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useGroups } from '../../groups/GroupsContext.jsx'

export default function CreateGroupModal({ opened, onClose }) {
  return (
    <Modal opened={opened} onClose={onClose} title="add group">
      {opened ? <CreateGroupForm onClose={onClose} /> : null}
    </Modal>
  )
}

function CreateGroupForm({ onClose }) {
  const { addGroup } = useGroups()
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submit() {
    setError('')
    setSubmitting(true)
    try {
      await addGroup({ name: name.trim() })
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
        value={name}
        onChange={(event) => setName(event.currentTarget.value)}
      />
      {error ? <Text c="red">{error}</Text> : null}
      <Button onClick={submit} loading={submitting} disabled={name.trim() === ''}>
        add group
      </Button>
    </Stack>
  )
}
