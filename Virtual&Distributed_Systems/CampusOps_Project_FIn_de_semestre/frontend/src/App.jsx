import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, CssBaseline } from '@mui/material'
import theme from './theme'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'

import Login          from './pages/Login'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword  from './pages/ResetPassword'
import Dashboard      from './pages/Dashboard'
import Sessions       from './pages/Sessions'
import CreateSession  from './pages/CreateSession'
import PendingSessions from './pages/PendingSessions'
import Planning       from './pages/Planning'
import Absences       from './pages/Absences'
import AbsenceStats   from './pages/AbsenceStats'
import MarkAbsence    from './pages/MarkAbsence'
import Payments       from './pages/Payments'
import Progress       from './pages/Progress'
import Users          from './pages/Users'
import Teachers       from './pages/Teachers'
import Students       from './pages/Students'
import Groups         from './pages/Groups'
import Courses        from './pages/Courses'
import MailInbox      from './pages/MailInbox'
import Profile        from './pages/Profile'

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public routes — no auth required */}
            <Route path="/login"            element={<Login />} />
            <Route path="/forgot-password"  element={<ForgotPassword />} />
            <Route path="/reset-password"   element={<ResetPassword />} />

            {/* Protected layout */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />

              {/* Dashboard */}
              <Route path="dashboard" element={<Dashboard />} />

              {/* Sessions */}
              <Route path="sessions" element={<Sessions />} />
              <Route
                path="sessions/create"
                element={
                  <ProtectedRoute roles={['admin', 'secretary', 'teacher']}>
                    <CreateSession />
                  </ProtectedRoute>
                }
              />
              <Route
                path="sessions/pending"
                element={
                  <ProtectedRoute roles={['admin']}>
                    <PendingSessions />
                  </ProtectedRoute>
                }
              />
              <Route
                path="planning"
                element={
                  <ProtectedRoute roles={['admin', 'secretary', 'teacher']}>
                    <Planning />
                  </ProtectedRoute>
                }
              />

              {/* Absences */}
              <Route path="absences" element={<Absences />} />
              <Route
                path="absences/mark"
                element={
                  <ProtectedRoute roles={['teacher', 'secretary']}>
                    <MarkAbsence />
                  </ProtectedRoute>
                }
              />
              <Route
                path="absences/stats"
                element={
                  <ProtectedRoute roles={['admin', 'secretary', 'teacher']}>
                    <AbsenceStats />
                  </ProtectedRoute>
                }
              />

              {/* Payments */}
              <Route
                path="payments"
                element={
                  <ProtectedRoute roles={['admin', 'secretary', 'student']}>
                    <Payments />
                  </ProtectedRoute>
                }
              />

              {/* Progress */}
              <Route
                path="progress"
                element={
                  <ProtectedRoute roles={['admin', 'secretary', 'teacher']}>
                    <Progress />
                  </ProtectedRoute>
                }
              />

              {/* Admin & secretary management */}
              <Route
                path="users"
                element={
                  <ProtectedRoute roles={['admin']}>
                    <Users />
                  </ProtectedRoute>
                }
              />
              <Route
                path="teachers"
                element={
                  <ProtectedRoute roles={['admin']}>
                    <Teachers />
                  </ProtectedRoute>
                }
              />
              <Route
                path="students"
                element={
                  <ProtectedRoute roles={['admin', 'secretary']}>
                    <Students />
                  </ProtectedRoute>
                }
              />
              <Route
                path="groups"
                element={
                  <ProtectedRoute roles={['admin', 'secretary']}>
                    <Groups />
                  </ProtectedRoute>
                }
              />
              <Route
                path="courses"
                element={
                  <ProtectedRoute roles={['admin', 'secretary']}>
                    <Courses />
                  </ProtectedRoute>
                }
              />
              <Route
                path="mail"
                element={
                  <ProtectedRoute roles={['admin']}>
                    <MailInbox />
                  </ProtectedRoute>
                }
              />

              {/* Profile — all roles */}
              <Route path="profile" element={<Profile />} />
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
