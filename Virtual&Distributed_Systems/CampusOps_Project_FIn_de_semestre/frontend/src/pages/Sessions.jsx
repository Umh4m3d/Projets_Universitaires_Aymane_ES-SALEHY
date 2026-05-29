import { useState } from 'react'
import {
  Box, Typography, Card, CardContent, Chip, Divider, Skeleton,
  Button, Dialog, DialogTitle, DialogContent, DialogActions, Alert,
} from '@mui/material'
import AccessTimeOutlinedIcon from '@mui/icons-material/AccessTimeOutlined'
import RoomOutlinedIcon       from '@mui/icons-material/RoomOutlined'
import PersonOutlinedIcon     from '@mui/icons-material/PersonOutlined'
import DeleteOutlinedIcon     from '@mui/icons-material/DeleteOutlined'
import { useApi } from '../hooks/useApi'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'

export default function Sessions() {
  const { user } = useAuth()
  const { data, loading, error, refetch } = useApi('/sessions/week')
  const canDelete = ['admin', 'secretary', 'teacher'].includes(user?.role)

  const [confirmDelete, setConfirmDelete] = useState(null)
  const [deleting, setDeleting]           = useState(false)
  const [deleteError, setDeleteError]     = useState(null)

  const handleDelete = async () => {
    setDeleting(true)
    setDeleteError(null)
    try {
      await api.delete(`/sessions/${confirmDelete.id}`)
      setConfirmDelete(null)
      refetch()
    } catch (err) {
      setDeleteError(err.response?.data?.detail || 'Failed to delete session')
      setConfirmDelete(null)
    } finally {
      setDeleting(false)
    }
  }

  const grouped = (data || []).reduce((acc, s) => {
    acc[s.date] = acc[s.date] || []
    acc[s.date].push(s)
    return acc
  }, {})

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">Sessions</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>This week's schedule</Typography>
      </Box>

      {deleteError && (
        <Alert severity="error" onClose={() => setDeleteError(null)} sx={{ mb: 3 }}>
          {deleteError}
        </Alert>
      )}

      {loading && [1, 2].map((k) => (
        <Skeleton key={k} height={120} sx={{ mb: 2, borderRadius: 2 }} />
      ))}

      {error && <Typography color="error">{error}</Typography>}

      {!loading && Object.keys(grouped).length === 0 && (
        <Card>
          <CardContent>
            <Typography variant="body2" sx={{ textAlign: 'center', py: 2 }}>
              No sessions this week.
            </Typography>
          </CardContent>
        </Card>
      )}

      {Object.entries(grouped).sort().map(([date, sessions]) => (
        <Box key={date} sx={{ mb: 3 }}>
          <Typography sx={{
            fontSize: '0.7rem', fontWeight: 700, color: 'text.secondary',
            textTransform: 'uppercase', letterSpacing: '0.08em', mb: 1.5,
          }}>
            {new Date(date + 'T00:00:00').toLocaleDateString('en-GB', {
              weekday: 'long', day: 'numeric', month: 'long',
            })}
          </Typography>

          <Card>
            <CardContent sx={{ p: '0 !important' }}>
              {sessions.map((s, i) => (
                <Box key={s.id}>
                  {i > 0 && <Divider />}
                  <Box sx={{
                    px: 2.5, py: 2,
                    display: 'flex', alignItems: 'center', gap: 3,
                    opacity: s.status === 'rejected' ? 0.55 : 1,
                  }}>
                    {/* Time */}
                    <Box sx={{ minWidth: 80, textAlign: 'center', flexShrink: 0 }}>
                      <Typography sx={{
                        fontSize: '1rem', fontWeight: 700, lineHeight: 1,
                        color: s.status === 'pending'
                          ? 'warning.main'
                          : s.status === 'rejected' ? 'text.disabled' : 'primary.main',
                      }}>
                        {s.start_time?.slice(0, 5)}
                      </Typography>
                      <Typography variant="caption">– {s.end_time?.slice(0, 5)}</Typography>
                    </Box>

                    <Divider orientation="vertical" flexItem />

                    {/* Info */}
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.75, flexWrap: 'wrap' }}>
                        <Typography sx={{ fontWeight: 600, fontSize: '0.875rem' }}>
                          {s.course_name}
                        </Typography>
                        {s.status === 'pending' && (
                          <Chip label="Pending approval" size="small" color="warning" />
                        )}
                        {s.status === 'rejected' && (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                            <Chip label="Rejected" size="small" color="error" />
                            {s.rejection_reason && (
                              <Typography variant="caption" sx={{ color: 'error.main', maxWidth: 260 }}>
                                Reason: {s.rejection_reason}
                              </Typography>
                            )}
                          </Box>
                        )}
                      </Box>

                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <RoomOutlinedIcon sx={{ fontSize: 13, color: 'text.secondary' }} />
                          <Typography variant="body2">{s.room}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <PersonOutlinedIcon sx={{ fontSize: 13, color: 'text.secondary' }} />
                          <Typography variant="body2">{s.teacher_name}</Typography>
                        </Box>
                      </Box>
                    </Box>

                    {/* Right side: group chip + delete */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexShrink: 0 }}>
                      <Chip label={s.group_name} size="small" variant="outlined" />
                      {canDelete && (
                        <Button
                          size="small"
                          color="error"
                          variant="outlined"
                          startIcon={<DeleteOutlinedIcon sx={{ fontSize: 14 }} />}
                          onClick={() => setConfirmDelete(s)}
                          sx={{ fontSize: '0.72rem', py: 0.4, px: 1 }}
                        >
                          Delete
                        </Button>
                      )}
                    </Box>
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Box>
      ))}

      {/* Delete confirmation dialog */}
      <Dialog open={!!confirmDelete} onClose={() => setConfirmDelete(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Delete session</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 1 }}>
            Are you sure you want to delete this session?
          </Typography>
          {confirmDelete && (
            <Box sx={{ p: 1.5, bgcolor: '#F8FAFC', borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>{confirmDelete.course_name}</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                {confirmDelete.date} · {confirmDelete.start_time?.slice(0, 5)}–{confirmDelete.end_time?.slice(0, 5)} · {confirmDelete.room}
              </Typography>
            </Box>
          )}
          {user?.role === 'teacher' && confirmDelete?.status === 'approved' && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              Approved sessions can only be deleted by an admin or secretary.
            </Alert>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setConfirmDelete(null)} variant="outlined">Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained" disabled={deleting}>
            {deleting ? 'Deleting…' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
