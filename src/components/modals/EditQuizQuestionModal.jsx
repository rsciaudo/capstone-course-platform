import { Button, Group, Modal, Stack } from '@mantine/core'
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
      key: choice.number,
      text: choice.text,
      correct: choice.correct,
    })),
  )

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
          save
        </Button>
      </Group>
    </Stack>
  )
}
