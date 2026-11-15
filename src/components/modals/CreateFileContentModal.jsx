import { Button, FileInput, Modal, Stack, Text, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCourses } from '../../courses/CoursesContext.jsx'

function isImageOrPdf(file) {
  return file.type.startsWith('image/') || file.type === 'application/pdf'
}

export default function CreateFileContentModal({ opened, onClose, courseId, moduleId }) {
  return (
    <Modal opened={opened} onClose={onClose} title="add file">
      {opened ? (
        <CreateFileContentForm onClose={onClose} courseId={courseId} moduleId={moduleId} />
      ) : null}
    </Modal>
  )
}

function CreateFileContentForm({ onClose, courseId, moduleId }) {
  const navigate = useNavigate()
  const { createFile } = useCourses()
  const [name, setName] = useState('')
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const fileError = file && !isImageOrPdf(file) ? 'Choose an image or PDF' : ''

  async function submit() {
    if (!file || !isImageOrPdf(file)) {
      return
    }

    setError('')
    setSubmitting(true)
    try {
      const created = await createFile(courseId, moduleId, {
        name: name.trim(),
        file,
      })
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
      <FileInput
        label="file"
        accept="image/*,application/pdf"
        value={file}
        onChange={setFile}
        placeholder="image or pdf"
      />
      {fileError ? <Text c="red">{fileError}</Text> : null}
      {error ? <Text c="red">{error}</Text> : null}
      <Button
        onClick={submit}
        loading={submitting}
        disabled={name.trim() === '' || !file || fileError !== ''}
      >
        add file
      </Button>
    </Stack>
  )
}
