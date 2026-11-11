import { Button, Group, Loader, Stack, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useNavigate, useParams } from 'react-router-dom'
import DeleteButton from '../components/buttons/DeleteButton.jsx'
import EditButton from '../components/buttons/EditButton.jsx'
import ModuleCard from '../components/cards/ModuleCard.jsx'
import UserCard from '../components/cards/UserCard.jsx'
import CreateModuleModal from '../components/modals/CreateModuleModal.jsx'
import EditCourseModal from '../components/modals/EditCourseModal.jsx'
import { useCourses } from '../courses/CoursesContext.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

export default function CoursePage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { courses, loading, error, deleteCourse } = useCourses()
  const { groups } = useGroups()
  const [opened, { open, close }] = useDisclosure(false)
  const [editing, { open: openEdit, close: closeEdit }] = useDisclosure(false)
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

  async function removeCourse() {
    await deleteCourse(id)
    navigate('/courses')
  }

  return (
    <Stack>
      <Group justify="space-between" align="center">
        <Title order={1}>{course?.name}</Title>
        {course ? (
          <Group>
            <EditButton onClick={openEdit} />
            <DeleteButton name={course.name} onDelete={removeCourse} />
          </Group>
        ) : null}
      </Group>
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
      <EditCourseModal
        opened={editing}
        onClose={closeEdit}
        courseId={id}
        name={course?.name ?? ''}
      />
      <CreateModuleModal opened={opened} onClose={close} courseId={id} />
    </Stack>
  )
}
