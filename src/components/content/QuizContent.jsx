import { Button, Group, Stack, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import QuizQuestionCard from '../cards/QuizQuestionCard.jsx'
import CreateQuizQuestionModal from '../modals/CreateQuizQuestionModal.jsx'
import { useCourses } from '../../courses/CoursesContext.jsx'

export default function QuizContent({ courseId, moduleId, contentNumber, questions }) {
  const { updateContent } = useCourses()
  const [creating, { open, close }] = useDisclosure(false)
  const list = questions ?? []

  function save(next) {
    updateContent(courseId, moduleId, contentNumber, { questions: next })
  }

  function addQuestion(draft) {
    const number = list.reduce((max, question) => Math.max(max, question.number ?? 0), 0) + 1
    save([...list, { number, ...draft }])
  }

  function updateQuestion(number, draft) {
    save(list.map((question) => (question.number === number ? { number, ...draft } : question)))
  }

  function deleteQuestion(number) {
    save(list.filter((question) => question.number !== number))
  }

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
          key={question.number}
          question={question}
          onSave={(draft) => updateQuestion(question.number, draft)}
          onDelete={() => deleteQuestion(question.number)}
        />
      ))}
      <CreateQuizQuestionModal opened={creating} onClose={close} onSubmit={addQuestion} />
    </Stack>
  )
}
