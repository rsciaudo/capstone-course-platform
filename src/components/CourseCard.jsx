import { Card, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function CourseCard({ number }) {
  return (
    <Card component={Link} to={`/courses/${number}`} withBorder padding="md">
      <Text>new course</Text>
    </Card>
  )
}
