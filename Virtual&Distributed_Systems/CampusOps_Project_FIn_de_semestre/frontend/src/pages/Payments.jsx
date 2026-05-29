import {
  Box, Typography, Card, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Skeleton,
} from '@mui/material'
import { useAuth } from '../context/AuthContext'
import { useApi } from '../hooks/useApi'

const STATUS_CHIP = {
  paid:    { label: 'Paid',    color: 'success' },
  partial: { label: 'Partial', color: 'warning' },
  overdue: { label: 'Overdue', color: 'error'   },
  pending: { label: 'Pending', color: 'default' },
}

export default function Payments() {
  const { user } = useAuth()
  const isStudent = user?.role === 'student'
  const { data, loading, error } = useApi(isStudent ? '/payments/mine' : '/payments/')

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5">Payments</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          {isStudent ? 'Your payment history' : 'All payment records'}
        </Typography>
      </Box>

      {error && <Typography color="error">{error}</Typography>}

      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                {!isStudent && <TableCell>Student</TableCell>}
                <TableCell>Type</TableCell>
                <TableCell>Month</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Paid</TableCell>
                <TableCell>Due Date</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                [1, 2, 3].map((k) => (
                  <TableRow key={k}>
                    {[...Array(isStudent ? 6 : 7)].map((_, i) => (
                      <TableCell key={i}><Skeleton height={20} /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : !data?.length ? (
                <TableRow>
                  <TableCell colSpan={isStudent ? 6 : 7} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                    No payment records found.
                  </TableCell>
                </TableRow>
              ) : (
                data.map((p) => {
                  const chip = STATUS_CHIP[p.status] || STATUS_CHIP.pending
                  return (
                    <TableRow key={p.id} hover>
                      {!isStudent && <TableCell>{p.student_name || '—'}</TableCell>}
                      <TableCell sx={{ textTransform: 'capitalize' }}>{p.type}</TableCell>
                      <TableCell>{p.month || '—'}</TableCell>
                      <TableCell>{p.amount} DH</TableCell>
                      <TableCell>{p.amount_paid} DH</TableCell>
                      <TableCell>{p.due_date}</TableCell>
                      <TableCell>
                        <Chip label={chip.label} color={chip.color} size="small" />
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
    </Box>
  )
}
