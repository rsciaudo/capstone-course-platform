import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

const GroupsContext = createContext(null)

function toGroup(group) {
  return {
    id: group.id,
    name: group.name,
    users: [],
  }
}

export function GroupsProvider({ children }) {
  const { user } = useAuth()
  const userId = user?.id ?? null
  const [groups, setGroups] = useState([])
  const [loadedUserId, setLoadedUserId] = useState(null)
  const [error, setError] = useState(null)
  const loading = userId !== null && loadedUserId !== userId

  useEffect(() => {
    if (userId === null) {
      setGroups([])
      setError(null)
      setLoadedUserId(null)
      return
    }

    let active = true
    setError(null)

    api('/api/groups')
      .then((rows) => {
        if (!active) {
          return
        }
        setGroups(rows.map(toGroup))
      })
      .catch((err) => {
        if (!active) {
          return
        }
        setGroups([])
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

  async function addGroup({ name }) {
    const created = await api('/api/groups', {
      method: 'POST',
      body: { name },
    })
    const group = toGroup(created)
    setGroups((current) => [...current, group])
    return group
  }

  function addUser(groupId, { name, role }) {
    setGroups((current) =>
      current.map((group) => {
        if (group.id !== Number(groupId)) {
          return group
        }

        return {
          ...group,
          users: [
            ...group.users,
            {
              number: group.users.length + 1,
              name,
              role,
              courseIds: [],
              editableCourseIds: [],
            },
          ],
        }
      }),
    )
  }

  function enrollUser(groupId, userNumber, courseId) {
    const selectedCourse = Number(courseId)

    setGroups((current) =>
      current.map((group) => {
        if (group.id !== Number(groupId)) {
          return group
        }

        return {
          ...group,
          users: group.users.map((user) => {
            if (user.number !== Number(userNumber)) {
              return user
            }

            if (user.role !== 'student') {
              return user
            }

            const courseIds = user.courseIds ?? []
            if (courseIds.includes(selectedCourse)) {
              return user
            }

            return {
              ...user,
              courseIds: [...courseIds, selectedCourse],
            }
          }),
        }
      }),
    )
  }

  function grantEditAccess(groupId, userNumber, courseId) {
    const selectedCourse = Number(courseId)

    setGroups((current) =>
      current.map((group) => {
        if (group.id !== Number(groupId)) {
          return group
        }

        return {
          ...group,
          users: group.users.map((user) => {
            if (user.number !== Number(userNumber)) {
              return user
            }

            if (user.role !== 'educator') {
              return user
            }

            const editableCourseIds = user.editableCourseIds ?? []
            if (editableCourseIds.includes(selectedCourse)) {
              return user
            }

            return {
              ...user,
              editableCourseIds: [...editableCourseIds, selectedCourse],
            }
          }),
        }
      }),
    )
  }

  return (
    <GroupsContext.Provider
      value={{ groups, loading, error, addGroup, addUser, enrollUser, grantEditAccess }}
    >
      {children}
    </GroupsContext.Provider>
  )
}

export function useGroups() {
  const context = useContext(GroupsContext)
  if (!context) {
    throw new Error('useGroups must be used within GroupsProvider')
  }
  return context
}
