import { Button, Stack, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import CourseCard from '../components/CourseCard.jsx'
import CreateCourseModal from '../components/CreateCourseModal.jsx'
import { useCourses } from '../courses/CoursesContext.jsx'

export default function CoursesPage() {
  const { courses } = useCourses()
  const [opened, { open, close }] = useDisclosure(false)

  return (
    <Stack>
      <Title order={1}>courses</Title>
      <Button onClick={open} w="fit-content">
        create course
      </Button>
      {courses.map((course) => (
        <CourseCard
          key={course.number}
          number={course.number}
          name={course.name}
        />
      ))}
      <CreateCourseModal opened={opened} onClose={close} />
    </Stack>
  )
}
