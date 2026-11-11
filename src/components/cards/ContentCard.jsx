import { Card, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function ContentCard({
  courseId,
  moduleId,
  contentNumber,
  label,
}) {
  return (
    <Card
      component={Link}
      to={`/courses/${courseId}/modules/${moduleId}/content/${contentNumber}`}
      withBorder
      padding="md"
    >
      <Text>{label}</Text>
    </Card>
  )
}
