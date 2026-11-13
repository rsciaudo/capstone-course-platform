import { Button, Group, Loader, Modal, Stack, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useCourses } from '../courses/CoursesContext.jsx'
import { useUsers } from '../users/UsersContext.jsx'
import CourseCard from '../components/cards/CourseCard.jsx'

export default function UserDetailPage() {
  const { id, userId } = useParams()
  const { courses } = useCourses()
  const { users, loading, error, enrollUser, grantEditAccess } = useUsers()
  const [opened, { open, close }] = useDisclosure(false)
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const user = users.find(
    (item) => item.id === Number(userId) && item.groupId === Number(id),
  )
  const isEducator = user?.role === 'educator'
  const assignedIds = isEducator
    ? (user?.editableCourseIds ?? [])
    : (user?.courseIds ?? [])
  const availableCourses = courses.filter(
    (course) =>
      course.groupId === user?.groupId && !assignedIds.includes(course.id),
  )
  const actionLabel = isEducator ? 'give edit access' : 'enroll in course'

  function openModal() {
    setFormError('')
    open()
  }

  async function chooseCourse(courseId) {
    if (!user || submitting) {
      return
    }
    setFormError('')
    setSubmitting(true)
    try {
      if (isEducator) {
        await grantEditAccess(user.id, courseId)
      } else {
        await enrollUser(user.id, courseId)
      }
      close()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Stack>
      <Title order={1}>{user?.name}</Title>
      {loading ? <Loader /> : null}
      {error ? <Text c="red">{error}</Text> : null}
      <Group justify = "space-between">
        <Title order={2}>courses</Title>
        {user ? (
          <Button onClick={openModal} w="fit-content">
            {actionLabel}
          </Button>
        ) : null}
      </Group>
      {user
        ? assignedIds.map((courseId) => {
            const course = courses.find((item) => item.id === courseId)
            return <CourseCard key={course.id} id={course.id} name={course.name} />
          })
        : null}

      <Modal opened={opened} onClose={close} title={actionLabel}>
        <Stack>
          {availableCourses.length === 0 ? (
            <Text>there are no courses available</Text>
          ) : (
            availableCourses.map((course) => (
              <Button
                key={course.id}
                variant="default"
                disabled={submitting}
                onClick={() => chooseCourse(course.id)}
              >
                {course.name}
              </Button>
            ))
          )}
          {formError ? <Text c="red">{formError}</Text> : null}
        </Stack>
      </Modal>
    </Stack>
  )
}
