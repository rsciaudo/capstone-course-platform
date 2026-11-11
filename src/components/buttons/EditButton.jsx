import { Button } from '@mantine/core'

export default function EditButton({ onClick }) {
  return (
    <Button variant="default" onClick={onClick}>
      edit
    </Button>
  )
}
