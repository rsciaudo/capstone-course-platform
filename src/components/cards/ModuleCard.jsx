import { Card, Group, Text } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { Link } from 'react-router-dom'
import { useCourses } from '../../courses/CoursesContext.jsx'
import DeleteButton from '../buttons/DeleteButton.jsx'
import EditButton from '../buttons/EditButton.jsx'
import EditModuleModal from '../modals/EditModuleModal.jsx'

export default function ModuleCard({ courseId, moduleId, name }) {
  const { deleteModule } = useCourses()
  const [editing, { open, close }] = useDisclosure(false)

  return (
    <>
      <Card withBorder flex={1}>
        <Group wrap="nowrap">
          <Card
            component={Link}
            to={`/courses/${courseId}/modules/${moduleId}`}
            padding="md"
            flex={1}
          >
            <Text>{name}</Text>
          </Card>
          <EditButton onClick={open} />
          <DeleteButton name={name} onDelete={() => deleteModule(courseId, moduleId)} />
        </Group>
      </Card>
      <EditModuleModal
        opened={editing}
        onClose={close}
        courseId={courseId}
        moduleId={moduleId}
        name={name}
      />
    </>
  )
}
