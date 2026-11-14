import { Button, Modal, Stack, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useCourses } from '../../courses/CoursesContext.jsx'

export default function EditQuizContentModal({
  opened,
  onClose,
  courseId,
  moduleId,
  contentNumber,
  name,
}) {
  return (
    <Modal opened={opened} onClose={onClose} title="edit quiz">
      {opened ? (
        <EditQuizContentForm
          onClose={onClose}
          courseId={courseId}
          moduleId={moduleId}
          contentNumber={contentNumber}
          name={name}
        />
      ) : null}
    </Modal>
  )
}

function EditQuizContentForm({ onClose, courseId, moduleId, contentNumber, name }) {
  const { updateContent } = useCourses()
  const [nextName, setNextName] = useState(name)

  function submit() {
    updateContent(courseId, moduleId, contentNumber, { name: nextName.trim() })
    onClose()
  }

  return (
    <Stack>
      <TextInput
        label="name"
        value={nextName}
        onChange={(event) => setNextName(event.currentTarget.value)}
      />
      <Button onClick={submit} disabled={nextName.trim() === ''}>
        save
      </Button>
    </Stack>
  )
}
