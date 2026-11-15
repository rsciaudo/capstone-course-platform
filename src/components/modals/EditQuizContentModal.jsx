import { Button, Modal, Stack, Text, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useCourses } from '../../courses/CoursesContext.jsx'

export default function EditQuizContentModal({
  opened,
  onClose,
  courseId,
  moduleId,
  contentId,
  name,
}) {
  return (
    <Modal opened={opened} onClose={onClose} title="edit quiz">
      {opened ? (
        <EditQuizContentForm
          onClose={onClose}
          courseId={courseId}
          moduleId={moduleId}
          contentId={contentId}
          name={name}
        />
      ) : null}
    </Modal>
  )
}

function EditQuizContentForm({ onClose, courseId, moduleId, contentId, name }) {
  const { renameContent } = useCourses()
  const [nextName, setNextName] = useState(name)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submit() {
    setError('')
    setSubmitting(true)
    try {
      await renameContent(courseId, moduleId, contentId, nextName.trim())
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
