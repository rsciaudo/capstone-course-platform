import { Card, Group, Text } from '@mantine/core'
import { Link } from 'react-router-dom'
import { useCourses } from '../../courses/CoursesContext.jsx'
import DeleteButton from '../buttons/DeleteButton.jsx'

export default function ContentCard({ courseId, moduleId, contentId, label, type }) {
  const { deleteContent } = useCourses()
  const to = `/courses/${courseId}/modules/${moduleId}/content/${contentId}`

  function remove() {
    return deleteContent(courseId, moduleId, contentId)
  }

  if (type === 'quiz' || type === 'file') {
    return (
      <Card withBorder flex={1}>
        <Group wrap="nowrap">
          <Card component={Link} to={to} padding="md" flex={1}>
            <Text>{label}</Text>
          </Card>
          <DeleteButton name={label} onDelete={remove} />
        </Group>
      </Card>
    )
  }

  return (
    <Card component={Link} to={to} withBorder padding="md">
      <Text>{label}</Text>
    </Card>
  )
}
