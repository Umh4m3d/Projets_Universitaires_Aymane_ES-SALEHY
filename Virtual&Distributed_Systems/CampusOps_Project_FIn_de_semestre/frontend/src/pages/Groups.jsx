import { useState } from 'react'
import {
  Box, Typography, Card, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Skeleton, Button,
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Grid, Alert,
} from '@mui/material'
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined'
import { useApi } from '../hooks/useApi'
import api from '../api/client'

export default function Groups() {
  const { data: groups, loading, error, refetch } = useApi('/groups/')
  const [open, setOpen]             = useState(false)
  const [formError, setFormError]   = useState(null)
  const [success, setSuccess]       = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({ name: '', description: '' })

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleClose = () => {
    setOpen(false)
    setFormError(null)
    setForm({ name: '', description: '' })
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      await api.post('/groups/', { name: form.name.trim(), description: form.description.trim() })
      setSuccess('Group created successfully.')
      handleClose()
      refetch()
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create group')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h5">Groups</Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>Manage student groups</Typography>
        </Box>
        <Button variant="contained" startIcon={<AddCircleOutlinedIcon sx={{ fontSize: 18 }} />} onClick={() => setOpen(true)}>
          New Group
        </Button>
      </Box>

      {success && <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 3 }}>{success}</Alert>}
      {error   && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Description</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                [1, 2, 3].map((k) => (
                  <TableRow key={k}>
                    <TableCell><Skeleton height={20} /></TableCell>
                    <TableCell><Skeleton height={20} /></TableCell>
                  </TableRow>
                ))
              ) : !groups?.length ? (
                <TableRow>
                  <TableCell colSpan={2} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                    No groups yet. Click "New Group" to create one.
                  </TableCell>
                </TableRow>
              ) : (
                groups.map((g) => (
                  <TableRow key={g.id} hover>
                    <TableCell sx={{ fontWeight: 500 }}>{g.name}</TableCell>
                    <TableCell sx={{ color: 'text.secondary' }}>{g.description || '—'}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Create Group</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          {formError && <Alert severity="error" sx={{ mb: 2 }}>{formError}</Alert>}
          <Box component="form" id="group-form" onSubmit={handleCreate}>
            <Grid container spacing={2} sx={{ mt: 0 }}>
              <Grid item xs={12}>
                <TextField label="Group name" value={form.name} onChange={set('name')} fullWidth required placeholder="e.g. Group A" />
              </Grid>
              <Grid item xs={12}>
                <TextField label="Description (optional)" value={form.description} onChange={set('description')} fullWidth placeholder="e.g. First-year morning group" />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleClose} variant="outlined">Cancel</Button>
          <Button type="submit" form="group-form" variant="contained" disabled={submitting}>
            {submitting ? 'Creating…' : 'Create Group'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
