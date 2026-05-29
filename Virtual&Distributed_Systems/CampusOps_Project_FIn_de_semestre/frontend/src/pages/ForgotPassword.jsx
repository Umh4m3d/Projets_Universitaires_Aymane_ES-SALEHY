import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Box, TextField, Button, Typography, Alert,
} from '@mui/material'
import LockOutlinedIcon from '@mui/icons-material/LockOutlined'
import api from '../api/client'

export default function ForgotPassword() {
  const [email, setEmail]     = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent]       = useState(false)
  const [error, setError]     = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await api.post('/auth/forgot-password', { email })
      setSent(true)
    } catch (err) {
      // Backend always returns 200 to prevent user enumeration.
      // Any real error here is a network issue.
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', bgcolor: '#F8FAFC' }}>
      <Box sx={{ display: { xs: 'none', md: 'flex' }, flex: 1, bgcolor: '#0F172A', flexDirection: 'column', justifyContent: 'center', px: 8 }}>
        <Typography variant="h4" sx={{ color: '#F8FAFC', mb: 2 }}>CampusOps</Typography>
        <Typography sx={{ color: '#64748B', fontSize: '1rem', lineHeight: 1.7, maxWidth: 360 }}>
          Enter your email address and we'll send you a reset link if an account exists.
        </Typography>
      </Box>

      <Box sx={{ flex: { xs: 1, md: '0 0 420px' }, display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
        <Box sx={{ width: '100%', maxWidth: 360 }}>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 4 }}>
            <Box sx={{ width: 40, height: 40, borderRadius: 2, bgcolor: 'primary.main', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <LockOutlinedIcon sx={{ color: '#fff', fontSize: 20 }} />
            </Box>
            <Box>
              <Typography variant="h6" sx={{ lineHeight: 1.2 }}>Forgot password</Typography>
              <Typography variant="body2">We'll email you a reset link</Typography>
            </Box>
          </Box>

          {sent ? (
            <Alert severity="success" sx={{ mb: 3 }}>
              If that email is registered, a reset link has been sent. Check your inbox.
            </Alert>
          ) : (
            <>
              {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
              <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  label="Email address"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  fullWidth
                  autoComplete="email"
                />
                <Button type="submit" variant="contained" fullWidth size="large" disabled={loading} sx={{ py: 1.25 }}>
                  {loading ? 'Sending…' : 'Send reset link'}
                </Button>
              </Box>
            </>
          )}

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2">
              <Link to="/login" style={{ color: '#2563EB', textDecoration: 'none', fontWeight: 500 }}>
                ← Back to login
              </Link>
            </Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  )
}
