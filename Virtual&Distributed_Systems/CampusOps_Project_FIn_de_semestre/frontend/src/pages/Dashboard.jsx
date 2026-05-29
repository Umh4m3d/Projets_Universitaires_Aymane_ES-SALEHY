import { useLocation } from 'react-router-dom'
import {
  Box, Grid, Card, CardContent, Typography,
  Alert, Divider, Chip, Skeleton,
} from '@mui/material'
import CalendarTodayOutlinedIcon from '@mui/icons-material/CalendarTodayOutlined'
import NotificationsNoneOutlinedIcon from '@mui/icons-material/NotificationsNoneOutlined'
import AccessTimeOutlinedIcon from '@mui/icons-material/AccessTimeOutlined'
import RoomOutlinedIcon from '@mui/icons-material/RoomOutlined'
import { useAuth } from '../context/AuthContext'
import { useApi } from '../hooks/useApi'
import { formatDate } from '../utils/date'

const STATUS_COLOR = {
  pending: 'default',
  absence: 'error',
  payment_overdue: 'warning',
}

// ✅ NEW: Notification color mapping
const NOTIF_COLOR = {
  absence: 'error',
  payment_overdue: 'warning',
  session_request: 'info',
  session_approved: 'success',
  session_rejected: 'error',
}

// ✅ NEW: Notification label mapping
const NOTIF_LABEL = {
  absence: 'Absence',
  payment_overdue: 'Payment',
  session_request: 'New Request',
  session_approved: 'Approved',
  session_rejected: 'Rejected',
}

export default function Dashboard() {
  const { user } = useAuth()
  const location = useLocation()
  const wasDenied = location.state?.denied

  const { data: sessions, loading: sLoading } = useApi('/sessions/today')
  const { data: notifications, loading: nLoading } = useApi('/notifications/mine')

  return (
    <Box>
      {wasDenied && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          You do not have permission to access that page.
        </Alert>
      )}

      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">Dashboard</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          Welcome back, {user?.full_name}
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Today's sessions */}
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent sx={{ pb: '16px !important' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <CalendarTodayOutlinedIcon sx={{ fontSize: 18, color: 'primary.main' }} />
                <Typography variant="h6">Today's Sessions</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />

              {sLoading ? (
                [1, 2].map((k) => (
                  <Skeleton key={k} height={56} sx={{ mb: 1, borderRadius: 1 }} />
                ))
              ) : sessions?.length === 0 ? (
                <Typography variant="body2" sx={{ py: 2, textAlign: 'center' }}>
                  No sessions scheduled for today.
                </Typography>
              ) : (
                sessions?.map((s) => (
                  <Box
                    key={s.id}
                    sx={{
                      p: 1.5,
                      mb: 1,
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: 'divider',
                      bgcolor: '#FAFBFD',
                      '&:last-child': { mb: 0 },
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Typography sx={{ fontWeight: 600, fontSize: '0.875rem' }}>
                        {s.course_name}
                      </Typography>
                      <Chip label={s.group_name} size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                    </Box>

                    <Box sx={{ display: 'flex', gap: 2, mt: 0.75 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <AccessTimeOutlinedIcon sx={{ fontSize: 13, color: 'text.secondary' }} />
                        <Typography variant="body2">
                          {s.start_time?.slice(0, 5)} – {s.end_time?.slice(0, 5)}
                        </Typography>
                      </Box>

                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <RoomOutlinedIcon sx={{ fontSize: 13, color: 'text.secondary' }} />
                        <Typography variant="body2">{s.room}</Typography>
                      </Box>
                    </Box>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* ✅ UPDATED Notifications Panel */}
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent sx={{ pb: '16px !important' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <NotificationsNoneOutlinedIcon sx={{ fontSize: 18, color: 'primary.main' }} />
                <Typography variant="h6">Recent Notifications</Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />

              {nLoading ? (
                [1, 2, 3].map((k) => (
                  <Skeleton key={k} height={48} sx={{ mb: 1 }} />
                ))
              ) : notifications?.length === 0 ? (
                <Typography
                  variant="body2"
                  sx={{ py: 2, textAlign: 'center', color: 'text.secondary' }}
                >
                  No notifications.
                </Typography>
              ) : (
                notifications?.slice(0, 8).map((n) => (
                  <Box
                    key={n.id}
                    sx={{
                      py: 1.5,
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                      '&:last-child': { borderBottom: 'none' },
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 0.5 }}>
                      <Chip
                        label={NOTIF_LABEL[n.type] || n.type}
                        size="small"
                        color={NOTIF_COLOR[n.type] || 'default'}
                        sx={{ fontSize: '0.65rem', height: 18, flexShrink: 0 }}
                      />
                    </Box>

                    <Typography
                      sx={{ fontSize: '0.8rem', color: 'text.primary', lineHeight: 1.5 }}
                    >
                      {n.message}
                    </Typography>

                    <Typography
                      variant="caption"
                      sx={{ mt: 0.25, display: 'block', color: 'text.secondary' }}
                    >
                      {formatDate(n.created_at)}
                    </Typography>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
