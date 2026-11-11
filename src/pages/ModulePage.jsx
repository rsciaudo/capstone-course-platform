import { Button, Group, Loader, Menu, Stack, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { useNavigate, useParams } from 'react-router-dom'
import ContentCard from '../components/ContentCard.jsx'
import DeleteButton from '../components/DeleteButton.jsx'
import EditButton from '../components/EditButton.jsx'
import EditModuleModal from '../components/EditModuleModal.jsx'
import { contentLabel, useCourses } from '../courses/CoursesContext.jsx'

const contentTypes = ['quiz', 'file', 'slide']

export default function ModulePage() {
  const { id, moduleId } = useParams()
  const navigate = useNavigate()
  const { courses, loading, error, addContent, deleteModule } = useCourses()
  const [editing, { open, close }] = useDisclosure(false)
  const course = courses.find((item) => item.id === Number(id))
  const module = course?.modules.find((item) => item.id === Number(moduleId))
  const content = module?.content ?? []

  async function removeModule() {
    await deleteModule(id, moduleId)
    navigate(`/courses/${id}`)
  }

  return (
    <Stack>
      <Group justify="space-between" align="center">
        <Title order={1}>{module?.name}</Title>
        {module ? (
          <Group>
            <EditButton onClick={open} />
            <DeleteButton name={module.name} onDelete={removeModule} />
          </Group>
        ) : null}
      </Group>
      {loading ? <Loader /> : null}
      {error ? <Text c="red">{error}</Text> : null}
      <Menu>
        <Menu.Target>
          <Button w="fit-content">add course content</Button>
        </Menu.Target>
        <Menu.Dropdown>
          {contentTypes.map((type) => (
            <Menu.Item key={type} onClick={() => addContent(id, moduleId, type)}>
              {type}
            </Menu.Item>
          ))}
        </Menu.Dropdown>
      </Menu>
      <EditModuleModal
        opened={editing}
        onClose={close}
        courseId={id}
        moduleId={moduleId}
        name={module?.name ?? ''}
      />
      {content.map((item) => (
        <ContentCard
          key={item.number}
          courseId={id}
          moduleId={moduleId}
          contentNumber={item.number}
          label={contentLabel(content, item)}
        />
      ))}
    </Stack>
  )
}
