import { Button, Loader, Stack, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import CourseCard from '../components/cards/CourseCard.jsx'
import CreateCourseModal from '../components/modals/CreateCourseModal.jsx'
import { useCourses } from '../courses/CoursesContext.jsx'

export default function CoursesPage() {
  const { courses, loading, error } = useCourses()
  const [opened, { open, close }] = useDisclosure(false)

  return (
    <Stack>
      <Title order={1}>courses</Title>
      <Button onClick={open} w="fit-content">
        create course
      </Button>
      {loading ? <Loader /> : null}
      {error ? <Text c="red">{error}</Text> : null}
      {courses.map((course) => (
        <CourseCard key={course.id} id={course.id} name={course.name} />
      ))}
      <CreateCourseModal opened={opened} onClose={close} />
    </Stack>
  )
}
