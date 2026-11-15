import { Button, Group, Stack, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import QuizQuestionCard from '../cards/QuizQuestionCard.jsx'
import CreateQuizQuestionModal from '../modals/CreateQuizQuestionModal.jsx'
import { useCourses } from '../../courses/CoursesContext.jsx'

export default function QuizContent({ courseId, moduleId, contentId, questions }) {
  const { addQuestion, saveQuestion, deleteQuestion } = useCourses()
  const [creating, { open, close }] = useDisclosure(false)
  const list = questions ?? []

  return (
    <Stack>
      <Group justify="space-between" align="center">
        <Title order={2}>Questions</Title>
        <Button onClick={open} w="fit-content">
          add question
        </Button>
      </Group>
      {list.map((question) => (
        <QuizQuestionCard
          key={question.id}
          question={question}
          onSave={(draft) => saveQuestion(courseId, moduleId, contentId, question.id, draft)}
          onDelete={() => deleteQuestion(courseId, moduleId, contentId, question.id)}
        />
      ))}
      <CreateQuizQuestionModal
        opened={creating}
        onClose={close}
        onSubmit={(draft) => addQuestion(courseId, moduleId, contentId, draft)}
      />
    </Stack>
  )
}
