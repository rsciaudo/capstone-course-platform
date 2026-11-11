import { Button } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import ConfirmDeleteModal from './ConfirmDeleteModal.jsx'

export default function DeleteButton({ name, onDelete }) {
  const [opened, { open, close }] = useDisclosure(false)

  return (
    <>
      <Button color="red" variant="light" onClick={open}>
        delete
      </Button>
      <ConfirmDeleteModal
        opened={opened}
        onClose={close}
        name={name}
        onConfirm={onDelete}
      />
    </>
  )
}
