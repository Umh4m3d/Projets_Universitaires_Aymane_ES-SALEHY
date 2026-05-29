import { Box } from '@mui/material'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

const SIDEBAR_WIDTH = 248

export default function Layout() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <Sidebar width={SIDEBAR_WIDTH} />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          ml: `${SIDEBAR_WIDTH}px`,
          p: { xs: 2, sm: 3, md: 4 },
          minHeight: '100vh',
          maxWidth: '100%',
        }}
      >
        <Outlet />
      </Box>
    </Box>
  )
}
