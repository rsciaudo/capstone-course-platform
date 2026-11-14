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
  const { addContent } = useCourses()
  const [name, setName] = useState('')
  const [file, setFile] = useState(null)
  const fileError = file && !isImageOrPdf(file) ? 'Choose an image or PDF' : ''

  function submit() {
    if (!file || !isImageOrPdf(file)) {
      return
    }

    const created = addContent(courseId, moduleId, {
      type: 'file',
      name: name.trim(),
      fileUrl: URL.createObjectURL(file),
      fileName: file.name,
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
      <FileInput
        label="file"
        accept="image/*,application/pdf"
        value={file}
        onChange={setFile}
        placeholder="image or pdf"
      />
      {fileError ? <Text c="red">{fileError}</Text> : null}
      <Button
        onClick={submit}
        disabled={name.trim() === '' || !file || fileError !== ''}
      >
        add file
      </Button>
    </Stack>
  )
}
