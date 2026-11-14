import { Button, Modal, Stack, TextInput } from '@mantine/core'
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
  const { addContent } = useCourses()
  const [name, setName] = useState('')

  function submit() {
    const created = addContent(courseId, moduleId, {
      type: 'quiz',
      name: name.trim(),
    })
    onClose()
    navigate(`/courses/${courseId}/modules/${moduleId}/content/${created.number}`)
  }

  return (
    <Stack>
      <TextInput
        label="name"
        value={name}
        onChange={(event) => setName(event.currentTarget.value)}
      />
      <Button onClick={submit} disabled={name.trim() === ''}>
        add quiz
      </Button>
    </Stack>
  )
}
