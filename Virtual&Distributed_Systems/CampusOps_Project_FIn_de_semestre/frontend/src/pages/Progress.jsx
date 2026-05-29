import { useState } from 'react'
import {
  Box, Typography, Card, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Skeleton, Button, Chip, Alert, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, MenuItem,
  Grid, LinearProgress, Tooltip,
} from '@mui/material'
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined'
import EditOutlinedIcon      from '@mui/icons-material/EditOutlined'
import { useAuth } from '../context/AuthContext'
import { useApi }  from '../hooks/useApi'
import api from '../api/client'

const TYPE_COLOR = { chapter: 'primary', competency: 'secondary', tp: 'success' }
const TYPE_LABEL = { chapter: 'Chapter', competency: 'Competency', tp: 'TP' }

export default function Progress() {
  const { user } = useAuth()
  const canEdit  = ['teacher', 'admin', 'secretary'].includes(user?.role)

  const { data: entries, loading, error, refetch } = useApi('/progress/')
  const { data: courses }  = useApi('/courses/')
  const { data: groups }   = useApi('/groups/')

  const [open, setOpen] = useState(false)
  const [editTarget, setEditTarget]   = useState(null)
  const [formError, setFormError]     = useState(null)
  const [success, setSuccess]         = useState(null)
  const [submitting, setSubmitting]   = useState(false)
  const [form, setForm] = useState({
    course_id: '', group_id: '', chapter: '',
    entry_type: 'chapter', completion: '', notes: '',
  })

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleClose = () => {
    setOpen(false)
    setEditTarget(null)
    setFormError(null)
    setForm({ course_id: '', group_id: '', chapter: '', entry_type: 'chapter', completion: '', notes: '' })
  }

  const openEdit = (entry) => {
    setEditTarget(entry)
    setForm({
      course_id:  entry.course_id,
      group_id:   entry.group_id,
      chapter:    entry.chapter,
      entry_type: entry.entry_type,
      completion: String(entry.completion),
      notes:      entry.notes || '',
    })
    setOpen(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    const payload = {
      course_id:  form.course_id,
      group_id:   form.group_id,
      chapter:    form.chapter.trim(),
      entry_type: form.entry_type,
      completion: parseFloat(form.completion) || 0,
      notes:      form.notes.trim() || null,
    }
    try {
      if (editTarget) {
        await api.patch(`/progress/${editTarget.id}`, {
          chapter:    payload.chapter,
          completion: payload.completion,
          notes:      payload.notes,
        })
        setSuccess('Entry updated.')
      } else {
        await api.post('/progress/', payload)
        setSuccess('Progress entry logged.')
      }
      handleClose()
      refetch()
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to save entry')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h5">Progress Tracking</Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            Track chapters, competencies, and TPs by group
          </Typography>
        </Box>
        {canEdit && (
          <Button variant="contained" startIcon={<AddCircleOutlinedIcon sx={{ fontSize: 18 }} />} onClick={() => setOpen(true)}>
            Log Progress
          </Button>
        )}
      </Box>

      {success && <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 3 }}>{success}</Alert>}
      {error   && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Course</TableCell>
                <TableCell>Group</TableCell>
                <TableCell>Chapter / Topic</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Completion</TableCell>
                <TableCell>Teacher</TableCell>
                {canEdit && <TableCell align="right">Actions</TableCell>}
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                [1, 2, 3].map((k) => (
                  <TableRow key={k}>
                    {[1,2,3,4,5,6].map((i) => <TableCell key={i}><Skeleton height={20} /></TableCell>)}
                  </TableRow>
                ))
              ) : !entries?.length ? (
                <TableRow>
                  <TableCell colSpan={canEdit ? 7 : 6} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                    No progress entries yet.
                  </TableCell>
                </TableRow>
              ) : (
                entries.map((e) => (
                  <TableRow key={e.id} hover>
                    <TableCell sx={{ fontWeight: 500 }}>{e.course_name}</TableCell>
                    <TableCell>{e.group_name}</TableCell>
                    <TableCell>{e.chapter}</TableCell>
                    <TableCell>
                      <Chip
                        label={TYPE_LABEL[e.entry_type] || e.entry_type}
                        color={TYPE_COLOR[e.entry_type] || 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell sx={{ minWidth: 140 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={e.completion}
                          sx={{ flex: 1, height: 6, borderRadius: 3 }}
                          color={e.completion >= 100 ? 'success' : e.completion >= 50 ? 'primary' : 'warning'}
                        />
                        <Typography variant="caption" sx={{ minWidth: 34, textAlign: 'right' }}>
                          {e.completion}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell sx={{ color: 'text.secondary' }}>{e.teacher_name}</TableCell>
                    {canEdit && (
                      <TableCell align="right">
                        <Tooltip title="Edit entry">
                          <Button size="small" variant="outlined"
                            startIcon={<EditOutlinedIcon sx={{ fontSize: 14 }} />}
                            onClick={() => openEdit(e)}
                            sx={{ fontSize: '0.75rem', py: 0.5 }}>
                            Edit
                          </Button>
                        </Tooltip>
                      </TableCell>
                    )}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Create / Edit dialog */}
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>{editTarget ? 'Edit Progress Entry' : 'Log Progress'}</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}
          <Box component="form" id="progress-form" onSubmit={handleSubmit}>
            <Grid container spacing={2} sx={{ mt: 0 }}>
              {!editTarget && (
                <>
                  <Grid item xs={12} sm={6}>
                    <TextField select label="Course" value={form.course_id} onChange={set('course_id')} fullWidth required>
                      {(courses || []).map((c) => <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>)}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField select label="Group" value={form.group_id} onChange={set('group_id')} fullWidth required>
                      {(groups || []).map((g) => <MenuItem key={g.id} value={g.id}>{g.name}</MenuItem>)}
                    </TextField>
                  </Grid>
                </>
              )}
              <Grid item xs={12}>
                <TextField
                  label="Chapter / Topic"
                  value={form.chapter}
                  onChange={set('chapter')}
                  fullWidth required
                  placeholder="e.g. Chapter 3: Integrals"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField select label="Type" value={form.entry_type} onChange={set('entry_type')} fullWidth required>
                  <MenuItem value="chapter">Chapter</MenuItem>
                  <MenuItem value="competency">Competency</MenuItem>
                  <MenuItem value="tp">TP (Lab Work)</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Completion %"
                  type="number"
                  value={form.completion}
                  onChange={set('completion')}
                  fullWidth required
                  slotProps={{ htmlInput: { min: 0, max: 100 } }}
                  placeholder="0–100"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Notes (optional)"
                  value={form.notes}
                  onChange={set('notes')}
                  fullWidth multiline rows={2}
                  placeholder="e.g. Covered sections 3.1–3.4"
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleClose} variant="outlined">Cancel</Button>
          <Button type="submit" form="progress-form" variant="contained" disabled={submitting}>
            {submitting ? 'Saving…' : editTarget ? 'Save Changes' : 'Log Progress'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
