import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

const UsersContext = createContext(null)

function rowsFor(rows, userId) {
  return rows.filter((row) => row.user_id === userId)
}

function courseIdsFor(rows) {
  return rows.map((row) => row.course_id)
}

function idsByCourse(rows) {
  return Object.fromEntries(rows.map((row) => [row.course_id, row.id]))
}

function withoutCourse(ids, courseId) {
  const next = { ...(ids ?? {}) }
  delete next[courseId]
  return next
}

function toUser(user, enrollments = [], editGrants = []) {
  const enrollmentRows = rowsFor(enrollments, user.id)
  const grantRows = rowsFor(editGrants, user.id)
  return {
    id: user.id,
    name: user.name,
    username: user.username,
    role: user.role,
    groupId: user.group_id,
    courseIds: courseIdsFor(enrollmentRows),
    editableCourseIds: courseIdsFor(grantRows),
    enrollmentIds: idsByCourse(enrollmentRows),
    editGrantIds: idsByCourse(grantRows),
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

    Promise.all([api('/api/users'), api('/api/enrollments'), api('/api/edit-grants')])
      .then(([userRows, enrollmentRows, grantRows]) => {
        if (!active) {
          return
        }
        setUsers(
          userRows.map((user) => toUser(user, enrollmentRows, grantRows)),
        )
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

  async function updateUser(id, { name, role, groupId }) {
    const updated = await api(`/api/users/${id}`, {
      method: 'PATCH',
      body: {
        name,
        role,
        group_id: Number(groupId),
      },
    })
    setUsers((current) =>
      current.map((item) =>
        item.id === updated.id
          ? {
              ...item,
              name: updated.name,
              role: updated.role,
              groupId: updated.group_id,
            }
          : item,
      ),
    )
    return updated
  }

  async function deleteUser(id) {
    await api(`/api/users/${id}`, { method: 'DELETE' })
    setUsers((current) => current.filter((item) => item.id !== Number(id)))
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
        enrollmentIds: withoutCourse(item.enrollmentIds, selected),
        editGrantIds: withoutCourse(item.editGrantIds, selected),
      })),
    )
  }

  async function enrollUser(userIdToEnroll, courseId) {
    const selectedUser = Number(userIdToEnroll)
    const selectedCourse = Number(courseId)
    const existing = users.find((item) => item.id === selectedUser)
    if (
      !existing ||
      existing.role !== 'student' ||
      (existing.courseIds ?? []).includes(selectedCourse)
    ) {
      return
    }

    const created = await api('/api/enrollments', {
      method: 'POST',
      body: { user_id: selectedUser, course_id: selectedCourse },
    })
    setUsers((current) =>
      current.map((item) => {
        if (item.id !== selectedUser) {
          return item
        }
        return {
          ...item,
          courseIds: [...(item.courseIds ?? []), selectedCourse],
          enrollmentIds: {
            ...(item.enrollmentIds ?? {}),
            [selectedCourse]: created.id,
          },
        }
      }),
    )
  }

  async function unenrollUser(userIdToRemove, courseId) {
    const selectedUser = Number(userIdToRemove)
    const selectedCourse = Number(courseId)
    const existing = users.find((item) => item.id === selectedUser)
    const enrollmentId = existing?.enrollmentIds?.[selectedCourse]
    if (!enrollmentId) {
      throw new Error('Enrollment not found')
    }

    await api(`/api/enrollments/${enrollmentId}`, { method: 'DELETE' })
    setUsers((current) =>
      current.map((item) => {
        if (item.id !== selectedUser) {
          return item
        }
        return {
          ...item,
          courseIds: (item.courseIds ?? []).filter((id) => id !== selectedCourse),
          enrollmentIds: withoutCourse(item.enrollmentIds, selectedCourse),
        }
      }),
    )
  }

  async function grantEditAccess(userIdToGrant, courseId) {
    const selectedUser = Number(userIdToGrant)
    const selectedCourse = Number(courseId)
    const existing = users.find((item) => item.id === selectedUser)
    if (
      !existing ||
      existing.role !== 'educator' ||
      (existing.editableCourseIds ?? []).includes(selectedCourse)
    ) {
      return
    }

    const created = await api('/api/edit-grants', {
      method: 'POST',
      body: { user_id: selectedUser, course_id: selectedCourse },
    })
    setUsers((current) =>
      current.map((item) => {
        if (item.id !== selectedUser) {
          return item
        }
        return {
          ...item,
          editableCourseIds: [...(item.editableCourseIds ?? []), selectedCourse],
          editGrantIds: {
            ...(item.editGrantIds ?? {}),
            [selectedCourse]: created.id,
          },
        }
      }),
    )
  }

  async function removeEditAccess(userIdToRemove, courseId) {
    const selectedUser = Number(userIdToRemove)
    const selectedCourse = Number(courseId)
    const existing = users.find((item) => item.id === selectedUser)
    const grantId = existing?.editGrantIds?.[selectedCourse]
    if (!grantId) {
      throw new Error('Edit grant not found')
    }

    await api(`/api/edit-grants/${grantId}`, { method: 'DELETE' })
    setUsers((current) =>
      current.map((item) => {
        if (item.id !== selectedUser) {
          return item
        }
        return {
          ...item,
          editableCourseIds: (item.editableCourseIds ?? []).filter(
            (id) => id !== selectedCourse,
          ),
          editGrantIds: withoutCourse(item.editGrantIds, selectedCourse),
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
        updateUser,
        deleteUser,
        clearCourse,
        enrollUser,
        unenrollUser,
        grantEditAccess,
        removeEditAccess,
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
