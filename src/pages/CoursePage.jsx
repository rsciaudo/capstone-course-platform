import { Button, Stack, Title } from '@mantine/core'
import { useParams } from 'react-router-dom'
import ModuleCard from '../components/ModuleCard.jsx'
import { useCourses } from '../courses/CoursesContext.jsx'

export default function CoursePage() {
  const { number } = useParams()
  const { courses, addModule } = useCourses()
  const course = courses.find((item) => item.number === Number(number))
  const modules = course?.modules ?? []

  return (
    <Stack>
      <Title order={1}>course {number}</Title>
      <Button onClick={() => addModule(number)} w="fit-content">
        add module
      </Button>
      {modules.map((module) => (
        <ModuleCard
          key={module.number}
          courseNumber={number}
          moduleNumber={module.number}
        />
      ))}
    </Stack>
  )
}
