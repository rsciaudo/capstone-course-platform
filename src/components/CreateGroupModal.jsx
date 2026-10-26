import { Button, Modal, Stack, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useGroups } from '../groups/GroupsContext.jsx'

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

  function submit() {
    addGroup({ name: name.trim() })
    onClose()
  }

  return (
    <Stack>
      <TextInput
        label="name"
        value={name}
        onChange={(event) => setName(event.currentTarget.value)}
      />
      <Button onClick={submit} disabled={name.trim() === ''}>
        add group
      </Button>
    </Stack>
  )
}
