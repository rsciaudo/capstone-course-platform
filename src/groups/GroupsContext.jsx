import { createContext, useContext, useState } from 'react'

const GroupsContext = createContext(null)

export function GroupsProvider({ children }) {
  const [groups, setGroups] = useState([])

  function addGroup({ name }) {
    setGroups((current) => [
      ...current,
      { number: current.length + 1, name, users: [] },
    ])
  }

  function addUser(groupNumber, { name, role }) {
    setGroups((current) =>
      current.map((group) => {
        if (group.number !== Number(groupNumber)) {
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
              courseNumbers: [],
              editableCourseNumbers: [],
            },
          ],
        }
      }),
    )
  }

  function enrollUser(groupNumber, userNumber, courseNumber) {
    const selectedCourse = Number(courseNumber)

    setGroups((current) =>
      current.map((group) => {
        if (group.number !== Number(groupNumber)) {
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

            const courseNumbers = user.courseNumbers ?? []
            if (courseNumbers.includes(selectedCourse)) {
              return user
            }

            return {
              ...user,
              courseNumbers: [...courseNumbers, selectedCourse],
            }
          }),
        }
      }),
    )
  }

  function grantEditAccess(groupNumber, userNumber, courseNumber) {
    const selectedCourse = Number(courseNumber)

    setGroups((current) =>
      current.map((group) => {
        if (group.number !== Number(groupNumber)) {
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

            const editableCourseNumbers = user.editableCourseNumbers ?? []
            if (editableCourseNumbers.includes(selectedCourse)) {
              return user
            }

            return {
              ...user,
              editableCourseNumbers: [...editableCourseNumbers, selectedCourse],
            }
          }),
        }
      }),
    )
  }

  return (
    <GroupsContext.Provider
      value={{ groups, addGroup, addUser, enrollUser, grantEditAccess }}
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
