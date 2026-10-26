import { Button, Modal, Select, Stack, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useCourses } from '../courses/CoursesContext.jsx'

export default function CreateModuleModal({ opened, onClose, courseNumber }) {
  return (
    <Modal opened={opened} onClose={onClose} title="add module">
      {opened ? (
        <CreateModuleForm onClose={onClose} courseNumber={courseNumber} />
      ) : null}
    </Modal>
  )
}

function CreateModuleForm({ onClose, courseNumber }) {
  const { courses, addModule } = useCourses()
  const [name, setName] = useState('')
  const [selectedCourse, setSelectedCourse] = useState(
    courseNumber == null ? null : String(courseNumber),
  )
  const courseOptions = courses.map((course) => ({
    value: String(course.number),
    label: course.name,
  }))

  function submit() {
    addModule(selectedCourse, { name: name.trim() })
    onClose()
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
      <Button onClick={submit} disabled={name.trim() === '' || !selectedCourse}>
        add module
      </Button>
    </Stack>
  )
}
