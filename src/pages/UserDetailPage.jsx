import { Button, Modal, Stack, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useParams } from 'react-router-dom'
import { useCourses } from '../courses/CoursesContext.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

export default function UserDetailPage() {
  const { id, userNumber } = useParams()
  const { courses } = useCourses()
  const { groups, enrollUser, grantEditAccess } = useGroups()
  const [opened, { open, close }] = useDisclosure(false)
  const group = groups.find((item) => item.id === Number(id))
  const user = group?.users.find((item) => item.number === Number(userNumber))
  const isEducator = user?.role === 'educator'
  const assignedIds = isEducator
    ? (user?.editableCourseIds ?? [])
    : (user?.courseIds ?? [])
  const availableCourses = courses.filter((course) => !assignedIds.includes(course.id))
  const actionLabel = isEducator ? 'give edit access' : 'enroll in course'

  function chooseCourse(courseId) {
    if (isEducator) {
      grantEditAccess(id, userNumber, courseId)
    } else {
      enrollUser(id, userNumber, courseId)
    }
    close()
  }

  return (
    <Stack>
      <Title order={1}>user {userNumber}</Title>
      {assignedIds.map((courseId) => {
        const course = courses.find((item) => item.id === courseId)
        return <Text key={courseId}>{course?.name}</Text>
      })}
      <Button onClick={open} w="fit-content">
        {actionLabel}
      </Button>
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
