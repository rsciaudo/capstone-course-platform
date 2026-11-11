import { Card, Group, Text } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { Link } from 'react-router-dom'
import { useCourses } from '../../courses/CoursesContext.jsx'
import DeleteButton from '../buttons/DeleteButton.jsx'
import EditButton from '../buttons/EditButton.jsx'
import EditCourseModal from '../modals/EditCourseModal.jsx'

export default function CourseCard({ id, name }) {
  const { deleteCourse } = useCourses()
  const [editing, { open, close }] = useDisclosure(false)

  return (
    <>
      <Card withBorder flex={1}>
        <Group wrap="nowrap">
          <Card component={Link} to={`/courses/${id}`} padding="md" flex={1}>
            <Text>{name}</Text>
          </Card>
          <EditButton onClick={open} />
          <DeleteButton name={name} onDelete={() => deleteCourse(id)} />
        </Group>
      </Card>
      <EditCourseModal opened={editing} onClose={close} courseId={id} name={name} />
    </>
  )
}
