import { Card, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function ModuleCard({ courseNumber, moduleNumber }) {
  return (
    <Card
      component={Link}
      to={`/courses/${courseNumber}/modules/${moduleNumber}`}
      withBorder
      padding="md"
    >
      <Text>module {moduleNumber}</Text>
    </Card>
  )
}
