// /src/pages/Profile.jsx
import { useState, useEffect, useCallback } from 'react'
import {
  Box, Typography, Card, CardContent, Grid, TextField,
  Button, Alert, Chip, Divider, Avatar, CircularProgress,
  Table, TableBody, TableCell, TableHead, TableRow, Dialog,
  DialogTitle, DialogContent, DialogActions,
} from '@mui/material'
import CheckCircleOutlinedIcon  from '@mui/icons-material/CheckCircleOutlined'
import AccessTimeOutlinedIcon   from '@mui/icons-material/AccessTimeOutlined'
import CancelOutlinedIcon       from '@mui/icons-material/CancelOutlined'
import SmartphoneOutlinedIcon   from '@mui/icons-material/SmartphoneOutlined'
import LockResetOutlinedIcon    from '@mui/icons-material/LockResetOutlined'
import EmailOutlinedIcon        from '@mui/icons-material/EmailOutlined'
import FamilyRestroomOutlinedIcon from '@mui/icons-material/FamilyRestroomOutlined'
import SchoolOutlinedIcon       from '@mui/icons-material/SchoolOutlined'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'
import { formatDate } from '../utils/date'

function getInitials(name) {
  if (!name) return '?'
  return name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()
}

function OtpTimer({ onExpire }) {
  const [seconds, setSeconds] = useState(300)
  useEffect(() => {
    if (seconds <= 0) { onExpire(); return }
    const id = setTimeout(() => setSeconds((s) => s - 1), 1000)
    return () => clearTimeout(id)
  }, [seconds, onExpire])
  const mins = Math.floor(seconds / 60)
  const secs = String(seconds % 60).padStart(2, '0')
  return (
    <Typography variant="caption" sx={{ color: seconds < 60 ? 'error.main' : 'text.secondary' }}>
      Expires in {mins}:{secs}
    </Typography>
  )
}

const REQUEST_CHIP = {
  pending:  { label: 'Pending',  color: 'warning' },
  approved: { label: 'Approved', color: 'success' },
  rejected: { label: 'Rejected', color: 'error'   },
}

export default function Profile() {
  const { user } = useAuth()
  const isStudent = user?.role === 'student'

  const [form, setForm] = useState({ full_name: '', email: '' })
  const [submitting, setSubmitting]     = useState(false)
  const [formError, setFormError]       = useState(null)
  const [formSuccess, setFormSuccess]   = useState(null)
  const [requests, setRequests]         = useState([])

  // Notification email
  const [notifEmail, setNotifEmail]       = useState('')
  const [notifSaving, setNotifSaving]     = useState(false)
  const [notifError, setNotifError]       = useState(null)
  const [notifSuccess, setNotifSuccess]   = useState(null)

  // Parent email (students only)
  const [parentEmail, setParentEmail]         = useState('')
  const [parentSaving, setParentSaving]       = useState(false)
  const [parentError, setParentError]         = useState(null)
  const [parentSuccess, setParentSuccess]     = useState(null)
  const [studentProfile, setStudentProfile]   = useState(null)

  // Telegram OTP
  const [otp, setOtp]               = useState(null)
  const [otpLoading, setOtpLoading] = useState(false)
  const [otpError, setOtpError]     = useState(null)
  const [otpExpired, setOtpExpired] = useState(false)

  // Reset password dialog
  const [resetOpen, setResetOpen]       = useState(false)
  const [resetLoading, setResetLoading] = useState(false)
  const [resetMsg, setResetMsg]         = useState(null)
  const [resetError, setResetError]     = useState(null)

  const loadRequests = useCallback(async () => {
    try {
      const { data } = await api.get('/profile/my-requests')
      setRequests(data)
    } catch (_) {}
  }, [])

  const loadStudentProfile = useCallback(async () => {
    if (!isStudent) return
    try {
      const { data } = await api.get('/profile/my-student-profile')
      if (data) {
        setStudentProfile(data)
        setParentEmail(data.parent_email || '')
      }
    } catch (_) {}
  }, [isStudent])

  useEffect(() => {
    if (user) {
      setForm({ full_name: user.full_name || '', email: user.email || '' })
      setNotifEmail(user.notification_email || '')
      loadRequests()
      loadStudentProfile()
    }
  }, [user, loadRequests, loadStudentProfile])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setFormSuccess(null)
    setSubmitting(true)
    try {
      await api.post('/profile/request-changes', {
        full_name: form.full_name !== user.full_name ? form.full_name : undefined,
        email: form.email !== user.email ? form.email : undefined,
      })
      setFormSuccess('Your change request has been submitted and is pending admin approval.')
      loadRequests()
    } catch (err) {
      const detail = err.response?.data?.detail
      setFormError(typeof detail === 'string' ? detail : 'Failed to submit request')
    } finally {
      setSubmitting(false)
    }
  }

  const handleSaveNotifEmail = async () => {
    setNotifSaving(true)
    setNotifError(null)
    setNotifSuccess(null)
    try {
      await api.patch('/profile/notification-email', { notification_email: notifEmail.trim() || null })
      setNotifSuccess('Notification email saved successfully.')
    } catch (err) {
      const detail = err.response?.data?.detail
      setNotifError(typeof detail === 'string' ? detail : 'Failed to save email')
    } finally {
      setNotifSaving(false)
    }
  }

  const handleSaveParentEmail = async () => {
    setParentSaving(true)
    setParentError(null)
    setParentSuccess(null)
    try {
      await api.patch('/profile/parent-email', { parent_email: parentEmail.trim() || null })
      setParentSuccess('Parent email saved successfully.')
      loadStudentProfile()
    } catch (err) {
      const detail = err.response?.data?.detail
      setParentError(typeof detail === 'string' ? detail : 'Failed to save parent email')
    } finally {
      setParentSaving(false)
    }
  }

  const handleResetPassword = async () => {
    setResetLoading(true)
    setResetMsg(null)
    setResetError(null)
    try {
      await api.post('/auth/forgot-password', { email: user.email })
      const emailToUse = notifEmail.trim() || user.email
      setResetMsg(`A password reset link has been sent to ${emailToUse}. Check your inbox.`)
    } catch (err) {
      setResetError(err.response?.data?.detail || 'Failed to send reset email')
    } finally {
      setResetLoading(false)
    }
  }

  const generateOtp = async () => {
    setOtpLoading(true)
    setOtpError(null)
    setOtp(null)
    setOtpExpired(false)
    try {
      const { data } = await api.post('/auth/telegram-otp')
      setOtp(data.otp)
    } catch (err) {
      setOtpError(err.response?.data?.detail || 'Failed to generate code')
    } finally {
      setOtpLoading(false)
    }
  }

  return (
    <Box sx={{ maxWidth: 720 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">My Profile</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>View your account details and request changes</Typography>
      </Box>

      {/* Identity card */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2.5, p: 3, flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2.5 }}>
            <Avatar sx={{ width: 56, height: 56, bgcolor: 'primary.main', fontSize: '1.1rem', fontWeight: 700 }}>
              {getInitials(user?.full_name)}
            </Avatar>
            <Box>
              <Typography variant="h6">{user?.full_name}</Typography>
              <Typography variant="body2">{user?.email}</Typography>
              <Chip
                label={user?.role}
                size="small"
                color={{ admin: 'error', secretary: 'secondary', teacher: 'primary', student: 'success' }[user?.role] || 'default'}
                sx={{ mt: 0.5, fontWeight: 600, fontSize: '0.7rem' }}
              />
            </Box>
          </Box>
          <Button
            variant="outlined"
            color="warning"
            startIcon={<LockResetOutlinedIcon />}
            onClick={() => { setResetOpen(true); setResetMsg(null); setResetError(null) }}
            size="small"
          >
            Reset Password
          </Button>
        </CardContent>
      </Card>

      {/* Student profile info (students only) */}
      {isStudent && studentProfile && (
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <SchoolOutlinedIcon sx={{ fontSize: 18, color: 'primary.main' }} />
              <Typography variant="h6">Academic Info</Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              <Box>
                <Typography variant="caption" color="text.secondary">Establishment</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{studentProfile.establishment}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Group</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{studentProfile.group_name || '—'}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Year</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>Year {studentProfile.year}</Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Notification email card */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <EmailOutlinedIcon sx={{ fontSize: 18, color: 'primary.main' }} />
            <Typography variant="h6">Notification Email</Typography>
          </Box>
          <Typography variant="body2" sx={{ mb: 2.5 }}>
            Since your platform email may be a placeholder, enter a real email address here to receive
            absence alerts, payment reminders, and password reset links.
          </Typography>

          {notifSuccess && <Alert severity="success" sx={{ mb: 2 }}>{notifSuccess}</Alert>}
          {notifError   && <Alert severity="error"   sx={{ mb: 2 }}>{notifError}</Alert>}

          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
            <TextField
              label="Your real email address"
              type="email"
              value={notifEmail}
              onChange={(e) => setNotifEmail(e.target.value)}
              placeholder="e.g. yourname@gmail.com"
              fullWidth
              size="small"
              helperText="Used for notifications and password resets. Not your login email."
            />
            <Button
              variant="contained"
              onClick={handleSaveNotifEmail}
              disabled={notifSaving}
              sx={{ mt: 0.25, flexShrink: 0 }}
            >
              {notifSaving ? 'Saving…' : 'Save'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Parent / Guardian email card (students only) */}
      {isStudent && (
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <FamilyRestroomOutlinedIcon sx={{ fontSize: 18, color: 'primary.main' }} />
              <Typography variant="h6">Parent / Guardian Email</Typography>
            </Box>
            <Typography variant="body2" sx={{ mb: 2.5 }}>
              Add your parent or guardian's email so they receive absence and payment
              notifications on your behalf.
            </Typography>

            {parentSuccess && <Alert severity="success" sx={{ mb: 2 }}>{parentSuccess}</Alert>}
            {parentError   && <Alert severity="error"   sx={{ mb: 2 }}>{parentError}</Alert>}

            {!studentProfile && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Your student profile hasn't been created yet. Ask your secretary to create it first.
              </Alert>
            )}

            <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
              <TextField
                label="Parent / guardian email"
                type="email"
                value={parentEmail}
                onChange={(e) => setParentEmail(e.target.value)}
                placeholder="e.g. parent@gmail.com"
                fullWidth
                size="small"
                disabled={!studentProfile}
                helperText={
                  parentEmail
                    ? 'Your parent/guardian will receive absence and payment alerts.'
                    : 'Leave blank to remove the parent email.'
                }
              />
              <Button
                variant="contained"
                onClick={handleSaveParentEmail}
                disabled={parentSaving || !studentProfile}
                sx={{ mt: 0.25, flexShrink: 0 }}
              >
                {parentSaving ? 'Saving…' : 'Save'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Edit form — request profile changes */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 0.5 }}>Request Profile Changes</Typography>
          <Typography variant="body2" sx={{ mb: 2.5 }}>
            Changes to your name or platform email require admin approval before taking effect.
          </Typography>

          {formSuccess && <Alert severity="success" sx={{ mb: 2.5 }}>{formSuccess}</Alert>}
          {formError   && <Alert severity="error"   sx={{ mb: 2.5 }}>{formError}</Alert>}

          <Box component="form" onSubmit={handleSubmit}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Full name"
                  value={form.full_name}
                  onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Platform email address"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12}>
                <Button type="submit" variant="contained" disabled={submitting} sx={{ px: 4 }}>
                  {submitting ? 'Submitting…' : 'Submit for approval'}
                </Button>
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>

      {/* Pending change requests */}
      {requests.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Recent Change Requests</Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Field</TableCell>
                  <TableCell>Requested Value</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Submitted</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {requests.map((r) => {
                  const chip = REQUEST_CHIP[r.status] || REQUEST_CHIP.pending
                  return (
                    <TableRow key={r.id}>
                      <TableCell sx={{ textTransform: 'capitalize' }}>{r.field.replace('_', ' ')}</TableCell>
                      <TableCell>{r.new_value}</TableCell>
                      <TableCell><Chip label={chip.label} color={chip.color} size="small" /></TableCell>
                      <TableCell>{formatDate(r.created_at)}</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Telegram link */}
      <Card>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <SmartphoneOutlinedIcon sx={{ fontSize: 18, color: 'primary.main' }} />
            <Typography variant="h6">Telegram Integration</Typography>
          </Box>
          <Typography variant="body2" sx={{ mb: 2.5 }}>
            Link your account to receive absence and payment notifications directly via Telegram.
            Generate a code below and send it to the bot using <code>/link YOUR_CODE</code>.
          </Typography>

          {otpError && <Alert severity="error" sx={{ mb: 2 }}>{otpError}</Alert>}

          {otp && !otpExpired ? (
            <Box sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, p: 2.5, bgcolor: '#FAFBFD' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>Your link code</Typography>
                <OtpTimer onExpire={() => setOtpExpired(true)} />
              </Box>
              <Typography sx={{ fontSize: '2rem', fontWeight: 700, letterSpacing: '0.25em', color: 'primary.main', fontFamily: 'monospace', mb: 1.5 }}>
                {otp}
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Open Telegram, find your bot, and send: <strong>/link {otp}</strong>
              </Typography>
              <Button size="small" variant="outlined" onClick={generateOtp} disabled={otpLoading}>
                Generate new code
              </Button>
            </Box>
          ) : otpExpired ? (
            <Alert severity="warning" action={<Button size="small" onClick={generateOtp} disabled={otpLoading}>Regenerate</Button>}>
              Your code expired.
            </Alert>
          ) : (
            <Button variant="outlined" onClick={generateOtp} disabled={otpLoading} startIcon={otpLoading ? <CircularProgress size={14} /> : null}>
              {otpLoading ? 'Generating…' : 'Generate link code'}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Reset Password dialog */}
      <Dialog open={resetOpen} onClose={() => setResetOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Reset Password</DialogTitle>
        <DialogContent>
          {resetMsg ? (
            <Alert severity="success">{resetMsg}</Alert>
          ) : (
            <>
              <Typography variant="body2" sx={{ mb: 2 }}>
                A reset link will be sent to:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 2 }}>
                {notifEmail.trim() ? notifEmail.trim() : user?.email}
              </Typography>
              {!notifEmail.trim() && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  You haven't set a notification email. The reset link will go to your platform
                  email ({user?.email}), which may be a placeholder.
                </Alert>
              )}
              {resetError && <Alert severity="error">{resetError}</Alert>}
            </>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setResetOpen(false)} variant="outlined">Cancel</Button>
          {!resetMsg && (
            <Button onClick={handleResetPassword} variant="contained" color="warning" disabled={resetLoading}>
              {resetLoading ? 'Sending…' : 'Send Reset Link'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  )
}
