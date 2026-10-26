import { Button, Modal, Select, Stack, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useCourses } from '../courses/CoursesContext.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

export default function CreateCourseModal({ opened, onClose }) {
  return (
    <Modal opened={opened} onClose={onClose} title="create course">
      {opened ? <CreateCourseForm onClose={onClose} /> : null}
    </Modal>
  )
}

function CreateCourseForm({ onClose }) {
  const { createCourse } = useCourses()
  const { groups } = useGroups()
  const [name, setName] = useState('')
  const [groupNumber, setGroupNumber] = useState(null)
  const groupOptions = groups.map((group) => ({
    value: String(group.number),
    label: group.name,
  }))

  function submit() {
    createCourse({ name: name.trim(), groupNumber })
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
        label="group"
        data={groupOptions}
        value={groupNumber}
        onChange={setGroupNumber}
        allowDeselect={false}
      />
      <Button onClick={submit} disabled={name.trim() === '' || !groupNumber}>
        create course
      </Button>
    </Stack>
  )
}
