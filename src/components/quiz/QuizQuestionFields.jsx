import { Button, Checkbox, Group, Stack, Text, TextInput } from '@mantine/core'

export function emptyChoices() {
  return [1, 2, 3, 4].map((key) => ({
    key,
    text: '',
    correct: false,
  }))
}

export function questionIsValid(text, choices) {
  return (
    text.trim() !== '' &&
    choices.length >= 2 &&
    choices.every((choice) => choice.text.trim() !== '') &&
    choices.filter((choice) => choice.correct).length === 1
  )
}

export function toQuestionDraft(text, choices) {
  return {
    text: text.trim(),
    choices: choices.map((choice, index) => ({
      number: index + 1,
      text: choice.text.trim(),
      correct: choice.correct,
    })),
  }
}

export default function QuizQuestionFields({ text, choices, onTextChange, onChoicesChange }) {
  function setCorrect(key) {
    onChoicesChange(
      choices.map((choice) => ({
        ...choice,
        correct: choice.key === key,
      })),
    )
  }

  function updateChoice(key, value) {
    onChoicesChange(
      choices.map((choice) => (choice.key === key ? { ...choice, text: value } : choice)),
    )
  }

  function removeChoice(key) {
    onChoicesChange(choices.filter((choice) => choice.key !== key))
  }

  function addChoice() {
    const key = choices.reduce((max, choice) => Math.max(max, choice.key), 0) + 1
    onChoicesChange([...choices, { key, text: '', correct: false }])
  }

  return (
    <Stack>
      <TextInput
        label="question"
        value={text}
        onChange={(event) => onTextChange(event.currentTarget.value)}
      />
      <Text>answer choices</Text>
      {choices.map((choice, index) => (
        <Group key={choice.key} wrap="nowrap" align="center">
          <Checkbox
            checked={choice.correct}
            onChange={() => setCorrect(choice.key)}
            aria-label={`correct answer ${index + 1}`}
          />
          <TextInput
            flex={1}
            aria-label={`answer ${index + 1}`}
            placeholder="answer"
            value={choice.text}
            onChange={(event) => updateChoice(choice.key, event.currentTarget.value)}
          />
          <Button
            variant="subtle"
            color="red"
            px="xs"
            onClick={() => removeChoice(choice.key)}
            disabled={choices.length <= 2}
            aria-label={`remove answer ${index + 1}`}
          >
            -
          </Button>
        </Group>
      ))}
      <Button variant="default" w="fit-content" onClick={addChoice}>
        +
      </Button>
    </Stack>
  )
}
