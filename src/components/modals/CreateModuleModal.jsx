import { Button, Modal, Select, Stack, Text, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useCourses } from '../../courses/CoursesContext.jsx'

export default function CreateModuleModal({ opened, onClose, courseId }) {
  return (
    <Modal opened={opened} onClose={onClose} title="add module">
      {opened ? (
        <CreateModuleForm onClose={onClose} courseId={courseId} />
      ) : null}
    </Modal>
  )
}

function CreateModuleForm({ onClose, courseId }) {
  const { courses, addModule } = useCourses()
  const [name, setName] = useState('')
  const [selectedCourse, setSelectedCourse] = useState(
    courseId == null ? null : String(courseId),
  )
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const courseOptions = courses.map((course) => ({
    value: String(course.id),
    label: course.name,
  }))

  async function submit() {
    setError('')
    setSubmitting(true)
    try {
      await addModule(selectedCourse, { name: name.trim() })
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
      <Select
        label="course"
        data={courseOptions}
        value={selectedCourse}
        onChange={setSelectedCourse}
        allowDeselect={false}
      />
      {error ? <Text c="red">{error}</Text> : null}
      <Button
        onClick={submit}
        loading={submitting}
        disabled={name.trim() === '' || !selectedCourse}
      >
        add module
      </Button>
    </Stack>
  )
}
