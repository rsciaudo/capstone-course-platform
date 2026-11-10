import { Button, Loader, Stack, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useParams } from 'react-router-dom'
import CreateModuleModal from '../components/CreateModuleModal.jsx'
import ModuleCard from '../components/ModuleCard.jsx'
import UserCard from '../components/UserCard.jsx'
import { useCourses } from '../courses/CoursesContext.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

export default function CoursePage() {
  const { id } = useParams()
  const { courses, loading, error } = useCourses()
  const { groups } = useGroups()
  const [opened, { open, close }] = useDisclosure(false)
  const courseId = Number(id)
  const course = courses.find((item) => item.id === courseId)
  const modules = course?.modules ?? []
  const enrolledUsers = groups.flatMap((group) =>
    (group.users ?? [])
      .filter((user) => (user.courseIds ?? []).includes(courseId))
      .map((user) => ({ ...user, groupId: group.id })),
  )
  const editors = groups.flatMap((group) =>
    (group.users ?? [])
      .filter((user) => (user.editableCourseIds ?? []).includes(courseId))
      .map((user) => ({ ...user, groupId: group.id })),
  )

  return (
    <Stack>
      <Title order={1}>{course?.name}</Title>
      {loading ? <Loader /> : null}
      {error ? <Text c="red">{error}</Text> : null}
      <Button onClick={open} w="fit-content">
        add module
      </Button>
      {modules.map((module) => (
        <ModuleCard
          key={module.id}
          courseId={id}
          moduleId={module.id}
          name={module.name}
        />
      ))}
      <Title order={2}>enrolled users</Title>
      {enrolledUsers.map((user) => (
        <UserCard
          key={`${user.groupId}-${user.number}`}
          groupId={user.groupId}
          userNumber={user.number}
          name={user.name}
          role={user.role}
        />
      ))}
      <Title order={2}>editors</Title>
      {editors.map((user) => (
        <UserCard
          key={`${user.groupId}-${user.number}`}
          groupId={user.groupId}
          userNumber={user.number}
          name={user.name}
          role={user.role}
        />
      ))}
      <CreateModuleModal opened={opened} onClose={close} courseId={id} />
    </Stack>
  )
}
