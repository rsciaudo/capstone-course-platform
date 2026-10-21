import { Title } from '@mantine/core'
import { useParams } from 'react-router-dom'

export default function UserDetailPage() {
  const { userNumber } = useParams()

  return <Title order={1}>user {userNumber}</Title>
}
