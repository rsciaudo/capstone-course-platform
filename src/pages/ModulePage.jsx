import { Button, Menu, Stack, Title } from '@mantine/core'
import { useParams } from 'react-router-dom'
import ContentCard from '../components/ContentCard.jsx'
import { contentLabel, useCourses } from '../courses/CoursesContext.jsx'

const contentTypes = ['quiz', 'file', 'slide']

export default function ModulePage() {
  const { number, moduleNumber } = useParams()
  const { courses, addContent } = useCourses()
  const course = courses.find((item) => item.number === Number(number))
  const module = course?.modules.find(
    (item) => item.number === Number(moduleNumber),
  )
  const content = module?.content ?? []

  return (
    <Stack>
      <Title order={1}>{module?.name}</Title>
      <Menu>
        <Menu.Target>
          <Button w="fit-content">add course content</Button>
        </Menu.Target>
        <Menu.Dropdown>
          {contentTypes.map((type) => (
            <Menu.Item
              key={type}
              onClick={() => addContent(number, moduleNumber, type)}
            >
              {type}
            </Menu.Item>
          ))}
        </Menu.Dropdown>
      </Menu>
      {content.map((item) => (
        <ContentCard
          key={item.number}
          courseNumber={number}
          moduleNumber={moduleNumber}
          contentNumber={item.number}
          label={contentLabel(content, item)}
        />
      ))}
    </Stack>
  )
}
