import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import {
  Box, TextField, Button, Typography, Alert,
  InputAdornment, IconButton,
} from '@mui/material'
import LockOutlinedIcon          from '@mui/icons-material/LockOutlined'
import VisibilityOutlinedIcon    from '@mui/icons-material/VisibilityOutlined'
import VisibilityOffOutlinedIcon from '@mui/icons-material/VisibilityOffOutlined'
import api from '../api/client'

export default function ResetPassword() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const token = params.get('token')

  const [password, setPassword]     = useState('')
  const [showPass, setShowPass]     = useState(false)
  const [loading, setLoading]       = useState(false)
  const [success, setSuccess]       = useState(false)
  const [error, setError]           = useState(null)

  if (!token) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Alert severity="error">Invalid or missing reset token. <Link to="/forgot-password">Request a new link.</Link></Alert>
      </Box>
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await api.post('/auth/reset-password', { token, new_password: password })
      setSuccess(true)
      setTimeout(() => navigate('/login'), 3000)
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(Array.isArray(detail) ? detail.map((d) => d.msg).join(', ') : detail || 'Failed to reset password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', bgcolor: '#F8FAFC' }}>
      <Box sx={{ display: { xs: 'none', md: 'flex' }, flex: 1, bgcolor: '#0F172A', flexDirection: 'column', justifyContent: 'center', px: 8 }}>
        <Typography variant="h4" sx={{ color: '#F8FAFC', mb: 2 }}>CampusOps</Typography>
        <Typography sx={{ color: '#64748B', fontSize: '1rem', lineHeight: 1.7, maxWidth: 360 }}>
          Choose a strong new password. It must have at least 8 characters, one uppercase letter, and one number.
        </Typography>
      </Box>

      <Box sx={{ flex: { xs: 1, md: '0 0 420px' }, display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
        <Box sx={{ width: '100%', maxWidth: 360 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 4 }}>
            <Box sx={{ width: 40, height: 40, borderRadius: 2, bgcolor: 'primary.main', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <LockOutlinedIcon sx={{ color: '#fff', fontSize: 20 }} />
            </Box>
            <Box>
              <Typography variant="h6" sx={{ lineHeight: 1.2 }}>Set new password</Typography>
              <Typography variant="body2">Enter your new password below</Typography>
            </Box>
          </Box>

          {success ? (
            <Alert severity="success">
              Password reset successfully! Redirecting to login…
            </Alert>
          ) : (
            <>
              {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
              <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  label="New password"
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required fullWidth
                  autoComplete="new-password"
                  helperText="Min 8 chars, 1 uppercase, 1 number"
                  slotProps={{
                    input: {
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton onClick={() => setShowPass((s) => !s)} edge="end" size="small">
                            {showPass ? <VisibilityOffOutlinedIcon sx={{ fontSize: 18 }} /> : <VisibilityOutlinedIcon sx={{ fontSize: 18 }} />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    },
                  }}
                />
                <Button type="submit" variant="contained" fullWidth size="large" disabled={loading} sx={{ py: 1.25 }}>
                  {loading ? 'Resetting…' : 'Reset password'}
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
