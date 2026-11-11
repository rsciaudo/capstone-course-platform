import { Button, Group, Modal, Stack, Text } from '@mantine/core'
import { useState } from 'react'

export default function ConfirmDeleteModal({ opened, onClose, name, onConfirm }) {
  return (
    <Modal opened={opened} onClose={onClose} title={`delete ${name}`}>
      {opened ? (
        <ConfirmDeleteForm name={name} onClose={onClose} onConfirm={onConfirm} />
      ) : null}
    </Modal>
  )
}

function ConfirmDeleteForm({ name, onClose, onConfirm }) {
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submit() {
    setError('')
    setSubmitting(true)
    try {
      await onConfirm()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
      setSubmitting(false)
    }
  }

  return (
    <Stack>
      <Text>Delete {name}? This cannot be undone.</Text>
      {error ? <Text c="red">{error}</Text> : null}
      <Group>
        <Button variant="default" onClick={onClose}>
          cancel
        </Button>
        <Button color="red" onClick={submit} loading={submitting}>
          delete
        </Button>
      </Group>
    </Stack>
  )
}
