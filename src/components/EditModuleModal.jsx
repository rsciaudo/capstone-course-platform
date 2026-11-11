import { Button, Modal, Stack, Text, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useCourses } from '../courses/CoursesContext.jsx'

export default function EditModuleModal({ opened, onClose, courseId, moduleId, name }) {
  return (
    <Modal opened={opened} onClose={onClose} title="edit module">
      {opened ? (
        <EditModuleForm
          onClose={onClose}
          courseId={courseId}
          moduleId={moduleId}
          name={name}
        />
      ) : null}
    </Modal>
  )
}

function EditModuleForm({ onClose, courseId, moduleId, name }) {
  const { updateModule } = useCourses()
  const [nextName, setNextName] = useState(name)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submit() {
    setError('')
    setSubmitting(true)
    try {
      await updateModule(courseId, moduleId, { name: nextName.trim() })
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
