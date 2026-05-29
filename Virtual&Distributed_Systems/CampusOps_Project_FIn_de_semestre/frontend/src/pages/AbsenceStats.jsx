import { useState, useMemo } from 'react'
import {
  Box, Typography, Card, CardContent, Grid, TextField,
  MenuItem, Button, Alert, Skeleton, Chip, Divider,
} from '@mui/material'
import PeopleOutlinedIcon     from '@mui/icons-material/PeopleOutlined'
import CheckCircleOutlinedIcon from '@mui/icons-material/CheckCircleOutlined'
import CancelOutlinedIcon      from '@mui/icons-material/CancelOutlined'
import { useApi } from '../hooks/useApi'
import api from '../api/client'

export default function AbsenceStats() {
  const { data: groups }   = useApi('/groups/')
  const { data: allStudents } = useApi('/users/students')

  const [filters, setFilters] = useState({ student_id: '', group_id: '', date_from: '', date_to: '' })
  const [stats, setStats]     = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  // When a group is selected, only show students in that group
  const filteredStudents = useMemo(() => {
    if (!allStudents) return []
    if (!filters.group_id) return allStudents
    // We rely on the backend /users/students?group_id= endpoint
    // but since we already have allStudents we need to filter client-side
    // OR: we re-fetch when group changes. Using a simple approach:
    return allStudents // will be updated by the group-aware fetch below
  }, [allStudents, filters.group_id])

  // Separate fetch for students filtered by group
  const { data: groupStudents } = useApi(
    filters.group_id ? `/users/students?group_id=${filters.group_id}` : '/users/students'
  )
  const studentOptions = groupStudents || []

  const set = (field) => (e) => {
    const value = e.target.value
    setFilters((f) => {
      const next = { ...f, [field]: value }
      // When student is selected, auto-fill group from student profile
      if (field === 'student_id' && value) {
        const student = (allStudents || []).find((s) => s.id === value)
        // We don't have group on user object here, so just clear student when group changes
      }
      // When group changes, reset student selection
      if (field === 'group_id') {
        next.student_id = ''
      }
      return next
    })
  }

  const handleFetch = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (filters.student_id) params.append('student_id', filters.student_id)
      if (filters.group_id)   params.append('group_id',   filters.group_id)
      if (filters.date_from)  params.append('date_from',  filters.date_from)
      if (filters.date_to)    params.append('date_to',    filters.date_to)
      const { data } = await api.get(`/absences/stats?${params}`)
      setStats(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load statistics')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFilters({ student_id: '', group_id: '', date_from: '', date_to: '' })
    setStats(null)
    setError(null)
  }

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">Absence Statistics</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          Filter by student, group, or date range to generate a report
        </Typography>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Grid container spacing={2} alignItems="flex-end">

            {/* Group first — filters the student list */}
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                select
                label="Group"
                value={filters.group_id}
                onChange={set('group_id')}
                fullWidth
              >
                <MenuItem value="">All groups</MenuItem>
                {(groups || []).map((g) => (
                  <MenuItem key={g.id} value={g.id}>{g.name}</MenuItem>
                ))}
              </TextField>
            </Grid>

            {/* Student — only shows students in selected group (or all if no group) */}
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                select
                label="Student"
                value={filters.student_id}
                onChange={set('student_id')}
                fullWidth
              >
                <MenuItem value="">All students</MenuItem>
                {studentOptions.map((s) => (
                  <MenuItem key={s.id} value={s.id}>{s.full_name}</MenuItem>
                ))}
              </TextField>
            </Grid>

            <Grid item xs={12} sm={6} md={2}>
              <TextField
                label="From date"
                type="date"
                value={filters.date_from}
                onChange={set('date_from')}
                fullWidth
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                label="To date"
                type="date"
                value={filters.date_to}
                onChange={set('date_to')}
                fullWidth
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>

            <Grid item xs={12} md={2}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  onClick={handleFetch}
                  disabled={loading}
                  fullWidth
                >
                  {loading ? 'Loading…' : 'Generate'}
                </Button>
                <Button variant="outlined" onClick={handleReset} disabled={loading}>
                  Reset
                </Button>
              </Box>
            </Grid>

          </Grid>
        </CardContent>
      </Card>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* Results */}
      {loading && (
        <Grid container spacing={3}>
          {[1, 2, 3].map((k) => (
            <Grid item xs={12} sm={4} key={k}>
              <Skeleton height={100} />
            </Grid>
          ))}
        </Grid>
      )}

      {stats && !loading && (
        <>
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent sx={{ p: 3, textAlign: 'center' }}>
                  <PeopleOutlinedIcon sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>{stats.total}</Typography>
                  <Typography variant="body2">Total Absences</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent sx={{ p: 3, textAlign: 'center' }}>
                  <CheckCircleOutlinedIcon sx={{ fontSize: 32, color: 'success.main', mb: 1 }} />
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main' }}>{stats.justified}</Typography>
                  <Typography variant="body2">Justified</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent sx={{ p: 3, textAlign: 'center' }}>
                  <CancelOutlinedIcon sx={{ fontSize: 32, color: 'error.main', mb: 1 }} />
                  <Typography variant="h4" sx={{ fontWeight: 700, color: 'error.main' }}>{stats.unjustified}</Typography>
                  <Typography variant="body2">Unjustified</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {stats.per_student?.length > 0 && (
            <Card>
              <CardContent sx={{ p: 0 }}>
                <Box sx={{ px: 3, py: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="h6">Breakdown by Student</Typography>
                </Box>
                {stats.per_student.map((s, i) => (
                  <Box key={s.student_id}>
                    {i > 0 && <Divider />}
                    <Box sx={{ px: 3, py: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Typography sx={{ fontWeight: 500, fontSize: '0.875rem' }}>{s.student_name}</Typography>
                      <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
                        <Chip label={`${s.total} total`} size="small" />
                        <Chip label={`${s.justified} justified`} size="small" color="success" />
                        <Chip label={`${s.unjustified} unjustified`} size="small" color="error" />
                      </Box>
                    </Box>
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}

          {stats.total === 0 && (
            <Card sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                No absences found for the selected filters.
              </Typography>
            </Card>
          )}
        </>
      )}
    </Box>
  )
}
