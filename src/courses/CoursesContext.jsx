import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'
import { useUsers } from '../users/UsersContext.jsx'

const CoursesContext = createContext(null)

export function contentLabel(content, item) {
  if (item.name) {
    return item.name
  }

  const count = content.filter(
    (entry) => entry.type === item.type && entry.number <= item.number,
  ).length

  return `${item.type} ${count}`
}

function revokeFileUrl(item) {
  if (item?.fileUrl) {
    URL.revokeObjectURL(item.fileUrl)
  }
}

function moduleContent(courses, courseId, moduleId) {
  const course = courses.find((item) => item.id === Number(courseId))
  const module = course?.modules.find((item) => item.id === Number(moduleId))
  return module?.content ?? []
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
    const course = courses.find((item) => item.id === courseId)
    for (const module of course?.modules ?? []) {
      for (const item of module.content ?? []) {
        revokeFileUrl(item)
      }
    }
    setCourses((current) => current.filter((item) => item.id !== courseId))
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
    for (const item of moduleContent(courses, courseId, moduleId)) {
      revokeFileUrl(item)
    }
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

  function addContent(courseId, moduleId, { type, name, fileUrl, fileName }) {
    const selectedCourseId = Number(courseId)
    const selectedModuleId = Number(moduleId)
    const content = moduleContent(courses, selectedCourseId, selectedModuleId)
    const number =
      content.reduce((max, item) => Math.max(max, item.number ?? 0), 0) + 1
    const created = { number, type }
    if (name != null) {
      created.name = name
    }
    if (fileUrl != null) {
      created.fileUrl = fileUrl
    }
    if (fileName != null) {
      created.fileName = fileName
    }

    setCourses((current) =>
      current.map((course) => {
        if (course.id !== selectedCourseId) {
          return course
        }

        return {
          ...course,
          modules: course.modules.map((module) => {
            if (module.id !== selectedModuleId) {
              return module
            }

            return {
              ...module,
              content: [...(module.content ?? []), created],
            }
          }),
        }
      }),
    )
    return created
  }

  function updateContent(courseId, moduleId, number, patch) {
    const current = moduleContent(courses, courseId, moduleId).find(
      (item) => item.number === Number(number),
    )
    if (patch.fileUrl && current?.fileUrl && patch.fileUrl !== current.fileUrl) {
      URL.revokeObjectURL(current.fileUrl)
    }

    setCourses((list) =>
      list.map((course) => {
        if (course.id !== Number(courseId)) {
          return course
        }

        return {
          ...course,
          modules: course.modules.map((module) => {
            if (module.id !== Number(moduleId)) {
              return module
            }

            return {
              ...module,
              content: (module.content ?? []).map((item) =>
                item.number === Number(number) ? { ...item, ...patch } : item,
              ),
            }
          }),
        }
      }),
    )
  }

  function deleteContent(courseId, moduleId, number) {
    const current = moduleContent(courses, courseId, moduleId).find(
      (item) => item.number === Number(number),
    )
    revokeFileUrl(current)

    setCourses((list) =>
      list.map((course) => {
        if (course.id !== Number(courseId)) {
          return course
        }

        return {
          ...course,
          modules: course.modules.map((module) => {
            if (module.id !== Number(moduleId)) {
              return module
            }

            return {
              ...module,
              content: (module.content ?? []).filter(
                (item) => item.number !== Number(number),
              ),
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
        updateContent,
        deleteContent,
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
