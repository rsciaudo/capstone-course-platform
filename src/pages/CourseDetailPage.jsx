import { Button, Stack, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useParams } from 'react-router-dom'
import CreateModuleModal from '../components/CreateModuleModal.jsx'
import ModuleCard from '../components/ModuleCard.jsx'
import UserCard from '../components/UserCard.jsx'
import { useCourses } from '../courses/CoursesContext.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

export default function CoursePage() {
  const { number } = useParams()
  const { courses } = useCourses()
  const { groups } = useGroups()
  const [opened, { open, close }] = useDisclosure(false)
  const course = courses.find((item) => item.number === Number(number))
  const modules = course?.modules ?? []
  const enrolledUsers = groups.flatMap((group) =>
    (group.users ?? [])
      .filter((user) => (user.courseNumbers ?? []).includes(Number(number)))
      .map((user) => ({ ...user, groupNumber: group.number })),
  )
  const editors = groups.flatMap((group) =>
    (group.users ?? [])
      .filter((user) => (user.editableCourseNumbers ?? []).includes(Number(number)))
      .map((user) => ({ ...user, groupNumber: group.number })),
  )

  return (
    <Stack>
      <Title order={1}>{course?.name}</Title>
      <Button onClick={open} w="fit-content">
        add module
      </Button>
      {modules.map((module) => (
        <ModuleCard
          key={module.number}
          courseNumber={number}
          moduleNumber={module.number}
          name={module.name}
        />
      ))}
      <Title order={2}>enrolled users</Title>
      {enrolledUsers.map((user) => (
        <UserCard
          key={`${user.groupNumber}-${user.number}`}
          groupNumber={user.groupNumber}
          userNumber={user.number}
          name={user.name}
          role={user.role}
        />
      ))}
      <Title order={2}>editors</Title>
      {editors.map((user) => (
        <UserCard
          key={`{user.groupNumber}-${user.number}`}
          groupNumber={user.groupNumber}
          userNumber={user.number}
          name={user.name}
          role={user.role}
        />
      ))}
      <CreateModuleModal
        opened={opened}
        onClose={close}
        courseNumber={number}
      />
    </Stack>
  )
}
