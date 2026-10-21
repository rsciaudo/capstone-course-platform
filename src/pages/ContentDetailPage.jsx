import { Stack, Title } from '@mantine/core'
import { useParams } from 'react-router-dom'
import FileContent from '../components/content/FileContent.jsx'
import QuizContent from '../components/content/QuizContent.jsx'
import SlideContent from '../components/content/SlideContent.jsx'
import { contentLabel, useCourses } from '../courses/CoursesContext.jsx'

const contentComponents = {
  quiz: QuizContent,
  file: FileContent,
  slide: SlideContent,
}

export default function ContentDetailPage() {
  const { number, moduleNumber, contentNumber } = useParams()
  const { courses } = useCourses()
  const course = courses.find((item) => item.number === Number(number))
  const module = course?.modules.find(
    (item) => item.number === Number(moduleNumber),
  )
  const content = module?.content ?? []
  const item = content.find((entry) => entry.number === Number(contentNumber))

  if (!item) {
    return null
  }

  const Content = contentComponents[item.type]

  return (
    <Stack>
      <Title order={1}>{contentLabel(content, item)}</Title>
      <Content />
    </Stack>
  )
}
