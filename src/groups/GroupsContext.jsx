import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'

const GroupsContext = createContext(null)

function toGroup(group) {
  return {
    id: group.id,
    name: group.name,
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

  async function updateGroup(id, { name }) {
    const updated = await api(`/api/groups/${id}`, {
      method: 'PATCH',
      body: { name },
    })
    setGroups((current) =>
      current.map((group) =>
        group.id === updated.id ? { ...group, name: updated.name } : group,
      ),
    )
    return updated
  }

  async function deleteGroup(id) {
    await api(`/api/groups/${id}`, { method: 'DELETE' })
    setGroups((current) => current.filter((group) => group.id !== Number(id)))
  }

  return (
    <GroupsContext.Provider
      value={{
        groups,
        loading,
        error,
        addGroup,
        updateGroup,
        deleteGroup,
      }}
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
