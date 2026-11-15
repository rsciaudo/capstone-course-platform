import { Button, Modal, Stack, Text, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCourses } from '../../courses/CoursesContext.jsx'

export default function CreateQuizContentModal({ opened, onClose, courseId, moduleId }) {
  return (
    <Modal opened={opened} onClose={onClose} title="add quiz">
      {opened ? (
        <CreateQuizContentForm onClose={onClose} courseId={courseId} moduleId={moduleId} />
      ) : null}
    </Modal>
  )
}

function CreateQuizContentForm({ onClose, courseId, moduleId }) {
  const navigate = useNavigate()
  const { createQuiz } = useCourses()
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submit() {
    setError('')
    setSubmitting(true)
    try {
      const created = await createQuiz(courseId, moduleId, { name: name.trim() })
      onClose()
      navigate(`/courses/${courseId}/modules/${moduleId}/content/${created.id}`)
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
        add quiz
      </Button>
    </Stack>
  )
}
