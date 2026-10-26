import { Button, Modal, Stack, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useParams } from 'react-router-dom'
import { useCourses } from '../courses/CoursesContext.jsx'
import { useGroups } from '../groups/GroupsContext.jsx'

export default function UserDetailPage() {
  const { number, userNumber } = useParams()
  const { courses } = useCourses()
  const { groups, enrollUser, grantEditAccess } = useGroups()
  const [opened, { open, close }] = useDisclosure(false)
  const group = groups.find((item) => item.number === Number(number))
  const user = group?.users.find((item) => item.number === Number(userNumber))
  const isEducator = user?.role === 'educator'
  const assignedNumbers = isEducator
    ? (user?.editableCourseNumbers ?? [])
    : (user?.courseNumbers ?? [])
  const availableCourses = courses.filter(
    (course) => !assignedNumbers.includes(course.number),
  )
  const actionLabel = isEducator ? 'give edit access' : 'enroll in course'

  function chooseCourse(courseNumber) {
    if (isEducator) {
      grantEditAccess(number, userNumber, courseNumber)
    } else {
      enrollUser(number, userNumber, courseNumber)
    }
    close()
  }

  return (
    <Stack>
      <Title order={1}>user {userNumber}</Title>
      {assignedNumbers.map((courseNumber) => {
        const course = courses.find((item) => item.number === courseNumber)
        return <Text key={courseNumber}>{course?.name}</Text>
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
                key={course.number}
                variant="default"
                onClick={() => chooseCourse(course.number)}
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
