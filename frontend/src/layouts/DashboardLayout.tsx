// ---------------------------------------------------------------------------
// DashboardLayout — sidebar layout with security-focused nav
// ---------------------------------------------------------------------------

import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Divider from '@mui/material/Divider';
import Avatar from '@mui/material/Avatar';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Tooltip from '@mui/material/Tooltip';
import Fade from '@mui/material/Fade';
import MenuIcon from '@mui/icons-material/Menu';
import HomeOutlinedIcon from '@mui/icons-material/HomeOutlined';
import ExploreOutlinedIcon from '@mui/icons-material/ExploreOutlined';
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined';
import LogoutIcon from '@mui/icons-material/Logout';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import ChatOutlinedIcon from '@mui/icons-material/ChatOutlined';
import AgentShieldLogo from '@/components/common/AgentShieldLogo';
import { useAuth } from '@/hooks/useAuth';
import { useUiStore } from '@/store/uiStore';
import { SIDEBAR_WIDTH } from '@/utils/constants';

const EASE = 'cubic-bezier(0.4, 0, 0.2, 1)';

const NAV_ITEMS = [
    { label: 'Security Hub', path: '/', icon: <HomeOutlinedIcon fontSize="small" /> },
    { label: 'Agent Explorer', path: '/explorer', icon: <ExploreOutlinedIcon fontSize="small" /> },
    { label: 'Playground', path: '/playground', icon: <ChatOutlinedIcon fontSize="small" /> },
    { label: 'Providers', path: '/settings/providers', icon: <SettingsOutlinedIcon fontSize="small" /> },
];

export default function DashboardLayout() {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, logout } = useAuth();
    const { sidebarOpen, toggleSidebar, themeMode, toggleTheme } = useUiStore();
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

    const drawer = (
        <Box sx={{ width: SIDEBAR_WIDTH, height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Brand */}
            <Box sx={{ px: 2, py: 2.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Box sx={{ width: 28, height: 28, borderRadius: '6px', overflow: 'hidden', flexShrink: 0 }}>
                    <AgentShieldLogo size={28} />
                </Box>
                <Box>
                    <Typography
                        sx={{
                            fontWeight: 600,
                            fontSize: '0.9rem',
                            letterSpacing: '-0.01em',
                            color: 'text.primary',
                            lineHeight: 1.2,
                        }}
                    >
                        AgentShield
                    </Typography>
                    <Typography sx={{ fontSize: '0.65rem', color: 'text.secondary', letterSpacing: '0.03em' }}>
                        On-Chain AI Security · Monad
                    </Typography>
                </Box>
            </Box>

            <Divider />

            {/* Navigation */}
            <List sx={{ flex: 1, px: 0.5, py: 1 }}>
                {NAV_ITEMS.map((item) => {
                    const active =
                        location.pathname === item.path ||
                        (item.path !== '/' && location.pathname.startsWith(item.path));
                    return (
                        <ListItemButton
                            key={item.path}
                            selected={active}
                            onClick={() => navigate(item.path)}
                            sx={{ mb: 0.25 }}
                        >
                            <ListItemIcon sx={{ opacity: active ? 1 : 0.6 }}>
                                {item.icon}
                            </ListItemIcon>
                            <ListItemText
                                primary={item.label}
                                primaryTypographyProps={{
                                    fontSize: '0.875rem',
                                    fontWeight: active ? 600 : 400,
                                }}
                            />
                        </ListItemButton>
                    );
                })}
            </List>

            <Divider />

            {/* User section */}
            <Box sx={{ p: 1.5 }}>
                <Box
                    sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        p: 1,
                        borderRadius: '6px',
                        cursor: 'default',
                        '&:hover': { bgcolor: 'action.hover' },
                    }}
                >
                    <Avatar
                        sx={{
                            width: 28,
                            height: 28,
                            fontSize: '0.75rem',
                            bgcolor: (t) => t.palette.mode === 'dark' ? '#21262D' : '#E2E5E9',
                            color: 'text.primary',
                            fontWeight: 600,
                        }}
                    >
                        {user?.full_name?.charAt(0)?.toUpperCase() ?? 'U'}
                    </Avatar>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography
                            sx={{
                                fontWeight: 500,
                                fontSize: '0.8125rem',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                color: 'text.primary',
                            }}
                        >
                            {user?.full_name ?? 'User'}
                        </Typography>
                    </Box>
                    <Tooltip title="Sign out">
                        <IconButton
                            size="small"
                            onClick={logout}
                            sx={{ color: 'text.secondary', '&:hover': { color: 'error.main' } }}
                        >
                            <LogoutIcon sx={{ fontSize: 16 }} />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>
        </Box>
    );

    return (
        <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
            {/* Sidebar */}
            <Drawer
                variant="persistent"
                open={sidebarOpen}
                sx={{
                    width: sidebarOpen ? SIDEBAR_WIDTH : 0,
                    flexShrink: 0,
                    transition: `width 0.22s ${EASE}`,
                    '& .MuiDrawer-paper': {
                        width: SIDEBAR_WIDTH,
                        boxSizing: 'border-box',
                        transition: `transform 0.22s ${EASE}`,
                        borderRight: 'none',
                        boxShadow: (t) => t.palette.mode === 'dark'
                            ? '1px 0 0 #30363D'
                            : '1px 0 0 #D0D7DE',
                    },
                }}
            >
                {drawer}
            </Drawer>

            {/* Main */}
            <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                {/* Top bar */}
                <AppBar position="sticky" color="default" elevation={0}>
                    <Toolbar sx={{ gap: 1, minHeight: { xs: 48, sm: 52 }, px: 2 }}>
                        <IconButton
                            size="small"
                            edge="start"
                            onClick={toggleSidebar}
                            sx={{ color: 'text.secondary' }}
                        >
                            <MenuIcon fontSize="small" />
                        </IconButton>

                        <Box sx={{ flexGrow: 1 }} />

                        <Tooltip title={`Switch to ${themeMode === 'light' ? 'dark' : 'light'} mode`}>
                            <IconButton
                                size="small"
                                onClick={toggleTheme}
                                sx={{ color: 'text.secondary' }}
                            >
                                {themeMode === 'light'
                                    ? <Brightness4Icon fontSize="small" />
                                    : <Brightness7Icon fontSize="small" />
                                }
                            </IconButton>
                        </Tooltip>

                        <Tooltip title={user?.email ?? ''}>
                            <IconButton
                                size="small"
                                onClick={(e) => setAnchorEl(e.currentTarget)}
                                sx={{ p: 0.25 }}
                            >
                                <Avatar
                                    sx={{
                                        width: 28,
                                        height: 28,
                                        fontSize: '0.75rem',
                                        bgcolor: (t) => t.palette.mode === 'dark' ? '#21262D' : '#E2E5E9',
                                        color: 'text.primary',
                                        fontWeight: 600,
                                        border: (t) => `1px solid ${t.palette.divider}`,
                                    }}
                                >
                                    {user?.full_name?.charAt(0)?.toUpperCase() ?? 'U'}
                                </Avatar>
                            </IconButton>
                        </Tooltip>

                        <Menu
                            anchorEl={anchorEl}
                            open={Boolean(anchorEl)}
                            onClose={() => setAnchorEl(null)}
                            TransitionComponent={Fade}
                            slotProps={{ paper: { sx: { mt: 0.5 } } }}
                        >
                            <Box sx={{ px: 2, py: 1.5 }}>
                                <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
                                    {user?.full_name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'inherit' }}>
                                    {user?.email}
                                </Typography>
                            </Box>
                            <Divider sx={{ my: 0.5 }} />
                            <MenuItem
                                onClick={() => { setAnchorEl(null); logout(); }}
                                sx={{ gap: 1.5, color: 'error.main', fontSize: '0.875rem' }}
                            >
                                <LogoutIcon sx={{ fontSize: 16 }} />
                                Sign Out
                            </MenuItem>
                        </Menu>
                    </Toolbar>
                </AppBar>

                {/* Page content */}
                <Fade in timeout={250}>
                    <Box
                        component="main"
                        sx={{
                            flexGrow: 1,
                            p: { xs: 2, sm: 3 },
                            maxWidth: 1400,
                            mx: 'auto',
                            width: '100%',
                        }}
                    >
                        <Outlet />
                    </Box>
                </Fade>
            </Box>
        </Box>
    );
}
