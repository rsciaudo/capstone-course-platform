import { Card, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function ModuleCard({ courseId, moduleId, name }) {
  return (
    <Card
      component={Link}
      to={`/courses/${courseId}/modules/${moduleId}`}
      withBorder
      padding="md"
    >
      <Text>{name}</Text>
    </Card>
  )
}
