import { Button, Group, Modal, Stack, Text } from '@mantine/core'
import { useState } from 'react'
import QuizQuestionFields, {
  emptyChoices,
  questionIsValid,
  toQuestionDraft,
} from '../quiz/QuizQuestionFields.jsx'

export default function CreateQuizQuestionModal({ opened, onClose, onSubmit }) {
  return (
    <Modal opened={opened} onClose={onClose} title="add question" size="lg">
      {opened ? <CreateQuizQuestionForm onClose={onClose} onSubmit={onSubmit} /> : null}
    </Modal>
  )
}

function CreateQuizQuestionForm({ onClose, onSubmit }) {
  const [text, setText] = useState('')
  const [choices, setChoices] = useState(emptyChoices)
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
        <Button
          onClick={submit}
          loading={submitting}
          disabled={!questionIsValid(text, choices)}
        >
          add question
        </Button>
      </Group>
    </Stack>
  )
}
