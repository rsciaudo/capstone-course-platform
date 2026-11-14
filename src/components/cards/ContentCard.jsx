import { Card, Group, Text } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { Link } from 'react-router-dom'
import { useCourses } from '../../courses/CoursesContext.jsx'
import DeleteButton from '../buttons/DeleteButton.jsx'
import EditButton from '../buttons/EditButton.jsx'
import EditFileContentModal from '../modals/EditFileContentModal.jsx'

export default function ContentCard({
  courseId,
  moduleId,
  contentNumber,
  label,
  type,
}) {
  const { deleteContent } = useCourses()
  const [editing, { open, close }] = useDisclosure(false)
  const to = `/courses/${courseId}/modules/${moduleId}/content/${contentNumber}`

  if (type !== 'file') {
    return (
      <Card component={Link} to={to} withBorder padding="md">
        <Text>{label}</Text>
      </Card>
    )
  }

  return (
    <>
      <Card withBorder flex={1}>
        <Group wrap="nowrap">
          <Card component={Link} to={to} padding="md" flex={1}>
            <Text>{label}</Text>
          </Card>
          <EditButton onClick={open} />
          <DeleteButton
            name={label}
            onDelete={() => deleteContent(courseId, moduleId, contentNumber)}
          />
        </Group>
      </Card>
      <EditFileContentModal
        opened={editing}
        onClose={close}
        courseId={courseId}
        moduleId={moduleId}
        contentNumber={contentNumber}
        name={label}
      />
    </>
  )
}
