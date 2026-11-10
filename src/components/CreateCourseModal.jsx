import { Button, Modal, Select, Stack, Text, TextInput } from '@mantine/core'
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
  const [groupId, setGroupId] = useState(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const groupOptions = groups.map((group) => ({
    value: String(group.id),
    label: group.name,
  }))

  async function submit() {
    setError('')
    setSubmitting(true)
    try {
      await createCourse({ name: name.trim(), groupId })
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
        label="group"
        data={groupOptions}
        value={groupId}
        onChange={setGroupId}
        allowDeselect={false}
      />
      {error ? <Text c="red">{error}</Text> : null}
      <Button
        onClick={submit}
        loading={submitting}
        disabled={name.trim() === '' || !groupId}
      >
        create course
      </Button>
    </Stack>
  )
}
