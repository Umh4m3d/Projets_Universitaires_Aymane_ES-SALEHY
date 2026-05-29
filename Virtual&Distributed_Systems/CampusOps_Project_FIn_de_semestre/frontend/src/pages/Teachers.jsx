import { useState } from 'react'
import {
  Box, Typography, Card, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Skeleton,
  Button, Dialog, DialogTitle, DialogContent,
  DialogContentText, DialogActions, Alert,
} from '@mui/material'
import BlockOutlinedIcon  from '@mui/icons-material/BlockOutlined'
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined'
import { useApi } from '../hooks/useApi'
import api from '../api/client'

export default function Teachers() {
  const { data, loading, refetch } = useApi('/users/teachers')
  const [confirm, setConfirm]      = useState(null)
  const [actionError, setActionError] = useState(null)
  const [working, setWorking]      = useState(false)

  const handleDeactivate = async () => {
    setWorking(true)
    setActionError(null)
    try {
      await api.patch(`/users/${confirm.id}/deactivate`)
      setConfirm(null)
      refetch()
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to deactivate')
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
      setActionError(err.response?.data?.detail || 'Failed to delete')
      setConfirm(null)
    } finally {
      setWorking(false)
    }
  }

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">Teachers</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          Manage teacher accounts and their access
        </Typography>
      </Box>

      {actionError && (
        <Alert severity="error" onClose={() => setActionError(null)} sx={{ mb: 3 }}>
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
                <TableCell>Status</TableCell>
                <TableCell>Joined</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                [1, 2, 3].map((k) => (
                  <TableRow key={k}>
                    {[1,2,3,4,5].map((i) => (
                      <TableCell key={i}><Skeleton height={20} /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : !data?.length ? (
                <TableRow>
                  <TableCell colSpan={5} align="center"
                    sx={{ py: 4, color: 'text.secondary' }}>
                    No teachers found.
                  </TableCell>
                </TableRow>
              ) : (
                data.map((u) => (
                  <TableRow key={u.id} hover>
                    <TableCell sx={{ fontWeight: 500 }}>{u.full_name}</TableCell>
                    <TableCell>{u.email}</TableCell>
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

      <Dialog open={!!confirm} onClose={() => setConfirm(null)} maxWidth="xs" fullWidth>
        <DialogTitle>
          {confirm?.action === 'delete' ? 'Delete teacher' : 'Deactivate teacher'}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {confirm?.action === 'delete' ? (
              <>
                Permanently delete <strong>{confirm?.full_name}</strong>?
                This will fail if they have existing sessions.
              </>
            ) : (
              <>
                Deactivate <strong>{confirm?.full_name}</strong>?
                Their sessions remain but they cannot log in.
              </>
            )}
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setConfirm(null)} variant="outlined">Cancel</Button>
          <Button
            onClick={confirm?.action === 'delete' ? handleDelete : handleDeactivate}
            color="error" variant="contained" disabled={working}
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
