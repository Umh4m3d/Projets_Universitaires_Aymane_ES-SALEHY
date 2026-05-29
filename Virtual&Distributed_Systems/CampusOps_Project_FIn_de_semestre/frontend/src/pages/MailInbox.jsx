import {
  Box, Typography, Card, CardContent, Skeleton, Alert,
  Button, Divider, Chip,
} from '@mui/material'
import MailOutlinedIcon      from '@mui/icons-material/MailOutlined'
import RefreshOutlinedIcon   from '@mui/icons-material/RefreshOutlined'
import { useApi } from '../hooks/useApi'

export default function MailInbox() {
  const { data: emails, loading, error, refetch } = useApi('/mail/latest')

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h5">Mail Inbox</Typography>
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            Last 10 messages from the connected mailbox
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshOutlinedIcon sx={{ fontSize: 16 }} />}
          onClick={refetch}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          {error} — Make sure MAIL_HOST_IMAP, MAIL_USER and MAIL_PASSWORD are set in your .env file.
        </Alert>
      )}

      <Card>
        <CardContent sx={{ p: 0 }}>
          {loading ? (
            [1, 2, 3, 4, 5].map((k) => (
              <Box key={k} sx={{ px: 3, py: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
                <Skeleton height={20} width="40%" sx={{ mb: 0.5 }} />
                <Skeleton height={16} width="70%" />
              </Box>
            ))
          ) : !emails?.length ? (
            <Box sx={{ px: 3, py: 6, textAlign: 'center' }}>
              <MailOutlinedIcon sx={{ fontSize: 40, color: 'text.disabled', mb: 1 }} />
              <Typography variant="body2" color="text.secondary">
                No emails found. Check your mail configuration in .env.
              </Typography>
            </Box>
          ) : (
            emails.map((mail, i) => (
              <Box key={mail.uid}>
                {i > 0 && <Divider />}
                <Box sx={{ px: 3, py: 2.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.75 }}>
                    <Typography sx={{ fontWeight: 600, fontSize: '0.875rem', flex: 1, mr: 2 }}>
                      {mail.subject}
                    </Typography>
                    <Chip label={`#${mail.uid}`} size="small" variant="outlined" sx={{ fontSize: '0.65rem', flexShrink: 0 }} />
                  </Box>
                  <Typography variant="body2" sx={{ color: 'text.secondary', mb: 0.5 }}>
                    From: {mail.sender}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.disabled', display: 'block', mb: 1 }}>
                    {mail.date}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic', fontSize: '0.8rem' }}>
                    {mail.preview || '(no preview)'}
                  </Typography>
                </Box>
              </Box>
            ))
          )}
        </CardContent>
      </Card>
    </Box>
  )
}
