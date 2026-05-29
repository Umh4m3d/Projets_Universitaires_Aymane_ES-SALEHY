import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Typography, Card, CardContent, Grid,
  TextField, Button, MenuItem, Alert, CircularProgress, Chip,
} from '@mui/material'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function CreateSession() {
  const navigate = useNavigate()
  const { user } = useAuth()

  const isTeacher          = user?.role === 'teacher'
  const isAdminOrSecretary = ['admin', 'secretary'].includes(user?.role)

  const [courses, setCourses]     = useState([])
  const [groups, setGroups]       = useState([])
  const [teachers, setTeachers]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]         = useState(null)
  const [success, setSuccess]     = useState(false)

  const [form, setForm] = useState({
    course_id:  '',
    teacher_id: '',
    group_id:   '',
    room:       '',
    date:       '',
    start_time: '',
    end_time:   '',
  })

  useEffect(() => {
    const requests = [
      api.get('/courses/'),
      api.get('/groups/'),
    ]

    // Only admin and secretary can pick any teacher
    // Teachers only submit for themselves so no need to fetch the list
    if (isAdminOrSecretary) {
      requests.push(api.get('/users/teachers'))
    }

    Promise.all(requests)
      .then(([c, g, t]) => {
        setCourses(c.data)
        setGroups(g.data)
        if (t) setTeachers(t.data)

        // Pre-fill teacher_id for teachers
        if (isTeacher && user?.id) {
          setForm((f) => ({ ...f, teacher_id: user.id }))
        }
      })
      .catch(() => setError('Failed to load form data'))
      .finally(() => setLoading(false))
  }, [isAdminOrSecretary, isTeacher, user?.id])

  const set = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await api.post('/sessions/', {
        ...form,
        start_time: form.start_time + ':00',
        end_time:   form.end_time   + ':00',
      })
      setSuccess(true)
      setTimeout(() => navigate('/sessions'), 1800)
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(
        Array.isArray(detail)
          ? detail.map((d) => d.msg).join(', ')
          : detail || 'Failed to submit session'
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress size={28} />
      </Box>
    )
  }

  return (
    <Box sx={{ maxWidth: 680 }}>

      {/* Page header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">
          {isTeacher ? 'Request a Session' : 'Schedule Session'}
        </Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          {isTeacher
            ? 'Submit a session request for admin approval'
            : 'Add a new class to the timetable'}
        </Typography>
      </Box>

      {/* Info banner for teachers */}
      {isTeacher && (
        <Alert
          severity="info"
          icon={<InfoOutlinedIcon fontSize="inherit" />}
          sx={{ mb: 3 }}
        >
          Your request will be reviewed by an administrator before appearing
          on the timetable. You will be able to track it under{' '}
          <strong>Sessions</strong>.
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {isTeacher
            ? 'Session request submitted successfully. Awaiting admin approval.'
            : 'Session created successfully. Redirecting…'}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
      )}

      <Card>
        <CardContent sx={{ p: 3 }}>
          <Box component="form" onSubmit={handleSubmit}>
            <Grid container spacing={2.5}>

              {/* Course */}
              <Grid item xs={12} sm={6}>
                <TextField
                  select
                  label="Course"
                  value={form.course_id}
                  onChange={set('course_id')}
                  fullWidth
                  required
                >
                  {courses.map((c) => (
                    <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                  ))}
                </TextField>
              </Grid>

              {/* Teacher — dropdown for admin/secretary, read-only for teacher */}
              <Grid item xs={12} sm={6}>
                {isAdminOrSecretary ? (
                  <TextField
                    select
                    label="Teacher"
                    value={form.teacher_id}
                    onChange={set('teacher_id')}
                    fullWidth
                    required
                  >
                    {teachers.map((t) => (
                      <MenuItem key={t.id} value={t.id}>{t.full_name}</MenuItem>
                    ))}
                  </TextField>
                ) : (
                  <TextField
                    label="Teacher"
                    value={user?.full_name || ''}
                    fullWidth
                    disabled
                    helperText="You are submitting this request for yourself"
                  />
                )}
              </Grid>

              {/* Group */}
              <Grid item xs={12} sm={6}>
                <TextField
                  select
                  label="Group"
                  value={form.group_id}
                  onChange={set('group_id')}
                  fullWidth
                  required
                >
                  {groups.map((g) => (
                    <MenuItem key={g.id} value={g.id}>{g.name}</MenuItem>
                  ))}
                </TextField>
              </Grid>

              {/* Room */}
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Room"
                  value={form.room}
                  onChange={set('room')}
                  fullWidth
                  required
                  placeholder="e.g. Room 101"
                />
              </Grid>

              {/* Date */}
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Date"
                  type="date"
                  value={form.date}
                  onChange={set('date')}
                  fullWidth
                  required
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              {/* Start time */}
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Start time"
                  type="time"
                  value={form.start_time}
                  onChange={set('start_time')}
                  fullWidth
                  required
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              {/* End time */}
              <Grid item xs={12} sm={4}>
                <TextField
                  label="End time"
                  type="time"
                  value={form.end_time}
                  onChange={set('end_time')}
                  fullWidth
                  required
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              {/* Submit */}
              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={submitting}
                  sx={{ px: 4 }}
                >
                  {submitting
                    ? 'Submitting…'
                    : isTeacher ? 'Submit Request' : 'Create Session'}
                </Button>
              </Grid>

            </Grid>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}
