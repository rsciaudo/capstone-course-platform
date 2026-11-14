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
  contentNumber,
  name,
}) {
  return (
    <Modal opened={opened} onClose={onClose} title="edit file">
      {opened ? (
        <EditFileContentForm
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

function EditFileContentForm({ onClose, courseId, moduleId, contentNumber, name }) {
  const { updateContent } = useCourses()
  const [nextName, setNextName] = useState(name)
  const [file, setFile] = useState(null)
  const fileError = file && !isImageOrPdf(file) ? 'Choose an image or PDF' : ''

  function submit() {
    if (file && !isImageOrPdf(file)) {
      return
    }

    const patch = { name: nextName.trim() }
    if (file) {
      patch.fileUrl = URL.createObjectURL(file)
      patch.fileName = file.name
    }
    updateContent(courseId, moduleId, contentNumber, patch)
    onClose()
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
      <Button
        onClick={submit}
        disabled={nextName.trim() === '' || fileError !== ''}
      >
        save
      </Button>
    </Stack>
  )
}
