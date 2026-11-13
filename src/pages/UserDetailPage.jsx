import { Button, Loader, Modal, Stack, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useParams } from 'react-router-dom'
import { useCourses } from '../courses/CoursesContext.jsx'
import { useUsers } from '../users/UsersContext.jsx'

export default function UserDetailPage() {
  const { id, userId } = useParams()
  const { courses } = useCourses()
  const { users, loading, error, enrollUser, grantEditAccess } = useUsers()
  const [opened, { open, close }] = useDisclosure(false)
  const user = users.find(
    (item) => item.id === Number(userId) && item.groupId === Number(id),
  )
  const isEducator = user?.role === 'educator'
  const assignedIds = isEducator
    ? (user?.editableCourseIds ?? [])
    : (user?.courseIds ?? [])
  const availableCourses = courses.filter((course) => !assignedIds.includes(course.id))
  const actionLabel = isEducator ? 'give edit access' : 'enroll in course'

  function chooseCourse(courseId) {
    if (!user) {
      return
    }
    if (isEducator) {
      grantEditAccess(user.id, courseId)
    } else {
      enrollUser(user.id, courseId)
    }
    close()
  }

  return (
    <Stack>
      <Title order={1}>{user?.name}</Title>
      {loading ? <Loader /> : null}
      {error ? <Text c="red">{error}</Text> : null}
      {user
        ? assignedIds.map((courseId) => {
            const course = courses.find((item) => item.id === courseId)
            return <Text key={courseId}>{course?.name}</Text>
          })
        : null}
      {user ? (
        <Button onClick={open} w="fit-content">
          {actionLabel}
        </Button>
      ) : null}
      <Modal opened={opened} onClose={close} title={actionLabel}>
        {availableCourses.length === 0 ? (
          <Text>there are no courses available</Text>
        ) : (
          <Stack>
            {availableCourses.map((course) => (
              <Button
                key={course.id}
                variant="default"
                onClick={() => chooseCourse(course.id)}
              >
                {course.name}
              </Button>
            ))}
          </Stack>
        )}
      </Modal>
    </Stack>
  )
}
