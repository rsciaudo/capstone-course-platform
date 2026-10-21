import { createContext, useContext, useState } from 'react'

const GroupsContext = createContext(null)

export function GroupsProvider({ children }) {
  const [groups, setGroups] = useState([])

  function addGroup() {
    setGroups((current) => [
      ...current,
      { number: current.length + 1, users: [] },
    ])
  }

  function addUser(groupNumber) {
    setGroups((current) =>
      current.map((group) => {
        if (group.number !== Number(groupNumber)) {
          return group
        }

        return {
          ...group,
          users: [...group.users, { number: group.users.length + 1 }],
        }
      }),
    )
  }

  return (
    <GroupsContext.Provider value={{ groups, addGroup, addUser }}>
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
