import { Group, Stack, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useNavigate, useParams } from 'react-router-dom'
import DeleteButton from '../components/buttons/DeleteButton.jsx'
import EditButton from '../components/buttons/EditButton.jsx'
import FileContent from '../components/content/FileContent.jsx'
import QuizContent from '../components/content/QuizContent.jsx'
import SlideContent from '../components/content/SlideContent.jsx'
import EditFileContentModal from '../components/modals/EditFileContentModal.jsx'
import { contentLabel, useCourses } from '../courses/CoursesContext.jsx'

const contentComponents = {
  quiz: QuizContent,
  file: FileContent,
  slide: SlideContent,
}

export default function ContentDetailPage() {
  const { id, moduleId, contentNumber } = useParams()
  const navigate = useNavigate()
  const { courses, deleteContent } = useCourses()
  const [editing, { open, close }] = useDisclosure(false)
  const course = courses.find((item) => item.id === Number(id))
  const module = course?.modules.find((item) => item.id === Number(moduleId))
  const content = module?.content ?? []
  const item = content.find((entry) => entry.number === Number(contentNumber))

  if (!item) {
    return null
  }

  function removeFile() {
    deleteContent(id, moduleId, item.number)
    navigate(`/courses/${id}/modules/${moduleId}`)
  }

  const Content = contentComponents[item.type]

  return (
    <Stack>
      <Group justify="space-between" align="center">
        <Title order={1}>{contentLabel(content, item)}</Title>
        {item.type === 'file' ? (
          <Group>
            <EditButton onClick={open} />
            <DeleteButton name={item.name} onDelete={removeFile} />
          </Group>
        ) : null}
      </Group>
      <Content fileUrl={item.fileUrl} />
      {item.type === 'file' ? (
        <EditFileContentModal
          opened={editing}
          onClose={close}
          courseId={id}
          moduleId={moduleId}
          contentNumber={item.number}
          name={item.name ?? ''}
        />
      ) : null}
    </Stack>
  )
}
