import { Button, Group, Modal, Stack, Text } from '@mantine/core'
import { useState } from 'react'
import QuizQuestionFields, {
  questionIsValid,
  toQuestionDraft,
} from '../quiz/QuizQuestionFields.jsx'

export default function EditQuizQuestionModal({ opened, onClose, question, onSubmit }) {
  return (
    <Modal opened={opened} onClose={onClose} title="edit question" size="lg">
      {opened ? (
        <EditQuizQuestionForm onClose={onClose} question={question} onSubmit={onSubmit} />
      ) : null}
    </Modal>
  )
}

function EditQuizQuestionForm({ onClose, question, onSubmit }) {
  const [text, setText] = useState(question.text)
  const [choices, setChoices] = useState(
    question.choices.map((choice) => ({
      key: choice.id,
      id: choice.id,
      text: choice.text,
      correct: choice.correct,
    })),
  )
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submit() {
    setError('')
    setSubmitting(true)
    try {
      await onSubmit(toQuestionDraft(text, choices))
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
      setSubmitting(false)
    }
  }

  return (
    <Stack>
      <QuizQuestionFields
        text={text}
        choices={choices}
        onTextChange={setText}
        onChoicesChange={setChoices}
      />
      {error ? <Text c="red">{error}</Text> : null}
      <Group>
        <Button variant="default" onClick={onClose}>
          cancel
        </Button>
        <Button onClick={submit} loading={submitting} disabled={!questionIsValid(text, choices)}>
          save
        </Button>
      </Group>
    </Stack>
  )
}
