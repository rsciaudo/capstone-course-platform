import { Card, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function ContentCard({
  courseNumber,
  moduleNumber,
  contentNumber,
  label,
}) {
  return (
    <Card
      component={Link}
      to={`/courses/${courseNumber}/modules/${moduleNumber}/content/${contentNumber}`}
      withBorder
      padding="md"
    >
      <Text>{label}</Text>
    </Card>
  )
}
