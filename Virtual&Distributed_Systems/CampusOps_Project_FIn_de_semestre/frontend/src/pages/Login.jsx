import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, TextField, Button,
  Typography, Alert, InputAdornment, IconButton,
} from '@mui/material'
import VisibilityOutlinedIcon    from '@mui/icons-material/VisibilityOutlined'
import VisibilityOffOutlinedIcon from '@mui/icons-material/VisibilityOffOutlined'
import LockOutlinedIcon          from '@mui/icons-material/LockOutlined'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [error, setError]       = useState(null)
  const [loading, setLoading]   = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(
        Array.isArray(detail)
          ? detail.map((d) => d.msg).join(', ')
          : detail || 'Invalid credentials'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', bgcolor: '#F8FAFC' }}>

      {/* Left panel */}
      <Box
        sx={{
          display: { xs: 'none', md: 'flex' },
          flex: 1,
          bgcolor: '#0F172A',
          flexDirection: 'column',
          justifyContent: 'center',
          px: 8,
        }}
      >
        <Typography variant="h4" sx={{ color: '#F8FAFC', mb: 2 }}>
          CampusOps
        </Typography>
        <Typography sx={{ color: '#64748B', fontSize: '1rem', lineHeight: 1.7, maxWidth: 360 }}>
          A unified platform for managing academic sessions, attendance, and student
          payments. Access is granted by your administrator.
        </Typography>
      </Box>

      {/* Right panel */}
      <Box
        sx={{
          flex: { xs: 1, md: '0 0 420px' },
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 3,
        }}
      >
        <Box sx={{ width: '100%', maxWidth: 360 }}>

          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 4 }}>
            <Box
              sx={{
                width: 40, height: 40, borderRadius: 2,
                bgcolor: 'primary.main',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >
              <LockOutlinedIcon sx={{ color: '#fff', fontSize: 20 }} />
            </Box>
            <Box>
              <Typography variant="h6" sx={{ lineHeight: 1.2 }}>Log in</Typography>
              <Typography variant="body2">to your CampusOps account</Typography>
            </Box>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3, borderRadius: 2, fontSize: '0.8rem' }}>
              {error}
            </Alert>
          )}

          <Box
            component="form"
            onSubmit={handleSubmit}
            sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}
          >
            <TextField
              label="Email address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              fullWidth
              autoComplete="email"
            />

            <TextField
              label="Password"
              type={showPass ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              fullWidth
              autoComplete="current-password"
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPass((s) => !s)}
                        edge="end"
                        size="small"
                      >
                        {showPass
                          ? <VisibilityOffOutlinedIcon sx={{ fontSize: 18 }} />
                          : <VisibilityOutlinedIcon   sx={{ fontSize: 18 }} />}
                      </IconButton>
                    </InputAdornment>
                  ),
                },
              }}
            />

            <Button
              type="submit"
              variant="contained"
              fullWidth
              size="large"
              disabled={loading}
              sx={{ mt: 1, py: 1.25 }}
            >
              {loading ? 'Logging in…' : 'Log in'}
            </Button>
          </Box>

        </Box>
      </Box>
    </Box>
  )
}
