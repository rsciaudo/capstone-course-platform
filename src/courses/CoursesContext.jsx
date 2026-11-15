import { createContext, useContext, useEffect, useState } from 'react'
import { api, apiForm } from '../api/client.js'
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

function moduleContent(courses, courseId, moduleId) {
  const course = courses.find((item) => item.id === Number(courseId))
  const module = course?.modules.find((item) => item.id === Number(moduleId))
  return module?.content ?? []
}

function nextPosition(content) {
  return content.reduce((max, item) => Math.max(max, item.position ?? 0), 0) + 1
}

function sameId(item, contentId) {
  return String(item.id) === String(contentId)
}

function withModuleContent(courses, courseId, moduleId, update) {
  return courses.map((course) => {
    if (course.id !== Number(courseId)) {
      return course
    }
    return {
      ...course,
      modules: course.modules.map((module) => {
        if (module.id !== Number(moduleId)) {
          return module
        }
        return { ...module, content: update(module.content ?? []) }
      }),
    }
  })
}

function placeContent(content, item) {
  const next = content.some((entry) => sameId(entry, item.id))
    ? content.map((entry) => (sameId(entry, item.id) ? item : entry))
    : [...content, item]
  return next.sort((left, right) => left.position - right.position)
}

function toChoice(choice) {
  return {
    id: choice.id,
    text: choice.text,
    position: choice.position,
    correct: choice.is_correct,
  }
}

function toQuestion(question) {
  return {
    id: question.id,
    text: question.text,
    position: question.position,
    choices: (question.choices ?? [])
      .map(toChoice)
      .sort((left, right) => left.position - right.position),
  }
}

function toContent(row) {
  const item = {
    id: row.id,
    type: row.type,
    name: row.title,
    position: row.position,
  }
  if (row.type === 'file') {
    item.fileName = row.filename
    item.contentType = row.content_type
    item.fileUrl = `/api/files/${row.id}`
  }
  if (row.type === 'slide') {
    item.slideData = row.slide_data
  }
  if (row.type === 'quiz') {
    item.questions = (row.questions ?? [])
      .map(toQuestion)
      .sort((left, right) => left.position - right.position)
  }
  return item
}

function toModule(module) {
  return {
    id: module.id,
    name: module.name,
    position: module.position,
    content: [],
  }
}

function toCourse(course, modules, contentRows = []) {
  return {
    id: course.id,
    name: course.name,
    groupId: course.group_id,
    modules: modules
      .filter((module) => module.course_id === course.id)
      .sort((left, right) => left.position - right.position)
      .map((module) => ({
        ...toModule(module),
        content: contentRows
          .filter((row) => row.module_id === module.id)
          .map(toContent)
          .sort((left, right) => left.position - right.position),
      })),
  }
}

function findQuiz(courses, courseId, moduleId, contentId) {
  return moduleContent(courses, courseId, moduleId).find((item) => sameId(item, contentId))
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

    Promise.all([api('/api/courses'), api('/api/modules'), api('/api/content')])
      .then(([courseRows, moduleRows, contentRows]) => {
        if (!active) {
          return
        }
        setCourses(
          courseRows.map((course) => toCourse(course, moduleRows, contentRows)),
        )
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

  function addContent(courseId, moduleId, { type }) {
    const selectedCourseId = Number(courseId)
    const selectedModuleId = Number(moduleId)
    const content = moduleContent(courses, selectedCourseId, selectedModuleId)
    const number = content.reduce((max, item) => Math.max(max, item.number ?? 0), 0) + 1
    const created = {
      id: `local-${number}`,
      number,
      type,
      position: nextPosition(content),
    }

    setCourses((current) =>
      withModuleContent(current, selectedCourseId, selectedModuleId, (items) =>
        placeContent(items, created),
      ),
    )
    return created
  }

  function storeContent(courseId, moduleId, item) {
    setCourses((current) =>
      withModuleContent(current, courseId, moduleId, (content) => placeContent(content, item)),
    )
    return item
  }

  async function createFile(courseId, moduleId, { name, file }) {
    const position = nextPosition(moduleContent(courses, courseId, moduleId))
    const body = new FormData()
    body.append('module_id', String(moduleId))
    body.append('title', name)
    body.append('position', String(position))
    body.append('file', file)
    const created = await apiForm('/api/files', { method: 'POST', body })
    return storeContent(courseId, moduleId, toContent(created))
  }

  async function updateFile(courseId, moduleId, contentId, { name, file }) {
    const current = moduleContent(courses, courseId, moduleId).find((item) =>
      sameId(item, contentId),
    )
    let row = null
    if (current?.name !== name) {
      row = await api(`/api/content/${contentId}`, {
        method: 'PATCH',
        body: { title: name },
      })
    }
    if (file) {
      const body = new FormData()
      body.append('file', file)
      row = await apiForm(`/api/files/${contentId}`, { method: 'PATCH', body })
    }
    if (!row) {
      return current
    }
    const item = toContent(row)
    if (file) {
      item.fileUrl = `${item.fileUrl}?t=${Date.now()}`
    }
    return storeContent(courseId, moduleId, item)
  }

  async function createQuiz(courseId, moduleId, { name }) {
    const position = nextPosition(moduleContent(courses, courseId, moduleId))
    const created = await api('/api/quizzes', {
      method: 'POST',
      body: { module_id: Number(moduleId), title: name, position },
    })
    return storeContent(courseId, moduleId, toContent(created))
  }

  async function renameContent(courseId, moduleId, contentId, name) {
    const updated = await api(`/api/content/${contentId}`, {
      method: 'PATCH',
      body: { title: name },
    })
    return storeContent(courseId, moduleId, toContent(updated))
  }

  async function deleteContent(courseId, moduleId, contentId) {
    if (!String(contentId).startsWith('local-')) {
      await api(`/api/content/${contentId}`, { method: 'DELETE' })
    }
    setCourses((current) =>
      withModuleContent(current, courseId, moduleId, (content) =>
        content.filter((item) => !sameId(item, contentId)),
      ),
    )
  }

  async function refreshContent(courseId, moduleId, contentId) {
    const row = await api(`/api/content/${contentId}`)
    return storeContent(courseId, moduleId, toContent(row))
  }

  async function addQuestion(courseId, moduleId, contentId, draft) {
    const quiz = findQuiz(courses, courseId, moduleId, contentId)
    const position =
      (quiz?.questions ?? []).reduce(
        (max, question) => Math.max(max, question.position ?? 0),
        0,
      ) + 1
    try {
      await api(`/api/quizzes/${contentId}/questions`, {
        method: 'POST',
        body: {
          text: draft.text,
          position,
          choices: draft.choices.map((choice) => ({
            text: choice.text,
            position: choice.position,
            is_correct: choice.correct,
          })),
        },
      })
      await refreshContent(courseId, moduleId, contentId)
    } catch (err) {
      await refreshContent(courseId, moduleId, contentId).catch(() => {})
      throw err
    }
  }

  async function deleteQuestion(courseId, moduleId, contentId, questionId) {
    try {
      await api(`/api/questions/${questionId}`, { method: 'DELETE' })
      await refreshContent(courseId, moduleId, contentId)
    } catch (err) {
      await refreshContent(courseId, moduleId, contentId).catch(() => {})
      throw err
    }
  }

  async function saveQuestion(courseId, moduleId, contentId, questionId, draft) {
    const quiz = findQuiz(courses, courseId, moduleId, contentId)
    const existing = (quiz?.questions ?? []).find((question) => question.id === questionId)
    if (!existing) {
      throw new Error('Question not found')
    }

    try {
      if (draft.text !== existing.text) {
        await api(`/api/questions/${questionId}`, {
          method: 'PATCH',
          body: { text: draft.text },
        })
      }

      const added = draft.choices.filter((choice) => choice.id == null)
      const kept = draft.choices.filter((choice) => choice.id != null)
      const removed = existing.choices.filter(
        (choice) => !kept.some((item) => item.id === choice.id),
      )
      const choicePosition = existing.choices.reduce(
        (max, choice) => Math.max(max, choice.position ?? 0),
        0,
      )
      const addedWithPositions = added.map((choice, offset) => ({
        choice,
        position: choicePosition + offset + 1,
      }))
      const correctAdded = addedWithPositions.find((item) => item.choice.correct)
      const orderedAdded = correctAdded
        ? [correctAdded, ...addedWithPositions.filter((item) => item !== correctAdded)]
        : addedWithPositions
      for (const item of orderedAdded) {
        await api(`/api/questions/${questionId}/choices`, {
          method: 'POST',
          body: {
            text: item.choice.text,
            position: item.position,
            is_correct: item.choice.correct,
          },
        })
      }

      for (const choice of kept) {
        const previous = existing.choices.find((item) => item.id === choice.id)
        if (!previous) {
          continue
        }
        const patch = {}
        if (previous.text !== choice.text) {
          patch.text = choice.text
        }
        if (!previous.correct && choice.correct) {
          patch.is_correct = true
        }
        if (Object.keys(patch).length > 0) {
          await api(`/api/choices/${choice.id}`, { method: 'PATCH', body: patch })
        }
      }

      for (const choice of removed) {
        await api(`/api/choices/${choice.id}`, { method: 'DELETE' })
      }

      await refreshContent(courseId, moduleId, contentId)
    } catch (err) {
      await refreshContent(courseId, moduleId, contentId).catch(() => {})
      throw err
    }
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
        createFile,
        updateFile,
        createQuiz,
        renameContent,
        deleteContent,
        addQuestion,
        saveQuestion,
        deleteQuestion,
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
