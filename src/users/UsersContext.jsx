import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

const UsersContext = createContext(null)

function toUser(user) {
  return {
    id: user.id,
    name: user.name,
    username: user.username,
    role: user.role,
    groupId: user.group_id,
    courseIds: [],
    editableCourseIds: [],
  }
}

export function UsersProvider({ children }) {
  const { user } = useAuth()
  const userId = user?.id ?? null
  const [users, setUsers] = useState([])
  const [loadedUserId, setLoadedUserId] = useState(null)
  const [error, setError] = useState(null)
  const loading = userId !== null && loadedUserId !== userId

  useEffect(() => {
    if (userId === null) {
      setUsers([])
      setError(null)
      setLoadedUserId(null)
      return
    }

    let active = true
    setError(null)

    api('/api/users')
      .then((rows) => {
        if (!active) {
          return
        }
        setUsers(rows.map(toUser))
      })
      .catch((err) => {
        if (!active) {
          return
        }
        setUsers([])
        setError(err instanceof Error ? err.message : 'Request failed')
      })
      .finally(() => {
        if (active) {
          setLoadedUserId(userId)
        }
      })

    return () => {
      active = false
    }
  }, [userId])

  async function addUser({ name, username, password, role, groupId }) {
    const created = await api('/api/users', {
      method: 'POST',
      body: {
        name,
        username,
        password,
        role,
        group_id: Number(groupId),
      },
    })
    const next = toUser(created)
    setUsers((current) => [...current, next])
    return next
  }

  function clearCourse(courseId) {
    const selected = Number(courseId)
    setUsers((current) =>
      current.map((item) => ({
        ...item,
        courseIds: (item.courseIds ?? []).filter((id) => id !== selected),
        editableCourseIds: (item.editableCourseIds ?? []).filter(
          (id) => id !== selected,
        ),
      })),
    )
  }

  function enrollUser(userIdToEnroll, courseId) {
    const selectedUser = Number(userIdToEnroll)
    const selectedCourse = Number(courseId)

    setUsers((current) =>
      current.map((item) => {
        if (item.id !== selectedUser || item.role !== 'student') {
          return item
        }

        const courseIds = item.courseIds ?? []
        if (courseIds.includes(selectedCourse)) {
          return item
        }

        return {
          ...item,
          courseIds: [...courseIds, selectedCourse],
        }
      }),
    )
  }

  function grantEditAccess(userIdToGrant, courseId) {
    const selectedUser = Number(userIdToGrant)
    const selectedCourse = Number(courseId)

    setUsers((current) =>
      current.map((item) => {
        if (item.id !== selectedUser || item.role !== 'educator') {
          return item
        }

        const editableCourseIds = item.editableCourseIds ?? []
        if (editableCourseIds.includes(selectedCourse)) {
          return item
        }

        return {
          ...item,
          editableCourseIds: [...editableCourseIds, selectedCourse],
        }
      }),
    )
  }

  return (
    <UsersContext.Provider
      value={{
        users,
        loading,
        error,
        addUser,
        clearCourse,
        enrollUser,
        grantEditAccess,
      }}
    >
      {children}
    </UsersContext.Provider>
  )
}

export function useUsers() {
  const context = useContext(UsersContext)
  if (!context) {
    throw new Error('useUsers must be used within UsersProvider')
  }
  return context
}
