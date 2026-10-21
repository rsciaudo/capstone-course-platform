import { createContext, useContext, useState } from 'react'

const CoursesContext = createContext(null)

export function contentLabel(content, item) {
  const count = content.filter(
    (entry) => entry.type === item.type && entry.number <= item.number,
  ).length

  return `${item.type} ${count}`
}

export function CoursesProvider({ children }) {
  const [courses, setCourses] = useState([])

  function createCourse() {
    setCourses((current) => [
      ...current,
      { number: current.length + 1, modules: [] },
    ])
  }

  function addModule(courseNumber) {
    setCourses((current) =>
      current.map((course) => {
        if (course.number !== Number(courseNumber)) {
          return course
        }

        return {
          ...course,
          modules: [
            ...course.modules,
            { number: course.modules.length + 1, content: [] },
          ],
        }
      }),
    )
  }

  function addContent(courseNumber, moduleNumber, type) {
    setCourses((current) =>
      current.map((course) => {
        if (course.number !== Number(courseNumber)) {
          return course
        }

        return {
          ...course,
          modules: course.modules.map((module) => {
            if (module.number !== Number(moduleNumber)) {
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
      value={{ courses, createCourse, addModule, addContent }}
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
