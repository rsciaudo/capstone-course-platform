import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'
import { useUsers } from '../users/UsersContext.jsx'

const CoursesContext = createContext(null)

export function contentLabel(content, item) {
  const count = content.filter(
    (entry) => entry.type === item.type && entry.number <= item.number,
  ).length

  return `${item.type} ${count}`
}

function toModule(module) {
  return {
    id: module.id,
    name: module.name,
    position: module.position,
    content: [],
  }
}

function toCourse(course, modules) {
  return {
    id: course.id,
    name: course.name,
    groupId: course.group_id,
    modules: modules
      .filter((module) => module.course_id === course.id)
      .sort((left, right) => left.position - right.position)
      .map(toModule),
  }
}

export function CoursesProvider({ children }) {
  const { user } = useAuth()
  const { clearCourse } = useUsers()
  const userId = user?.id ?? null
  const [courses, setCourses] = useState([])
  const [loadedUserId, setLoadedUserId] = useState(null)
  const [error, setError] = useState(null)
  const loading = userId !== null && loadedUserId !== userId

  useEffect(() => {
    if (userId === null) {
      setCourses([])
      setError(null)
      setLoadedUserId(null)
      return
    }

    let active = true
    setError(null)

    Promise.all([api('/api/courses'), api('/api/modules')])
      .then(([courseRows, moduleRows]) => {
        if (!active) {
          return
        }
        setCourses(courseRows.map((course) => toCourse(course, moduleRows)))
      })
      .catch((err) => {
        if (!active) {
          return
        }
        setCourses([])
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

  async function createCourse({ name, groupId }) {
    const created = await api('/api/courses', {
      method: 'POST',
      body: { name, group_id: Number(groupId) },
    })
    const course = toCourse(created, [])
    setCourses((current) => [...current, course])
    return course
  }

  async function updateCourse(id, { name }) {
    const updated = await api(`/api/courses/${id}`, {
      method: 'PATCH',
      body: { name },
    })
    setCourses((current) =>
      current.map((course) =>
        course.id === updated.id ? { ...course, name: updated.name } : course,
      ),
    )
    return updated
  }

  async function deleteCourse(id) {
    await api(`/api/courses/${id}`, { method: 'DELETE' })
    const courseId = Number(id)
    setCourses((current) => current.filter((course) => course.id !== courseId))
    clearCourse(courseId)
  }

  async function updateModule(courseId, moduleId, { name }) {
    const updated = await api(`/api/modules/${moduleId}`, {
      method: 'PATCH',
      body: { name },
    })
    setCourses((current) =>
      current.map((course) => {
        if (course.id !== Number(courseId)) {
          return course
        }
        return {
          ...course,
          modules: course.modules.map((module) =>
            module.id === updated.id ? { ...module, name: updated.name } : module,
          ),
        }
      }),
    )
    return updated
  }

  async function deleteModule(courseId, moduleId) {
    await api(`/api/modules/${moduleId}`, { method: 'DELETE' })
    setCourses((current) =>
      current.map((course) => {
        if (course.id !== Number(courseId)) {
          return course
        }
        return {
          ...course,
          modules: course.modules.filter((module) => module.id !== Number(moduleId)),
        }
      }),
    )
  }

  async function addModule(courseId, { name }) {
    const selectedCourseId = Number(courseId)
    const course = courses.find((item) => item.id === selectedCourseId)
    const highest = (course?.modules ?? []).reduce(
      (max, module) => Math.max(max, module.position ?? 0),
      0,
    )
    const created = await api('/api/modules', {
      method: 'POST',
      body: {
        name,
        course_id: selectedCourseId,
        position: highest + 1,
      },
    })
    const module = toModule(created)
    setCourses((current) =>
      current.map((item) => {
        if (item.id !== selectedCourseId) {
          return item
        }
        return { ...item, modules: [...item.modules, module] }
      }),
    )
    return module
  }

  function addContent(courseId, moduleId, type) {
    setCourses((current) =>
      current.map((course) => {
        if (course.id !== Number(courseId)) {
          return course
        }

        return {
          ...course,
          modules: course.modules.map((module) => {
            if (module.id !== Number(moduleId)) {
              return module
            }

            const content = module.content ?? []
            return {
              ...module,
              content: [...content, { number: content.length + 1, type }],
            }
          }),
        }
      }),
    )
  }

  return (
    <CoursesContext.Provider
      value={{
        courses,
        loading,
        error,
        createCourse,
        updateCourse,
        deleteCourse,
        addModule,
        updateModule,
        deleteModule,
        addContent,
      }}
    >
      {children}
    </CoursesContext.Provider>
  )
}

export function useCourses() {
  const context = useContext(CoursesContext)
  if (!context) {
    throw new Error('useCourses must be used within CoursesProvider')
  }
  return context
}
