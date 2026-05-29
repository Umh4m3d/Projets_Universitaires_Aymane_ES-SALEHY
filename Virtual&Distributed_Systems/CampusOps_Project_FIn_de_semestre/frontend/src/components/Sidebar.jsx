import { useNavigate, useLocation } from 'react-router-dom'
import {
  Box, Drawer, List, ListItemButton, ListItemIcon,
  ListItemText, Typography, Divider, Avatar, Chip, Button,
} from '@mui/material'
import DashboardOutlinedIcon      from '@mui/icons-material/DashboardOutlined'
import CalendarTodayOutlinedIcon  from '@mui/icons-material/CalendarTodayOutlined'
import AddCircleOutlinedIcon      from '@mui/icons-material/AddCircleOutlined'
import AssignmentOutlinedIcon     from '@mui/icons-material/AssignmentOutlined'
import EditNoteOutlinedIcon       from '@mui/icons-material/EditNoteOutlined'
import CreditCardOutlinedIcon     from '@mui/icons-material/CreditCardOutlined'
import PeopleOutlinedIcon         from '@mui/icons-material/PeopleOutlined'
import PersonOutlinedIcon         from '@mui/icons-material/PersonOutlined'
import LogoutOutlinedIcon         from '@mui/icons-material/LogoutOutlined'
import SchoolOutlinedIcon         from '@mui/icons-material/SchoolOutlined'
import GroupsOutlinedIcon         from '@mui/icons-material/GroupsOutlined'
import PendingActionsOutlinedIcon from '@mui/icons-material/PendingActionsOutlined'
import FolderOutlinedIcon         from '@mui/icons-material/FolderOutlined'
import MenuBookOutlinedIcon       from '@mui/icons-material/MenuBookOutlined'
import TrendingUpOutlinedIcon     from '@mui/icons-material/TrendingUpOutlined'
import BarChartOutlinedIcon       from '@mui/icons-material/BarChartOutlined'
import EventNoteOutlinedIcon      from '@mui/icons-material/EventNoteOutlined'
import MailOutlinedIcon           from '@mui/icons-material/MailOutlined'
import { useAuth } from '../context/AuthContext'

const NAV = [
  // ── General ──────────────────────────────────────────────────────
  { to: '/dashboard',        label: 'Dashboard',         Icon: DashboardOutlinedIcon,      roles: ['admin','secretary','teacher','student'] },

  // ── Sessions ─────────────────────────────────────────────────────
  { to: '/sessions',         label: 'Sessions',          Icon: CalendarTodayOutlinedIcon,  roles: ['admin','secretary','teacher','student'] },
  { to: '/sessions/create',  label: 'New Session',       Icon: AddCircleOutlinedIcon,      roles: ['admin','secretary','teacher'] },
  { to: '/sessions/pending', label: 'Session Requests',  Icon: PendingActionsOutlinedIcon, roles: ['admin'] },
  { to: '/planning',         label: 'Planning',          Icon: EventNoteOutlinedIcon,      roles: ['admin','secretary','teacher'] },

  // ── Absences ──────────────────────────────────────────────────────
  { to: '/absences',         label: 'Absences',          Icon: AssignmentOutlinedIcon,     roles: ['admin','secretary','teacher','student'] },
  { to: '/absences/mark',    label: 'Mark Absence',      Icon: EditNoteOutlinedIcon,       roles: ['teacher','secretary'] },
  { to: '/absences/stats',   label: 'Absence Stats',     Icon: BarChartOutlinedIcon,       roles: ['admin','secretary','teacher'] },

  // ── Finance ──────────────────────────────────────────────────────
  { to: '/payments',         label: 'Payments',          Icon: CreditCardOutlinedIcon,     roles: ['admin','secretary','student'] },

  // ── Progress ─────────────────────────────────────────────────────
  { to: '/progress',         label: 'Progress',          Icon: TrendingUpOutlinedIcon,     roles: ['admin','secretary','teacher'] },

  // ── Management ───────────────────────────────────────────────────
  { to: '/teachers',         label: 'Teachers',          Icon: SchoolOutlinedIcon,         roles: ['admin'] },
  { to: '/students',         label: 'Students',          Icon: GroupsOutlinedIcon,         roles: ['admin','secretary'] },
  { to: '/groups',           label: 'Groups',            Icon: FolderOutlinedIcon,         roles: ['admin','secretary'] },
  { to: '/courses',          label: 'Courses',           Icon: MenuBookOutlinedIcon,       roles: ['admin','secretary'] },
  { to: '/users',            label: 'Staff Accounts',    Icon: PeopleOutlinedIcon,         roles: ['admin'] },
  { to: '/mail',             label: 'Mail Inbox',        Icon: MailOutlinedIcon,           roles: ['admin'] },

  // ── Personal ─────────────────────────────────────────────────────
  { to: '/profile',          label: 'My Profile',        Icon: PersonOutlinedIcon,         roles: ['admin','secretary','teacher','student'] },
]

const ROLE_COLOR = {
  admin:     'error',
  secretary: 'secondary',
  teacher:   'primary',
  student:   'success',
}

function getInitials(name) {
  if (!name) return '?'
  return name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()
}

export default function Sidebar({ width }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const links = NAV.filter((n) => n.roles.includes(user?.role))

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <Drawer
      variant="permanent"
      sx={{
        width,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width,
          boxSizing: 'border-box',
          bgcolor: '#0F172A',
          color: '#CBD5E1',
          borderRight: 'none',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      {/* Brand */}
      <Box sx={{ px: 2.5, pt: 3, pb: 2 }}>
        <Typography variant="h6" sx={{ color: '#F8FAFC', fontWeight: 700, letterSpacing: '-0.02em', fontSize: '1.1rem' }}>
          CampusOps
        </Typography>
        <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.7rem' }}>
          Academic Management
        </Typography>
      </Box>

      <Divider sx={{ borderColor: '#1E293B', mx: 2 }} />

      {/* User info */}
      <Box sx={{ px: 2, py: 2, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Avatar sx={{ width: 36, height: 36, bgcolor: '#2563EB', fontSize: '0.8rem', fontWeight: 700 }}>
          {getInitials(user?.full_name)}
        </Avatar>
        <Box sx={{ minWidth: 0 }}>
          <Typography sx={{ color: '#F1F5F9', fontSize: '0.8rem', fontWeight: 600, lineHeight: 1.2 }} noWrap>
            {user?.full_name}
          </Typography>
          <Chip
            label={user?.role}
            size="small"
            color={ROLE_COLOR[user?.role] || 'default'}
            sx={{ height: 18, fontSize: '0.65rem', mt: 0.25, fontWeight: 600 }}
          />
        </Box>
      </Box>

      <Divider sx={{ borderColor: '#1E293B', mx: 2, mb: 1 }} />

      {/* Navigation */}
      <List sx={{ px: 1.5, flex: 1, overflowY: 'auto' }}>
        {links.map(({ to, label, Icon }) => {
          const active =
            location.pathname === to ||
            (to !== '/dashboard' && location.pathname.startsWith(to))
          return (
            <ListItemButton
              key={to}
              selected={active}
              onClick={() => navigate(to)}
              sx={{
                py: 0.85,
                px: 1.5,
                '&.Mui-selected': {
                  bgcolor: '#1E3A5F',
                  color: '#93C5FD',
                  '& .MuiListItemIcon-root': { color: '#93C5FD' },
                },
                '&:hover': { bgcolor: '#1E293B' },
                color: '#94A3B8',
              }}
            >
              <ListItemIcon sx={{ minWidth: 34, color: 'inherit' }}>
                <Icon sx={{ fontSize: 17 }} />
              </ListItemIcon>
              <ListItemText
                primary={label}
                primaryTypographyProps={{ fontSize: '0.8rem', fontWeight: active ? 600 : 400 }}
              />
            </ListItemButton>
          )
        })}
      </List>

      {/* Logout */}
      <Box sx={{ p: 2 }}>
        <Divider sx={{ borderColor: '#1E293B', mb: 2 }} />
        <Button
          fullWidth
          startIcon={<LogoutOutlinedIcon sx={{ fontSize: 16 }} />}
          onClick={handleLogout}
          sx={{
            color: '#64748B',
            justifyContent: 'flex-start',
            px: 1.5,
            py: 1,
            fontSize: '0.8rem',
            '&:hover': { bgcolor: '#1E293B', color: '#94A3B8' },
          }}
        >
          Sign out
        </Button>
      </Box>
    </Drawer>
  )
}
