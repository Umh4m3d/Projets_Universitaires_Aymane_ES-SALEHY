import { useState } from 'react'
import {
  Box, Typography, Card, CardContent, Chip, Divider,
  TextField, MenuItem, Button, Skeleton, Alert, ToggleButton, ToggleButtonGroup,
} from '@mui/material'
import AccessTimeOutlinedIcon from '@mui/icons-material/AccessTimeOutlined'
import RoomOutlinedIcon       from '@mui/icons-material/RoomOutlined'
import PersonOutlinedIcon     from '@mui/icons-material/PersonOutlined'
import GroupsOutlinedIcon     from '@mui/icons-material/GroupsOutlined'
import CalendarTodayOutlinedIcon from '@mui/icons-material/CalendarTodayOutlined'
import api from '../api/client'
import { useApi } from '../hooks/useApi'

// Returns date range {from, to} based on a pivot date and view mode
function getDateRange(pivot, viewMode) {
  const d = new Date(pivot)
  if (viewMode === 'day') {
    const iso = d.toISOString().split('T')[0]
    return { from: iso, to: iso }
  }
  if (viewMode === 'week') {
    // Monday → Sunday
    const day = d.getDay() // 0=Sun
    const diffToMon = (day === 0 ? -6 : 1 - day)
    const mon = new Date(d)
    mon.setDate(d.getDate() + diffToMon)
    const sun = new Date(mon)
    sun.setDate(mon.getDate() + 6)
    return {
      from: mon.toISOString().split('T')[0],
      to:   sun.toISOString().split('T')[0],
    }
  }
  if (viewMode === 'month') {
    const from = new Date(d.getFullYear(), d.getMonth(), 1)
    const to   = new Date(d.getFullYear(), d.getMonth() + 1, 0)
    return {
      from: from.toISOString().split('T')[0],
      to:   to.toISOString().split('T')[0],
    }
  }
  return {}
}

function formatNavLabel(pivot, viewMode) {
  const d = new Date(pivot)
  if (viewMode === 'day') {
    return d.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
  }
  if (viewMode === 'week') {
    const { from, to } = getDateRange(pivot, 'week')
    const f = new Date(from + 'T00:00:00')
    const t = new Date(to   + 'T00:00:00')
    return `${f.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })} – ${t.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}`
  }
  if (viewMode === 'month') {
    return d.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
  }
  return ''
}

function navigatePivot(pivot, viewMode, direction) {
  const d = new Date(pivot)
  if (viewMode === 'day') {
    d.setDate(d.getDate() + direction)
  } else if (viewMode === 'week') {
    d.setDate(d.getDate() + direction * 7)
  } else if (viewMode === 'month') {
    d.setMonth(d.getMonth() + direction)
  }
  return d.toISOString().split('T')[0]
}

export default function Planning() {
  const { data: groups }   = useApi('/groups/')
  const { data: teachers } = useApi('/users/teachers')
  const { data: students } = useApi('/users/students')

  const [mode, setMode]         = useState('group')     // 'group' | 'teacher' | 'student'
  const [selected, setSelected] = useState('')
  const [sessions, setSessions] = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  // Time navigation
  const today = new Date().toISOString().split('T')[0]
  const [viewMode, setViewMode] = useState('week')  // 'day' | 'week' | 'month'
  const [pivot, setPivot]       = useState(today)

  const handleFetch = async (overrideSelected, overridePivot, overrideView) => {
    const sel  = overrideSelected ?? selected
    const piv  = overridePivot    ?? pivot
    const view = overrideView     ?? viewMode
    if (!sel) return
    setLoading(true)
    setError(null)
    setSessions(null)
    try {
      const endpointMap = {
        group:   `/sessions/by-group/${sel}`,
        teacher: `/sessions/by-teacher/${sel}`,
        student: `/sessions/by-student/${sel}`,
      }
      const { from, to } = getDateRange(piv, view)
      const params = new URLSearchParams()
      if (from) params.append('date_from', from)
      if (to)   params.append('date_to',   to)
      const { data } = await api.get(`${endpointMap[mode]}?${params}`)
      setSessions(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load sessions')
    } finally {
      setLoading(false)
    }
  }

  const handleNavigate = (direction) => {
    const newPivot = navigatePivot(pivot, viewMode, direction)
    setPivot(newPivot)
    if (selected) handleFetch(selected, newPivot, viewMode)
  }

  const handleViewModeChange = (_, newView) => {
    if (!newView) return
    setViewMode(newView)
    setPivot(today)
    if (selected) handleFetch(selected, today, newView)
  }

  // Group sessions by date for display
  const grouped = (sessions || []).reduce((acc, s) => {
    acc[s.date] = acc[s.date] || []
    acc[s.date].push(s)
    return acc
  }, {})

  const optionMap = {
    group:   groups   || [],
    teacher: teachers || [],
    student: students || [],
  }
  const labelMap = {
    group:   (x) => x.name,
    teacher: (x) => x.full_name,
    student: (x) => x.full_name,
  }

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">Planning</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          View sessions by group, teacher, or student
        </Typography>
      </Box>

      {/* Filter bar */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <TextField
              select
              label="View by"
              value={mode}
              onChange={(e) => { setMode(e.target.value); setSelected(''); setSessions(null) }}
              sx={{ minWidth: 160 }}
            >
              <MenuItem value="group">Group</MenuItem>
              <MenuItem value="teacher">Teacher</MenuItem>
              <MenuItem value="student">Student</MenuItem>
            </TextField>

            <TextField
              select
              label={mode.charAt(0).toUpperCase() + mode.slice(1)}
              value={selected}
              onChange={(e) => { setSelected(e.target.value); handleFetch(e.target.value, pivot, viewMode) }}
              sx={{ minWidth: 220 }}
              disabled={!optionMap[mode].length}
            >
              {optionMap[mode].map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {labelMap[mode](item)}
                </MenuItem>
              ))}
            </TextField>

            <Button
              variant="contained"
              onClick={() => handleFetch()}
              disabled={!selected || loading}
            >
              {loading ? 'Loading…' : 'Show Planning'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Time navigation bar */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>

            {/* View mode toggle */}
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={handleViewModeChange}
              size="small"
            >
              <ToggleButton value="day">Day</ToggleButton>
              <ToggleButton value="week">Week</ToggleButton>
              <ToggleButton value="month">Month</ToggleButton>
            </ToggleButtonGroup>

            {/* Prev / Label / Next */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Button
                variant="outlined"
                size="small"
                onClick={() => handleNavigate(-1)}
                sx={{ minWidth: 32, px: 1 }}
              >
                ‹
              </Button>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                <CalendarTodayOutlinedIcon sx={{ fontSize: 15, color: 'text.secondary' }} />
                <Typography variant="body2" sx={{ fontWeight: 600, minWidth: 200, textAlign: 'center' }}>
                  {formatNavLabel(pivot, viewMode)}
                </Typography>
              </Box>
              <Button
                variant="outlined"
                size="small"
                onClick={() => handleNavigate(1)}
                sx={{ minWidth: 32, px: 1 }}
              >
                ›
              </Button>
              <Button
                size="small"
                variant="text"
                onClick={() => {
                  setPivot(today)
                  if (selected) handleFetch(selected, today, viewMode)
                }}
                disabled={pivot === today}
                sx={{ ml: 1 }}
              >
                Today
              </Button>
            </Box>

            {/* Current range chip */}
            <Chip
              size="small"
              label={(() => {
                const { from, to } = getDateRange(pivot, viewMode)
                if (from === to) return from
                return `${from} → ${to}`
              })()}
              variant="outlined"
              sx={{ fontSize: '0.7rem' }}
            />
          </Box>
        </CardContent>
      </Card>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {loading && [1, 2].map((k) => (
        <Skeleton key={k} height={120} sx={{ mb: 2, borderRadius: 2 }} />
      ))}

      {sessions !== null && !loading && Object.keys(grouped).length === 0 && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              No approved sessions found for this selection.
            </Typography>
          </CardContent>
        </Card>
      )}

      {Object.entries(grouped).sort().map(([date, dateSessions]) => (
        <Box key={date} sx={{ mb: 3 }}>
          <Typography sx={{
            fontSize: '0.7rem', fontWeight: 700, color: 'text.secondary',
            textTransform: 'uppercase', letterSpacing: '0.08em', mb: 1.5,
          }}>
            {new Date(date + 'T00:00:00').toLocaleDateString('en-GB', {
              weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
            })}
          </Typography>
          <Card>
            <CardContent sx={{ p: '0 !important' }}>
              {dateSessions.map((s, i) => (
                <Box key={s.id}>
                  {i > 0 && <Divider />}
                  <Box sx={{ px: 2.5, py: 2, display: 'flex', alignItems: 'center', gap: 3 }}>
                    {/* Time */}
                    <Box sx={{ minWidth: 80, textAlign: 'center', flexShrink: 0 }}>
                      <Typography sx={{ fontSize: '1rem', fontWeight: 700, color: 'primary.main', lineHeight: 1 }}>
                        {s.start_time?.slice(0, 5)}
                      </Typography>
                      <Typography variant="caption">– {s.end_time?.slice(0, 5)}</Typography>
                    </Box>
                    <Divider orientation="vertical" flexItem />
                    {/* Info */}
                    <Box sx={{ flex: 1 }}>
                      <Typography sx={{ fontWeight: 600, fontSize: '0.875rem', mb: 0.75 }}>
                        {s.course_name}
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <RoomOutlinedIcon sx={{ fontSize: 13, color: 'text.secondary' }} />
                          <Typography variant="body2">{s.room}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <PersonOutlinedIcon sx={{ fontSize: 13, color: 'text.secondary' }} />
                          <Typography variant="body2">{s.teacher_name}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <GroupsOutlinedIcon sx={{ fontSize: 13, color: 'text.secondary' }} />
                          <Typography variant="body2">{s.group_name}</Typography>
                        </Box>
                      </Box>
                    </Box>
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Box>
      ))}
    </Box>
  )
}
