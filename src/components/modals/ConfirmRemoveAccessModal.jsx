import { Button, Group, Modal, Stack, Text } from '@mantine/core'
import { useState } from 'react'

export default function ConfirmRemoveAccessModal({
  opened,
  onClose,
  userName,
  courseName,
  onConfirm,
}) {
  return (
    <Modal opened={opened} onClose={onClose} title={`remove access to ${courseName}`}>
      {opened ? (
        <ConfirmRemoveAccessForm
          userName={userName}
          courseName={courseName}
          onClose={onClose}
          onConfirm={onConfirm}
        />
      ) : null}
    </Modal>
  )
}

function ConfirmRemoveAccessForm({ userName, courseName, onClose, onConfirm }) {
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
      <Text>
        Remove {userName}'s access to {courseName}? This cannot be undone.
      </Text>
      {error ? <Text c="red">{error}</Text> : null}
      <Group>
        <Button variant="default" onClick={onClose}>
          cancel
        </Button>
        <Button color="red" onClick={submit} loading={submitting}>
          remove
        </Button>
      </Group>
    </Stack>
  )
}
