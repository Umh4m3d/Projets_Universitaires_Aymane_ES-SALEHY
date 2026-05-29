import { useState } from 'react'
import {
  Box, Typography, Card, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Skeleton,
  Button, Alert, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField,
} from '@mui/material'
import CheckOutlinedIcon from '@mui/icons-material/CheckOutlined'
import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined'
import { useApi } from '../hooks/useApi'
import api from '../api/client'

export default function PendingSessions() {
  const { data, loading, refetch } = useApi('/sessions/pending')

  const [working, setWorking]           = useState(null)
  const [error, setError]               = useState(null)
  const [rejectTarget, setRejectTarget] = useState(null)
  const [reason, setReason]             = useState('')
  const [submitting, setSubmitting]     = useState(false)

  // ── Approve ───────────────────────────────────────────────────────
  const handleApprove = async (id) => {
    setWorking(id)
    setError(null)
    try {
      await api.patch(`/sessions/${id}/approve`)
      refetch()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to approve session')
    } finally {
      setWorking(null)
    }
  }

  // ── Open reject dialog ────────────────────────────────────────────
  const openReject = (session) => {
    setRejectTarget(session)
    setReason('')
  }

  // ── Confirm rejection ─────────────────────────────────────────────
  const handleReject = async () => {
    setSubmitting(true)
    setError(null)
    try {
      await api.patch(`/sessions/${rejectTarget.id}/reject`, {
        reason: reason.trim() || null,
      })
      setRejectTarget(null)
      setReason('')
      refetch()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reject session')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box>

      {/* Page header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">Session Requests</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          Review and approve or reject sessions submitted by teachers
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Teacher</TableCell>
                <TableCell>Course</TableCell>
                <TableCell>Group</TableCell>
                <TableCell>Room</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Time</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                [1, 2, 3].map((k) => (
                  <TableRow key={k}>
                    {[1,2,3,4,5,6,7].map((i) => (
                      <TableCell key={i}><Skeleton height={20} /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : !data?.length ? (
                <TableRow>
                  <TableCell colSpan={7} align="center"
                    sx={{ py: 4, color: 'text.secondary' }}>
                    No pending session requests.
                  </TableCell>
                </TableRow>
              ) : (
                data.map((s) => (
                  <TableRow key={s.id} hover>
                    <TableCell sx={{ fontWeight: 500 }}>
                      {s.teacher_name}
                    </TableCell>
                    <TableCell>{s.course_name}</TableCell>
                    <TableCell>
                      <Chip label={s.group_name} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>{s.room}</TableCell>
                    <TableCell>{s.date}</TableCell>
                    <TableCell>
                      {s.start_time?.slice(0, 5)} – {s.end_time?.slice(0, 5)}
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        <Button
                          size="small"
                          color="success"
                          variant="outlined"
                          startIcon={<CheckOutlinedIcon sx={{ fontSize: 14 }} />}
                          disabled={working === s.id}
                          onClick={() => handleApprove(s.id)}
                          sx={{ fontSize: '0.75rem', py: 0.5 }}
                        >
                          Approve
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          variant="outlined"
                          startIcon={<CloseOutlinedIcon sx={{ fontSize: 14 }} />}
                          disabled={working === s.id}
                          onClick={() => openReject(s)}
                          sx={{ fontSize: '0.75rem', py: 0.5 }}
                        >
                          Reject
                        </Button>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* ── Rejection reason dialog ─────────────────────────────────── */}
      <Dialog
        open={!!rejectTarget}
        onClose={() => setRejectTarget(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Reject session request</DialogTitle>
        <DialogContent>

          {/* Session summary */}
          {rejectTarget && (
            <Box sx={{
              mb: 2.5, p: 2,
              bgcolor: '#F8FAFC',
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'divider',
            }}>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                {rejectTarget.course_name}
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                {rejectTarget.teacher_name} · {rejectTarget.group_name} ·{' '}
                {rejectTarget.room} · {rejectTarget.date}{' '}
                {rejectTarget.start_time?.slice(0, 5)}–{rejectTarget.end_time?.slice(0, 5)}
              </Typography>
            </Box>
          )}

          <TextField
            label="Reason for rejection"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            fullWidth
            multiline
            rows={3}
            placeholder="Explain why this session request is being rejected. The teacher will see this message."
            helperText="Optional but recommended so the teacher understands what to change."
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setRejectTarget(null)}
            variant="outlined"
          >
            Cancel
          </Button>
          <Button
            onClick={handleReject}
            color="error"
            variant="contained"
            disabled={submitting}
          >
            {submitting ? 'Rejecting…' : 'Confirm Rejection'}
          </Button>
        </DialogActions>
      </Dialog>

    </Box>
  )
}
