import { useState } from 'react'
import {
  Box, Typography, Card, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Skeleton,
  Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Alert,
} from '@mui/material'
import GavelOutlinedIcon from '@mui/icons-material/GavelOutlined'
import { useAuth } from '../context/AuthContext'
import { useApi } from '../hooks/useApi'
import { formatDate } from '../utils/date'
import api from '../api/client'

const JUSTIFIED_CHIP = {
  true:  { label: 'Justified',   color: 'success' },
  false: { label: 'Unjustified', color: 'error'   },
}

export default function Absences() {
  const { user } = useAuth()
  const isStudent = user?.role === 'student'
  const canJustify = user?.role === 'admin' || user?.role === 'secretary'
  const { data, loading, error, refetch } = useApi(isStudent ? '/absences/mine' : '/absences/')

  const [justifyTarget, setJustifyTarget] = useState(null)
  const [justification, setJustification] = useState('')
  const [submitting, setSubmitting]       = useState(false)
  const [justifyError, setJustifyError]   = useState(null)
  const [success, setSuccess]             = useState(null)

  const openJustify = (absence) => {
    setJustifyTarget(absence)
    setJustification(absence.justification && absence.justification !== 'None'
      ? absence.justification : '')
    setJustifyError(null)
  }

  const handleJustify = async (e) => {
    e.preventDefault()
    setJustifyError(null)
    setSubmitting(true)
    try {
      await api.patch(`/absences/${justifyTarget.id}/justify`, {
        is_justified: true,
        justification: justification.trim() || null,
      })
      setSuccess('Absence marked as justified.')
      setJustifyTarget(null)
      refetch()
    } catch (err) {
      setJustifyError(err.response?.data?.detail || 'Failed to justify absence')
    } finally {
      setSubmitting(false)
    }
  }

  const handleUnjustify = async () => {
    setJustifyError(null)
    setSubmitting(true)
    try {
      await api.patch(`/absences/${justifyTarget.id}/justify`, {
        is_justified: false,
        justification: null,
      })
      setSuccess('Absence marked as unjustified.')
      setJustifyTarget(null)
      refetch()
    } catch (err) {
      setJustifyError(err.response?.data?.detail || 'Failed to update absence')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">Absences</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          {isStudent ? 'Your attendance record' : 'All recorded absences'}
        </Typography>
      </Box>

      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}
      {error && <Typography color="error">{error}</Typography>}

      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                {!isStudent && <TableCell>Student</TableCell>}
                <TableCell>Date</TableCell>
                <TableCell>Course</TableCell>
                <TableCell>Marked By</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Justification</TableCell>
                {canJustify && <TableCell align="right">Actions</TableCell>}
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                [1, 2, 3].map((k) => (
                  <TableRow key={k}>
                    {[...Array(isStudent ? 5 : 6)].map((_, i) => (
                      <TableCell key={i}><Skeleton height={20} /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : !data?.length ? (
                <TableRow>
                  <TableCell colSpan={isStudent ? 5 : 7} align="center"
                    sx={{ py: 4, color: 'text.secondary' }}>
                    No absences recorded.
                  </TableCell>
                </TableRow>
              ) : (
                data.map((a) => {
                  const chip = JUSTIFIED_CHIP[String(a.is_justified)]
                  return (
                    <TableRow key={a.id} hover>
                      {!isStudent && <TableCell>{a.student_name || '—'}</TableCell>}
                      <TableCell>{a.session_date || '—'}</TableCell>
                      <TableCell>{a.course_name || '—'}</TableCell>
                      <TableCell>{a.marked_by_name || '—'}</TableCell>
                      <TableCell>
                        <Chip label={chip.label} color={chip.color} size="small" />
                      </TableCell>
                      <TableCell sx={{ color: 'text.secondary' }}>
                        {a.justification && a.justification !== 'None' ? a.justification : '—'}
                      </TableCell>
                      {canJustify && (
                        <TableCell align="right">
                          <Button
                            size="small"
                            variant="outlined"
                            color={a.is_justified ? 'warning' : 'success'}
                            startIcon={<GavelOutlinedIcon sx={{ fontSize: 14 }} />}
                            onClick={() => openJustify(a)}
                            sx={{ fontSize: '0.75rem', py: 0.5 }}
                          >
                            {a.is_justified ? 'Review' : 'Justify'}
                          </Button>
                        </TableCell>
                      )}
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Justify dialog */}
      <Dialog
        open={!!justifyTarget}
        onClose={() => setJustifyTarget(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {justifyTarget?.is_justified ? 'Update Justification' : 'Justify Absence'}
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          {justifyError && <Alert severity="error" sx={{ mb: 2 }}>{justifyError}</Alert>}
          <Typography variant="body2" sx={{ mb: 2 }}>
            Student: <strong>{justifyTarget?.student_name}</strong> —{' '}
            {justifyTarget?.session_date} ({justifyTarget?.course_name})
          </Typography>
          <Box component="form" id="justify-form" onSubmit={handleJustify}>
            <TextField
              label="Justification note"
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              fullWidth
              multiline
              rows={3}
              placeholder="Enter the reason for justification…"
              inputProps={{ maxLength: 500 }}
              helperText={`${justification.length}/500`}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
          <Button onClick={() => setJustifyTarget(null)} variant="outlined">
            Cancel
          </Button>
          {justifyTarget?.is_justified && (
            <Button
              onClick={handleUnjustify}
              color="warning"
              variant="outlined"
              disabled={submitting}
            >
              Mark Unjustified
            </Button>
          )}
          <Button
            type="submit"
            form="justify-form"
            variant="contained"
            color="success"
            disabled={submitting}
          >
            {submitting ? 'Saving…' : 'Mark Justified'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
