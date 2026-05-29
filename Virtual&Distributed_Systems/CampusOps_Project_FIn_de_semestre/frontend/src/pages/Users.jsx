import { useState } from 'react'
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Skeleton,
  Button, Dialog, DialogTitle, DialogContent, DialogContentText,
  DialogActions, Alert,
} from '@mui/material'
import BlockOutlinedIcon  from '@mui/icons-material/BlockOutlined'
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined'
import CheckOutlinedIcon  from '@mui/icons-material/CheckOutlined'
import CloseOutlinedIcon  from '@mui/icons-material/CloseOutlined'
import { useApi } from '../hooks/useApi'
import api from '../api/client'
import { formatDate } from '../utils/date'

const ROLE_CHIP = {
  admin:     { color: 'error' },
  secretary: { color: 'secondary' },
}

export default function Users() {
  const { data, loading, refetch }                          = useApi('/users/staff')
  const { data: changeRequests, loading: crLoading,
          refetch: refetchCr }                              = useApi('/profile/pending-requests')
  const [confirm, setConfirm]                              = useState(null)
  const [actionError, setActionError]                      = useState(null)
  const [working, setWorking]                              = useState(false)
  const [reviewing, setReviewing]                          = useState(null)

  const handleDeactivate = async () => {
    setWorking(true)
    setActionError(null)
    try {
      await api.patch(`/users/${confirm.id}/deactivate`)
      setConfirm(null)
      refetch()
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to deactivate user')
      setConfirm(null)
    } finally {
      setWorking(false)
    }
  }

  const handleDelete = async () => {
    setWorking(true)
    setActionError(null)
    try {
      await api.delete(`/users/${confirm.id}`)
      setConfirm(null)
      refetch()
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to delete user')
      setConfirm(null)
    } finally {
      setWorking(false)
    }
  }

  const handleReview = async (id, action) => {
    setReviewing(id)
    setActionError(null)
    try {
      await api.patch(`/profile/${id}/review`, { action })
      refetchCr()
      if (action === 'approve') refetch()
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to review request')
    } finally {
      setReviewing(null)
    }
  }

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">Staff Accounts</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          Manage administrator and secretary accounts
        </Typography>
      </Box>

      {actionError && (
        <Alert
          severity={actionError.includes('own account') ? 'info' : 'error'}
          onClose={() => setActionError(null)}
          sx={{ mb: 3 }}
        >
          {actionError}
        </Alert>
      )}

      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Joined</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                [1, 2].map((k) => (
                  <TableRow key={k}>
                    {[1,2,3,4,5,6].map((i) => (
                      <TableCell key={i}><Skeleton height={20} /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : !data?.length ? (
                <TableRow>
                  <TableCell colSpan={6} align="center"
                    sx={{ py: 4, color: 'text.secondary' }}>
                    No staff accounts found.
                  </TableCell>
                </TableRow>
              ) : (
                data.map((u) => (
                  <TableRow key={u.id} hover>
                    <TableCell sx={{ fontWeight: 500 }}>{u.full_name}</TableCell>
                    <TableCell>{u.email}</TableCell>
                    <TableCell>
                      <Chip label={u.role} size="small"
                        color={ROLE_CHIP[u.role]?.color || 'default'}
                        sx={{ textTransform: 'capitalize' }} />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={u.is_active ? 'Active' : 'Inactive'}
                        size="small"
                        color={u.is_active ? 'success' : 'default'}
                        variant={u.is_active ? 'filled' : 'outlined'}
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(u.created_at).toLocaleDateString('en-GB', {
                        day: '2-digit', month: 'short', year: 'numeric',
                      })}
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        {u.is_active && (
                          <Button size="small" color="warning" variant="outlined"
                            startIcon={<BlockOutlinedIcon sx={{ fontSize: 14 }} />}
                            onClick={() => setConfirm({ ...u, action: 'deactivate' })}
                            sx={{ fontSize: '0.75rem', py: 0.5 }}>
                            Deactivate
                          </Button>
                        )}
                        <Button size="small" color="error" variant="outlined"
                          startIcon={<DeleteOutlinedIcon sx={{ fontSize: 14 }} />}
                          onClick={() => setConfirm({ ...u, action: 'delete' })}
                          sx={{ fontSize: '0.75rem', py: 0.5 }}>
                          Delete
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

      {/* Pending profile change requests */}
      {(crLoading || changeRequests?.length > 0) && (
        <Card sx={{ mt: 3 }}>
          <CardContent sx={{ p: 0 }}>
            <Box sx={{ px: 3, py: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
              <Typography variant="h6">Pending Profile Change Requests</Typography>
              <Typography variant="body2">
                Review and approve or reject user-requested changes
              </Typography>
            </Box>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>User</TableCell>
                    <TableCell>Field</TableCell>
                    <TableCell>Current value</TableCell>
                    <TableCell>Requested value</TableCell>
                    <TableCell>Submitted</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {crLoading ? (
                    [1, 2].map((k) => (
                      <TableRow key={k}>
                        {[1,2,3,4,5,6].map((i) => (
                          <TableCell key={i}><Skeleton height={20} /></TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : (
                    changeRequests.map((r) => (
                      <TableRow key={r.id} hover>
                        <TableCell>
                          <Typography sx={{ fontSize: '0.875rem', fontWeight: 500 }}>
                            {r.user_name}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                            {r.user_email}
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ textTransform: 'capitalize' }}>
                          {r.field.replace('_', ' ')}
                        </TableCell>
                        <TableCell sx={{ color: 'text.secondary', fontSize: '0.8rem' }}>
                          {r.old_value}
                        </TableCell>
                        <TableCell sx={{ fontWeight: 500 }}>{r.new_value}</TableCell>
                        <TableCell>{formatDate(r.created_at)}</TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                            <Button size="small" color="success" variant="outlined"
                              startIcon={<CheckOutlinedIcon sx={{ fontSize: 14 }} />}
                              disabled={reviewing === r.id}
                              onClick={() => handleReview(r.id, 'approve')}
                              sx={{ fontSize: '0.75rem', py: 0.5 }}>
                              Approve
                            </Button>
                            <Button size="small" color="error" variant="outlined"
                              startIcon={<CloseOutlinedIcon sx={{ fontSize: 14 }} />}
                              disabled={reviewing === r.id}
                              onClick={() => handleReview(r.id, 'reject')}
                              sx={{ fontSize: '0.75rem', py: 0.5 }}>
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
          </CardContent>
        </Card>
      )}

      {/* Confirmation dialog */}
      <Dialog open={!!confirm} onClose={() => setConfirm(null)} maxWidth="xs" fullWidth>
        <DialogTitle>
          {confirm?.action === 'delete' ? 'Delete account' : 'Deactivate account'}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {confirm?.action === 'delete' ? (
              <>
                Permanently delete <strong>{confirm?.full_name}</strong>?
                This cannot be undone. If they have linked records, deletion will be blocked.
              </>
            ) : (
              <>
                Deactivate <strong>{confirm?.full_name}</strong>?
                Their account will remain in the system but they will lose access immediately.
                You can re-enable them later by updating the database directly.
              </>
            )}
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setConfirm(null)} variant="outlined">Cancel</Button>
          <Button
            onClick={confirm?.action === 'delete' ? handleDelete : handleDeactivate}
            color="error"
            variant="contained"
            disabled={working}
          >
            {working
              ? 'Working…'
              : confirm?.action === 'delete' ? 'Delete permanently' : 'Deactivate'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
