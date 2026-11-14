import { Card, Group, Stack, Text } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import DeleteButton from '../buttons/DeleteButton.jsx'
import EditButton from '../buttons/EditButton.jsx'
import EditQuizQuestionModal from '../modals/EditQuizQuestionModal.jsx'

export default function QuizQuestionCard({ question, onSave, onDelete }) {
  const [editing, { open, close }] = useDisclosure(false)

  return (
    <>
      <Card withBorder>
        <Stack>
          <Group justify="space-between" align="flex-start" wrap="nowrap">
            <Text>{question.text}</Text>
            <Group wrap="nowrap">
              <EditButton onClick={open} />
              <DeleteButton name={question.text} onDelete={onDelete} />
            </Group>
          </Group>
          {question.choices.map((choice) => (
            <Group key={choice.number} justify="space-between" wrap="nowrap">
              <Text>{choice.text}</Text>
              {choice.correct ? <Text aria-label="correct answer">✓</Text> : null}
            </Group>
          ))}
        </Stack>
      </Card>
      <EditQuizQuestionModal
        opened={editing}
        onClose={close}
        question={question}
        onSubmit={onSave}
      />
    </>
  )
}
