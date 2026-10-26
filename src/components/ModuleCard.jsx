import { Card, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function ModuleCard({ courseNumber, moduleNumber, name }) {
  return (
    <Card
      component={Link}
      to={`/courses/${courseNumber}/modules/${moduleNumber}`}
      withBorder
      padding="md"
    >
      <Text>{name}</Text>
    </Card>
  )
}
