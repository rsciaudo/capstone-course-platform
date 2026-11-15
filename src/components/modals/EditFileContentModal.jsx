import { Button, FileInput, Modal, Stack, Text, TextInput } from '@mantine/core'
import { useState } from 'react'
import { useCourses } from '../../courses/CoursesContext.jsx'

function isImageOrPdf(file) {
  return file.type.startsWith('image/') || file.type === 'application/pdf'
}

export default function EditFileContentModal({
  opened,
  onClose,
  courseId,
  moduleId,
  contentId,
  name,
}) {
  return (
    <Modal opened={opened} onClose={onClose} title="edit file">
      {opened ? (
        <EditFileContentForm
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

function EditFileContentForm({ onClose, courseId, moduleId, contentId, name }) {
  const { updateFile } = useCourses()
  const [nextName, setNextName] = useState(name)
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const fileError = file && !isImageOrPdf(file) ? 'Choose an image or PDF' : ''

  async function submit() {
    if (file && !isImageOrPdf(file)) {
      return
    }

    setError('')
    setSubmitting(true)
    try {
      await updateFile(courseId, moduleId, contentId, {
        name: nextName.trim(),
        file,
      })
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
      <FileInput
        label="file"
        accept="image/*,application/pdf"
        value={file}
        onChange={setFile}
        placeholder="keep current file"
      />
      {fileError ? <Text c="red">{fileError}</Text> : null}
      {error ? <Text c="red">{error}</Text> : null}
      <Button
        onClick={submit}
        loading={submitting}
        disabled={nextName.trim() === '' || fileError !== ''}
      >
        save
      </Button>
    </Stack>
  )
}
