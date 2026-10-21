import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import { CoursesProvider } from './courses/CoursesContext.jsx'
import { GroupsProvider } from './groups/GroupsContext.jsx'
import ContentDetailPage from './pages/ContentDetailPage.jsx'
import CoursePage from './pages/CoursePage.jsx'
import CoursesPage from './pages/CoursesPage.jsx'
import GroupDetailPage from './pages/GroupDetailPage.jsx'
import GroupsPage from './pages/GroupsPage.jsx'
import HomePage from './pages/HomePage.jsx'
import ModulePage from './pages/ModulePage.jsx'
import UserDetailPage from './pages/UserDetailPage.jsx'

export default function App() {
  return (
    <CoursesProvider>
      <GroupsProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<HomePage />} />
              <Route path="courses" element={<CoursesPage />} />
              <Route path="courses/:number" element={<CoursePage />} />
              <Route
                path="courses/:number/modules/:moduleNumber"
                element={<ModulePage />}
              />
              <Route
                path="courses/:number/modules/:moduleNumber/content/:contentNumber"
                element={<ContentDetailPage />}
              />
              <Route path="groups" element={<GroupsPage />} />
              <Route path="groups/:number" element={<GroupDetailPage />} />
              <Route
                path="groups/:number/users/:userNumber"
                element={<UserDetailPage />}
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </GroupsProvider>
    </CoursesProvider>
  )
}
