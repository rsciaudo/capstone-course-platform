import { Button, Stack, Title } from '@mantine/core'
import CourseCard from '../components/CourseCard.jsx'
import { useCourses } from '../courses/CoursesContext.jsx'

export default function CoursesPage() {
  const { courses, createCourse } = useCourses()

  return (
    <Stack>
      <Title order={1}>courses</Title>
      <Button onClick={createCourse} w="fit-content">
        create course
      </Button>
      {courses.map((course) => (
        <CourseCard key={course.number} number={course.number} />
      ))}
    </Stack>
  )
}
