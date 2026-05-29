import { useState, useEffect } from 'react'
import {
  Box, Typography, Card, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Skeleton, Button,
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, MenuItem, Grid, Alert, Tooltip,
} from '@mui/material'
import AddCircleOutlinedIcon  from '@mui/icons-material/AddCircleOutlined'
import EditOutlinedIcon       from '@mui/icons-material/EditOutlined'
import DeleteOutlinedIcon     from '@mui/icons-material/DeleteOutlined'
import BlockOutlinedIcon      from '@mui/icons-material/BlockOutlined'
import { useApi } from '../hooks/useApi'
import api from '../api/client'

export default function Students() {
  const [filterGroup, setFilterGroup]             = useState('')
  const [open, setOpen]                           = useState(false)
  const [editTarget, setEditTarget]               = useState(null)
  const [confirmDelete, setConfirmDelete]         = useState(null)
  const [confirmDeactivate, setConfirmDeactivate] = useState(null)
  const [error, setError]                         = useState(null)
  const [actionError, setActionError]             = useState(null)
  const [success, setSuccess]                     = useState(null)
  const [submitting, setSubmitting]               = useState(false)
  const [working, setWorking]                     = useState(false)
  const [unprofiledUsers, setUnprofiledUsers]     = useState([])
  const [form, setForm] = useState({
    user_id: '', establishment: '', group_id: '', year: '', parent_email: '',
  })

  // ✅ FIX: always use /students/ (enriched profiles) for both filtered and unfiltered views
  const { data: students, loading, refetch } = useApi(
    filterGroup ? `/students/?group_id=${filterGroup}` : '/students/'
  )
  const { data: groups } = useApi('/groups/')

  useEffect(() => {
    if (!open || editTarget) return
    api.get('/users/students').then((r) => {
      const profiledIds = new Set((students || []).map((s) => s.user_id))
      setUnprofiledUsers(r.data.filter((u) => !profiledIds.has(u.id)))
    }).catch(() => setUnprofiledUsers([]))
  }, [open, editTarget, students])

  useEffect(() => {
    if (editTarget) {
      setForm({
        user_id:       editTarget.user_id,
        establishment: editTarget.establishment,
        group_id:      editTarget.group_id || '',
        year:          String(editTarget.year),
        parent_email:  editTarget.parent_email || '',
      })
    }
  }, [editTarget])

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleClose = () => {
    setOpen(false)
    setEditTarget(null)
    setError(null)
    setForm({ user_id: '', establishment: '', group_id: '', year: '', parent_email: '' })
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await api.post('/students/', {
        user_id:       form.user_id,
        establishment: form.establishment,
        group_id:      form.group_id || null,
        year:          parseInt(form.year),
        parent_email:  form.parent_email.trim() || null,
      })
      setSuccess('Student profile created successfully.')
      handleClose()
      refetch()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create profile')
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await api.patch(`/students/${editTarget.id}`, {
        establishment: form.establishment,
        group_id:      form.group_id || null,
        year:          parseInt(form.year),
        parent_email:  form.parent_email.trim() || null,
      })
      setSuccess('Student profile updated successfully.')
      handleClose()
      refetch()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeactivate = async () => {
    setWorking(true)
    setActionError(null)
    try {
      await api.patch(`/users/${confirmDeactivate.user_id}/deactivate`)
      setSuccess(`${confirmDeactivate.full_name}'s account has been deactivated.`)
      setConfirmDeactivate(null)
      refetch()
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to deactivate account')
      setConfirmDeactivate(null)
    } finally {
      setWorking(false)
    }
  }

  const handleDelete = async () => {
    setWorking(true)
    setActionError(null)
    try {
      await api.delete(`/users/${confirmDelete.user_id}`)
      setSuccess(`${confirmDelete.full_name} has been permanently deleted.`)
      setConfirmDelete(null)
      refetch()
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to delete student')
      setConfirmDelete(null)
    } finally {
      setWorking(false)
    }
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h5">Students</Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>Manage student profiles, groups, and establishments</Typography>
        </Box>
        <Button variant="contained" startIcon={<AddCircleOutlinedIcon sx={{ fontSize: 18 }} />} onClick={() => { setEditTarget(null); setOpen(true) }}>
          Add Profile
        </Button>
      </Box>

      {success     && <Alert severity="success" onClose={() => setSuccess(null)}     sx={{ mb: 3 }}>{success}</Alert>}
      {actionError && <Alert severity="error"   onClose={() => setActionError(null)} sx={{ mb: 3 }}>{actionError}</Alert>}

      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <TextField select label="Filter by group" value={filterGroup} onChange={(e) => setFilterGroup(e.target.value)} size="small" sx={{ minWidth: 220 }}>
          <MenuItem value="">All groups</MenuItem>
          {(groups || []).map((g) => <MenuItem key={g.id} value={g.id}>{g.name}</MenuItem>)}
        </TextField>
        {filterGroup && <Button size="small" variant="outlined" onClick={() => setFilterGroup('')}>Clear filter</Button>}
        {filterGroup && (
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            Showing students in <strong>{(groups || []).find((g) => g.id === filterGroup)?.name}</strong>
          </Typography>
        )}
      </Box>

      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Parent Email</TableCell>
                <TableCell>Establishment</TableCell>
                <TableCell>Group</TableCell>
                <TableCell>Year</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                [1,2,3,4].map((k) => (
                  <TableRow key={k}>
                    {[1,2,3,4,5,6,7].map((i) => <TableCell key={i}><Skeleton height={20} /></TableCell>)}
                  </TableRow>
                ))
              ) : !students?.length ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                    {filterGroup ? 'No students found in this group.' : 'No student profiles yet.'}
                  </TableCell>
                </TableRow>
              ) : (
                students.map((s) => (
                  <TableRow key={s.id} hover>
                    <TableCell sx={{ fontWeight: 500 }}>{s.full_name}</TableCell>
                    <TableCell>{s.email}</TableCell>
                    <TableCell sx={{ color: s.parent_email ? 'text.primary' : 'text.disabled', fontSize: '0.8rem' }}>
                      {s.parent_email || '—'}
                    </TableCell>
                    <TableCell>{s.establishment}</TableCell>
                    <TableCell>
                      {s.group_name
                        ? <Chip label={s.group_name} size="small" variant="outlined" color="primary" />
                        : <Typography variant="caption" color="text.secondary">Unassigned</Typography>}
                    </TableCell>
                    <TableCell>Year {s.year}</TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        <Tooltip title="Edit profile">
                          <Button size="small" variant="outlined"
                            startIcon={<EditOutlinedIcon sx={{ fontSize: 14 }} />}
                            onClick={() => { setEditTarget(s); setOpen(true) }}
                            sx={{ fontSize: '0.75rem', py: 0.5 }}>
                            Edit
                          </Button>
                        </Tooltip>
                        <Tooltip title="Deactivate login access">
                          <Button size="small" color="warning" variant="outlined"
                            startIcon={<BlockOutlinedIcon sx={{ fontSize: 14 }} />}
                            onClick={() => setConfirmDeactivate(s)}
                            sx={{ fontSize: '0.75rem', py: 0.5 }}>
                            Deactivate
                          </Button>
                        </Tooltip>
                        <Tooltip title="Permanently delete student">
                          <Button size="small" color="error" variant="outlined"
                            startIcon={<DeleteOutlinedIcon sx={{ fontSize: 14 }} />}
                            onClick={() => setConfirmDelete(s)}
                            sx={{ fontSize: '0.75rem', py: 0.5 }}>
                            Delete
                          </Button>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Create / Edit dialog */}
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>{editTarget ? 'Edit Student Profile' : 'Create Student Profile'}</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Box component="form" id="student-form" onSubmit={editTarget ? handleUpdate : handleCreate}>
            <Grid container spacing={2} sx={{ mt: 0 }}>
              {!editTarget && (
                <Grid item xs={12}>
                  <TextField select label="Student account" value={form.user_id} onChange={set('user_id')} fullWidth required
                    helperText="Only students without an existing profile are shown">
                    {unprofiledUsers.length === 0
                      ? <MenuItem disabled value="">No students available</MenuItem>
                      : unprofiledUsers.map((u) => <MenuItem key={u.id} value={u.id}>{u.full_name} — {u.email}</MenuItem>)}
                  </TextField>
                </Grid>
              )}
              {editTarget && (
                <Grid item xs={12}>
                  <TextField label="Student" value={`${editTarget.full_name} — ${editTarget.email}`} fullWidth disabled />
                </Grid>
              )}
              <Grid item xs={12}>
                <TextField label="Establishment" value={form.establishment} onChange={set('establishment')} fullWidth required placeholder="e.g. Faculty of Sciences" />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField select label="Group" value={form.group_id} onChange={set('group_id')} fullWidth>
                  <MenuItem value="">— No group —</MenuItem>
                  {(groups || []).map((g) => <MenuItem key={g.id} value={g.id}>{g.name}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="Year" type="number" value={form.year} onChange={set('year')} fullWidth required
                  placeholder="e.g. 1" slotProps={{ htmlInput: { min: 1, max: 7 } }} />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Parent email (optional)"
                  type="email"
                  value={form.parent_email}
                  onChange={set('parent_email')}
                  fullWidth
                  placeholder="e.g. parent@example.com"
                  helperText="Used to send absence and payment notifications to the student's parent or guardian."
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleClose} variant="outlined">Cancel</Button>
          <Button type="submit" form="student-form" variant="contained" disabled={submitting}>
            {submitting ? 'Saving…' : editTarget ? 'Save Changes' : 'Create Profile'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Deactivate dialog */}
      <Dialog open={!!confirmDeactivate} onClose={() => setConfirmDeactivate(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Deactivate student account</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            Deactivate <strong>{confirmDeactivate?.full_name}</strong>? Their profile and records are preserved but they will not be able to log in.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setConfirmDeactivate(null)} variant="outlined">Cancel</Button>
          <Button onClick={handleDeactivate} color="warning" variant="contained" disabled={working}>
            {working ? 'Working…' : 'Deactivate'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete dialog */}
      <Dialog open={!!confirmDelete} onClose={() => setConfirmDelete(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Delete student permanently</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            Permanently delete <strong>{confirmDelete?.full_name}</strong>? If they have absences or payment records, deletion will be blocked — deactivate instead.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setConfirmDelete(null)} variant="outlined">Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained" disabled={working}>
            {working ? 'Working…' : 'Delete permanently'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
