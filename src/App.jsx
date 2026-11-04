import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider, RequireAuth } from './auth/AuthContext.jsx'
import Layout from './components/Layout.jsx'
import { CoursesProvider } from './courses/CoursesContext.jsx'
import { GroupsProvider } from './groups/GroupsContext.jsx'
import ContentDetailPage from './pages/ContentDetailPage.jsx'
import CourseDetailPage from './pages/CourseDetailPage.jsx'
import CoursesPage from './pages/CoursesPage.jsx'
import GroupDetailPage from './pages/GroupDetailPage.jsx'
import GroupsPage from './pages/GroupsPage.jsx'
import HomePage from './pages/HomePage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import ModulePage from './pages/ModulePage.jsx'
import UserDetailPage from './pages/UserDetailPage.jsx'

export default function App() {
  return (
    <AuthProvider>
      <CoursesProvider>
        <GroupsProvider>
          <BrowserRouter>
            <Routes>
              <Route path="login" element={<LoginPage />} />
              <Route element={<RequireAuth />}>
                <Route element={<Layout />}>
                  <Route index element={<HomePage />} />
                  <Route path="courses" element={<CoursesPage />} />
                  <Route path="courses/:number" element={<CourseDetailPage />} />
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
              </Route>
            </Routes>
          </BrowserRouter>
        </GroupsProvider>
      </CoursesProvider>
    </AuthProvider>
  )
}
