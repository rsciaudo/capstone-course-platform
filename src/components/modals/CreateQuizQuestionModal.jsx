import { Button, Group, Modal, Stack } from '@mantine/core'
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

  function submit() {
    onSubmit(toQuestionDraft(text, choices))
    onClose()
  }

  return (
    <Stack>
      <QuizQuestionFields
        text={text}
        choices={choices}
        onTextChange={setText}
        onChoicesChange={setChoices}
      />
      <Group>
        <Button variant="default" onClick={onClose}>
          cancel
        </Button>
        <Button onClick={submit} disabled={!questionIsValid(text, choices)}>
          add question
        </Button>
      </Group>
    </Stack>
  )
}
