import { Button, Loader, Menu, Stack, Text, Title } from '@mantine/core'
import { useParams } from 'react-router-dom'
import ContentCard from '../components/ContentCard.jsx'
import { contentLabel, useCourses } from '../courses/CoursesContext.jsx'

const contentTypes = ['quiz', 'file', 'slide']

export default function ModulePage() {
  const { id, moduleId } = useParams()
  const { courses, loading, error, addContent } = useCourses()
  const course = courses.find((item) => item.id === Number(id))
  const module = course?.modules.find((item) => item.id === Number(moduleId))
  const content = module?.content ?? []

  return (
    <Stack>
      <Title order={1}>{module?.name}</Title>
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
