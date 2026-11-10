import { Card, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function CourseCard({ id, name }) {
  return (
    <Card component={Link} to={`/courses/${id}`} withBorder padding="md">
      <Text>{name}</Text>
    </Card>
  )
}
