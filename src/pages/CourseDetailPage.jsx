import { Button, Group, Loader, Stack, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useNavigate, useParams } from 'react-router-dom'
import DeleteButton from '../components/buttons/DeleteButton.jsx'
import EditButton from '../components/buttons/EditButton.jsx'
import ModuleCard from '../components/cards/ModuleCard.jsx'
import UserCard from '../components/cards/UserCard.jsx'
import CreateModuleModal from '../components/modals/CreateModuleModal.jsx'
import EditCourseModal from '../components/modals/EditCourseModal.jsx'
import { useAuth } from '../auth/AuthContext.jsx'
import { useCourses } from '../courses/CoursesContext.jsx'
import { useUsers } from '../users/UsersContext.jsx'

export default function CoursePage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user: currentUser } = useAuth()
  const { courses, loading, error, deleteCourse } = useCourses()
  const { users, unenrollUser, removeEditAccess } = useUsers()
  const [opened, { open, close }] = useDisclosure(false)
  const [editing, { open: openEdit, close: closeEdit }] = useDisclosure(false)
  const courseId = Number(id)
  const course = courses.find((item) => item.id === courseId)
  const modules = course?.modules ?? []
  const enrolledUsers = users.filter((user) =>
    (user.courseIds ?? []).includes(courseId),
  )
  const editors = users.filter((user) =>
    (user.editableCourseIds ?? []).includes(courseId),
  )
  const currentRecord = users.find((user) => user.id === currentUser?.id)
  const canManage =
    currentUser?.role === 'super-user' ||
    currentUser?.role === 'admin' ||
    (currentRecord?.editableCourseIds ?? []).includes(courseId)

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

      <Group justify="space-between"> 
        <Title order={2}>modules</Title>
        <Button onClick={open} w="fit-content">
          add module
        </Button>
      </Group>
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
          key={user.id}
          groupId={user.groupId}
          userId={user.id}
          name={user.name}
          role={user.role}
          courseName={course?.name ?? ''}
          removeLabel={canManage ? 'unenroll' : undefined}
          onRemove={() => unenrollUser(user.id, courseId)}
        />
      ))}
      <Title order={2}>editors</Title>
      {editors.map((user) => (
        <UserCard
          key={user.id}
          groupId={user.groupId}
          userId={user.id}
          name={user.name}
          role={user.role}
          courseName={course?.name ?? ''}
          removeLabel={canManage ? 'remove edit access' : undefined}
          onRemove={() => removeEditAccess(user.id, courseId)}
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
