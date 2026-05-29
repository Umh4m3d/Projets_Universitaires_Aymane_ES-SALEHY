import { useState, useEffect } from 'react'
import {
  Box, Typography, Card, CardContent, Grid,
  TextField, Button, MenuItem, Alert,
} from '@mui/material'
import api from '../api/client'

export default function MarkAbsence() {
  const [sessions, setSessions]   = useState([])
  const [students, setStudents]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]         = useState(null)
  const [success, setSuccess]     = useState(null)
  const [form, setForm] = useState({
    session_id: '', student_id: '', justification: '',
  })

  // Load today's sessions on mount
  useEffect(() => {
    api.get('/sessions/today')
      .then((r) => setSessions(r.data))
      .catch(() => setError('Failed to load today\'s sessions'))
      .finally(() => setLoading(false))
  }, [])

  // When session changes, load students for that session's group
  useEffect(() => {
    if (!form.session_id) {
      setStudents([])
      return
    }
    const session = sessions.find((s) => s.id === form.session_id)
    if (!session) return

    const params = session.group_id
      ? `?group_id=${session.group_id}`
      : ''

    api.get(`/users/students${params}`)
      .then((r) => setStudents(r.data))
      .catch(() => setStudents([]))
  }, [form.session_id, sessions])

  const set = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSessionChange = (e) => {
    setForm((f) => ({
      ...f,
      session_id: e.target.value,
      student_id: '',       // reset student when session changes
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setSubmitting(true)
    try {
      await api.post('/absences/', {
        session_id: form.session_id,
        student_id: form.student_id,
        justification: form.justification.trim() || null,
      })
      setSuccess('Absence recorded successfully.')
      setForm((f) => ({ ...f, student_id: '', justification: '' }))
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Failed to mark absence')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box sx={{ maxWidth: 560 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">Mark Absence</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          Record a student absence for a session
        </Typography>
      </Box>

      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}
      {error   && <Alert severity="error"   sx={{ mb: 3 }}>{error}</Alert>}

      {!loading && sessions.length === 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          No sessions are scheduled for today.
        </Alert>
      )}

      <Card>
        <CardContent sx={{ p: 3 }}>
          <Box component="form" onSubmit={handleSubmit}>
            <Grid container spacing={2.5}>

              <Grid item xs={12}>
                <TextField
                  select
                  label="Session"
                  value={form.session_id}
                  onChange={handleSessionChange}
                  fullWidth
                  required
                  disabled={sessions.length === 0}
                  helperText={
                    form.session_id
                      ? `Group: ${sessions.find(s => s.id === form.session_id)?.group_name || '—'}`
                      : 'Select a session to filter students by group'
                  }
                >
                  {sessions.map((s) => (
                    <MenuItem key={s.id} value={s.id}>
                      {s.course_name} — {s.start_time?.slice(0, 5)}–{s.end_time?.slice(0, 5)} ({s.room})
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  select
                  label="Student"
                  value={form.student_id}
                  onChange={set('student_id')}
                  fullWidth
                  required
                  disabled={!form.session_id || students.length === 0}
                  helperText={
                    form.session_id && students.length === 0
                      ? 'No students found for this group'
                      : ''
                  }
                >
                  {students.map((s) => (
                    <MenuItem key={s.id} value={s.id}>
                      {s.full_name} — {s.email}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  label="Justification (optional)"
                  value={form.justification}
                  onChange={set('justification')}
                  fullWidth
                  placeholder="Leave blank for an unjustified absence"
                  helperText="Absence remains unjustified until an administrator reviews it."
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={submitting || sessions.length === 0}
                  sx={{ px: 4 }}
                >
                  {submitting ? 'Saving…' : 'Mark Absent'}
                </Button>
              </Grid>

            </Grid>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}
