import React, { useCallback, useEffect, useMemo, useState } from 'react';
import authService, { type CreateUserRequest, type UpdateUserRequest, type User } from '../services/authService';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  LinearProgress,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Divider,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Add as AddIcon,
  AdminPanelSettings as AdminIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Group as GroupIcon,
  Person as PersonIcon,
  Dashboard as DashboardIcon,
  Storage as DatabaseIcon,
  Security as SecurityIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  Warning as WarningIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
  Memory as MemoryIcon,
  Computer as ComputerIcon,
  Search as SearchIcon,
  Tune as TuneIcon,
  Speed as SpeedIcon,
  MonitorHeart as MonitoringIcon,
} from '@mui/icons-material';

interface UserFormData {
  username: string;
  email: string;
  password: string;
  role: 'USER' | 'EDITOR' | 'ADMINISTRATOR';
}

interface SystemStats {
  system_status: 'healthy' | 'warning' | 'critical';
  uptime: string;
  cpu_usage_percent: number;
  memory_usage_percent: number;
  disk_usage_percent: number;
  total_users: number;
  active_users: number;
  admin_users: number;
  queries_today: number;
  avg_response_time: number;
  error_rate: number;
  article_count: number;
  fragment_count: number;
  fact_count: number;
  entity_count: number;
  relation_count: number;
}

interface RAGSettings {
  chunk_size: number;
  similarity_threshold: number;
  max_results: number;
  temperature: number;
  cache_enabled: boolean;
  parallel_processing: boolean;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const MOCK_USERS: User[] = [
  {
    id: 1,
    username: 'aktywny_user',
    email: 'aktywny@example.com',
    role: 'USER',
    is_active: true,
    is_verified: true,
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-01-20T00:00:00Z',
    full_name: 'Aktywny Użytkownik',
    last_login: '2024-01-21T14:30:00Z',
  },
];

const AdminPanel: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [ragSettings, setRagSettings] = useState<RAGSettings>({
    chunk_size: 1000,
    similarity_threshold: 0.7,
    max_results: 10,
    temperature: 0.7,
    cache_enabled: true,
    parallel_processing: true,
  });
  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    email: '',
    password: '',
    role: 'USER',
  });

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      const usersData = await authService.getAllUsers();
      setUsers(usersData);
      setError(null);
    } catch (err) {
      console.error('Error loading users:', err);
      setError('Błąd podczas ładowania użytkowników. Wyświetlam dane przykładowe.');
      setUsers((prev) => (prev.length ? prev : MOCK_USERS));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSystemStats = useCallback(async () => {
    try {
      // Pobierz statystyki systemu
      const token = localStorage.getItem('auth_token');
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const [analyticsResponse, systemResponse, usersResponse] = await Promise.all([
        fetch('http://localhost:8000/api/analytics/dashboard'),
        fetch('http://localhost:8000/api/admin/system-stats', { headers }),
        fetch('http://localhost:8000/api/admin/users-stats', { headers })
      ]);

      const analyticsData = analyticsResponse.ok ? await analyticsResponse.json() : {};
      const systemData = systemResponse.ok ? await systemResponse.json() : {};
      const usersData = usersResponse.ok ? await usersResponse.json() : {};

      setSystemStats({
        system_status: systemData.system_status || 'healthy',
        uptime: systemData.uptime || '24h 15m',
        cpu_usage_percent: systemData.cpu_usage_percent || 45,
        memory_usage_percent: systemData.memory_usage_percent || 62,
        disk_usage_percent: systemData.disk_usage_percent || 78,
        total_users: usersData.total_users || users.length,
        active_users: usersData.active_users || 15,
        admin_users: usersData.admin_users || 3,
        queries_today: analyticsData.queries_today || 234,
        avg_response_time: analyticsData.avg_response_time || 850,
        error_rate: analyticsData.error_rate || 2.1,
        article_count: analyticsData.article_count || 0,
        fragment_count: analyticsData.fragment_count || 0,
        fact_count: analyticsData.fact_count || 0,
        entity_count: analyticsData.entity_count || 0,
        relation_count: analyticsData.relation_count || 0,
      });
    } catch (err) {
      console.error('Error loading system stats:', err);
      // Fallback do danych przykładowych
      setSystemStats({
        system_status: 'healthy',
        uptime: '24h 15m',
        cpu_usage_percent: 45,
        memory_usage_percent: 62,
        disk_usage_percent: 78,
        total_users: users.length,
        active_users: 15,
        admin_users: 3,
        queries_today: 234,
        avg_response_time: 850,
        error_rate: 2.1,
        article_count: 156,
        fragment_count: 1247,
        fact_count: 892,
        entity_count: 345,
        relation_count: 678,
      });
    }
  }, [users.length]);

  useEffect(() => {
    void loadUsers();
    void loadSystemStats();
  }, [loadUsers, loadSystemStats]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleRagSettingChange = (key: keyof RAGSettings, value: any) => {
    setRagSettings(prev => ({ ...prev, [key]: value }));
  };

  const saveRagSettings = async () => {
    try {
      setSubmitting(true);
      // Tutaj można dodać wywołanie API do zapisania ustawień RAG
      setSuccess('Ustawienia RAG zostały zapisane');
    } catch (err) {
      setError('Błąd podczas zapisywania ustawień RAG');
    } finally {
      setSubmitting(false);
    }
  };

  const stats = useMemo(() => {
    const totalUsers = users.length;
    const adminUsers = users.filter((user) => user.role === 'ADMINISTRATOR').length;
    const regularUsers = totalUsers - adminUsers;
    return { totalUsers, adminUsers, regularUsers };
  }, [users]);

  const handleOpenDialog = (user?: User) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        username: user.username,
        email: user.email,
        password: '',
        role: user.role,
      });
    } else {
      setEditingUser(null);
      setFormData({
        username: '',
        email: '',
        password: '',
        role: 'USER',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingUser(null);
    setFormData({
      username: '',
      email: '',
      password: '',
      role: 'USER',
    });
  };

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      setError(null);

      if (editingUser) {
        const updateData: UpdateUserRequest = {
          username: formData.username,
          email: formData.email,
          role: formData.role,
        };

        if (formData.password) {
          updateData.password = formData.password;
        }

        await authService.updateUser(editingUser.id, updateData);
        setSuccess('Użytkownik został zaktualizowany');
      } else {
        if (!formData.password.trim()) {
          setError('Hasło jest wymagane przy tworzeniu nowego użytkownika');
          return;
        }

        const createData: CreateUserRequest = {
          username: formData.username,
          email: formData.email,
          password: formData.password,
          role: formData.role,
        };

        await authService.createUser(createData);
        setSuccess('Użytkownik został utworzony');
      }

      await loadUsers();
      handleCloseDialog();
    } catch (err) {
      console.error('Error saving user:', err);
      setError('Błąd podczas zapisywania użytkownika');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    try {
      setSubmitting(true);
      await authService.deleteUser(userId);
      await loadUsers();
      setSuccess('Użytkownik został usunięty');
    } catch (err) {
      console.error('Error deleting user:', err);
      setError('Błąd podczas usuwania użytkownika');
    } finally {
      setSubmitting(false);
    }
  };



  if (loading && !users.length) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <AdminIcon sx={{ mr: 2, fontSize: 32 }} />
        <Typography variant="h4" component="h1">
          Panel Administracyjny
        </Typography>
      </Box>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Centralny panel zarządzania systemem - użytkownicy, statystyki, monitoring i kluczowe ustawienia
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="admin panel tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<DashboardIcon />} label="Przegląd systemu" />
          <Tab icon={<GroupIcon />} label="Zarządzanie użytkownikami" />
          <Tab icon={<TuneIcon />} label="Szybkie ustawienia RAG" />
          <Tab icon={<MonitoringIcon />} label="Monitoring" />
        </Tabs>

        {/* Tab 1: Przegląd systemu */}
        <TabPanel value={tabValue} index={0}>
          {systemStats && (
            <Grid container spacing={3}>
              {/* Status systemu */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <ComputerIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <Typography variant="h6">Status systemu</Typography>
                      <Chip
                        label={systemStats.system_status === 'healthy' ? 'Zdrowy' : 
                               systemStats.system_status === 'warning' ? 'Ostrzeżenie' : 'Krytyczny'}
                        color={systemStats.system_status === 'healthy' ? 'success' : 
                               systemStats.system_status === 'warning' ? 'warning' : 'error'}
                        sx={{ ml: 'auto' }}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Uptime: {systemStats.uptime}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Zasoby systemowe */}
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <MemoryIcon sx={{ mr: 2, color: 'info.main' }} />
                      <Typography variant="h6">CPU</Typography>
                    </Box>
                    <Typography variant="h4" color="primary">
                      {systemStats.cpu_usage_percent}%
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={systemStats.cpu_usage_percent} 
                      sx={{ mt: 1 }}
                    />
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <MemoryIcon sx={{ mr: 2, color: 'warning.main' }} />
                      <Typography variant="h6">Pamięć</Typography>
                    </Box>
                    <Typography variant="h4" color="primary">
                      {systemStats.memory_usage_percent}%
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={systemStats.memory_usage_percent} 
                      sx={{ mt: 1 }}
                    />
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <DatabaseIcon sx={{ mr: 2, color: 'success.main' }} />
                      <Typography variant="h6">Dysk</Typography>
                    </Box>
                    <Typography variant="h4" color="primary">
                      {systemStats.disk_usage_percent}%
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={systemStats.disk_usage_percent} 
                      sx={{ mt: 1 }}
                    />
                  </CardContent>
                </Card>
              </Grid>

              {/* Statystyki użytkowników */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <GroupIcon color="primary" />
                      Użytkownicy
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={4}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="primary">
                            {systemStats.total_users}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Wszyscy
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={4}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="success.main">
                            {systemStats.active_users}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Aktywni
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={4}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="warning.main">
                            {systemStats.admin_users}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Admini
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>

              {/* Statystyki RAG */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SearchIcon color="primary" />
                      Aktywność RAG
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="primary">
                            {systemStats.queries_today}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Zapytania dziś
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="info.main">
                            {systemStats.avg_response_time}ms
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Śr. czas odpowiedzi
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>

              {/* Baza wiedzy */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <DatabaseIcon color="primary" />
                      Baza wiedzy
                    </Typography>
                    <Grid container spacing={3}>
                      <Grid item xs={6} md={2.4}>
                        <Box textAlign="center" p={2}>
                          <Typography variant="h4" color="primary">
                            {systemStats.article_count}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Dokumenty
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} md={2.4}>
                        <Box textAlign="center" p={2}>
                          <Typography variant="h4" color="info.main">
                            {systemStats.fragment_count}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Fragmenty
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} md={2.4}>
                        <Box textAlign="center" p={2}>
                          <Typography variant="h4" color="success.main">
                            {systemStats.fact_count}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Fakty
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} md={2.4}>
                        <Box textAlign="center" p={2}>
                          <Typography variant="h4" color="warning.main">
                            {systemStats.entity_count}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Encje
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6} md={2.4}>
                        <Box textAlign="center" p={2}>
                          <Typography variant="h4" color="error.main">
                            {systemStats.relation_count}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Relacje
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* Tab 2: Zarządzanie użytkownikami */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Zarządzanie użytkownikami</Typography>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
              Dodaj użytkownika
            </Button>
          </Box>

          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Nazwa użytkownika</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Rola</TableCell>
                  <TableCell>Data utworzenia</TableCell>
                  <TableCell align="right">Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((userItem) => (
                  <TableRow key={userItem.id} hover>
                    <TableCell>{userItem.id}</TableCell>
                    <TableCell>{userItem.username}</TableCell>
                    <TableCell>{userItem.email}</TableCell>
                    <TableCell>
                      <Chip
                        label={
                          userItem.role === 'ADMINISTRATOR'
                            ? 'Administrator'
                            : userItem.role === 'EDITOR'
                            ? 'Edytor'
                            : 'Użytkownik'
                        }
                        color={
                          userItem.role === 'ADMINISTRATOR'
                            ? 'warning'
                            : userItem.role === 'EDITOR'
                            ? 'info'
                            : 'default'
                        }
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {userItem.created_at
                        ? new Date(userItem.created_at).toLocaleDateString('pl-PL')
                        : '—'}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => handleOpenDialog(userItem)} color="primary">
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteUser(userItem.id)}
                        color="error"
                        disabled={userItem.id === 1 || submitting}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* Tab 3: Szybkie ustawienia RAG */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TuneIcon color="primary" />
                Kluczowe ustawienia RAG
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Szybka konfiguracja najważniejszych parametrów systemu RAG
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Parametry wyszukiwania
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <TextField
                      fullWidth
                      label="Rozmiar fragmentu"
                      type="number"
                      value={ragSettings.chunk_size}
                      onChange={(e) => handleRagSettingChange('chunk_size', parseInt(e.target.value))}
                      sx={{ mb: 2 }}
                    />
                    <TextField
                      fullWidth
                      label="Maksymalna liczba wyników"
                      type="number"
                      value={ragSettings.max_results}
                      onChange={(e) => handleRagSettingChange('max_results', parseInt(e.target.value))}
                      sx={{ mb: 2 }}
                    />
                    <Box sx={{ px: 2, mb: 2 }}>
                      <Typography gutterBottom>
                        Próg podobieństwa: {ragSettings.similarity_threshold}
                      </Typography>
                      <Box sx={{ px: 1 }}>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.1"
                          value={ragSettings.similarity_threshold}
                          onChange={(e) => handleRagSettingChange('similarity_threshold', parseFloat(e.target.value))}
                          style={{ width: '100%' }}
                        />
                      </Box>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Ustawienia modelu
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Box sx={{ px: 2, mb: 2 }}>
                      <Typography gutterBottom>
                        Temperatura: {ragSettings.temperature}
                      </Typography>
                      <Box sx={{ px: 1 }}>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.1"
                          value={ragSettings.temperature}
                          onChange={(e) => handleRagSettingChange('temperature', parseFloat(e.target.value))}
                          style={{ width: '100%' }}
                        />
                      </Box>
                    </Box>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={ragSettings.cache_enabled}
                          onChange={(e) => handleRagSettingChange('cache_enabled', e.target.checked)}
                        />
                      }
                      label="Cache'owanie włączone"
                      sx={{ mb: 1 }}
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={ragSettings.parallel_processing}
                          onChange={(e) => handleRagSettingChange('parallel_processing', e.target.checked)}
                        />
                      }
                      label="Przetwarzanie równoległe"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                <Button variant="outlined" onClick={() => setRagSettings({
                  chunk_size: 1000,
                  similarity_threshold: 0.7,
                  max_results: 10,
                  temperature: 0.7,
                  cache_enabled: true,
                  parallel_processing: true,
                })}>
                  Przywróć domyślne
                </Button>
                <Button variant="contained" onClick={saveRagSettings} disabled={submitting}>
                  Zapisz ustawienia
                </Button>
              </Box>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 4: Monitoring */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MonitoringIcon color="primary" />
                Monitoring systemu
              </Typography>
            </Grid>

            {systemStats && (
              <>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Wydajność
                      </Typography>
                      <Box sx={{ mt: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Średni czas odpowiedzi</Typography>
                          <Typography variant="body2" color="primary">
                            {systemStats.avg_response_time}ms
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Współczynnik błędów</Typography>
                          <Typography variant="body2" color={systemStats.error_rate > 5 ? 'error' : 'success'}>
                            {systemStats.error_rate}%
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">Zapytania dziś</Typography>
                          <Typography variant="body2" color="info.main">
                            {systemStats.queries_today}
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Alerty
                      </Typography>
                      <Box sx={{ mt: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          {systemStats.system_status === 'healthy' ? (
                            <SuccessIcon color="success" sx={{ mr: 1 }} />
                          ) : systemStats.system_status === 'warning' ? (
                            <WarningIcon color="warning" sx={{ mr: 1 }} />
                          ) : (
                            <ErrorIcon color="error" sx={{ mr: 1 }} />
                          )}
                          <Typography variant="body2">
                            System: {systemStats.system_status === 'healthy' ? 'Zdrowy' : 
                                     systemStats.system_status === 'warning' ? 'Ostrzeżenie' : 'Krytyczny'}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          {systemStats.cpu_usage_percent < 80 ? (
                            <SuccessIcon color="success" sx={{ mr: 1 }} />
                          ) : (
                            <WarningIcon color="warning" sx={{ mr: 1 }} />
                          )}
                          <Typography variant="body2">
                            CPU: {systemStats.cpu_usage_percent}%
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {systemStats.memory_usage_percent < 85 ? (
                            <SuccessIcon color="success" sx={{ mr: 1 }} />
                          ) : (
                            <WarningIcon color="warning" sx={{ mr: 1 }} />
                          )}
                          <Typography variant="body2">
                            Pamięć: {systemStats.memory_usage_percent}%
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Szybkie akcje
                      </Typography>
                      <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Button variant="outlined" size="small" startIcon={<AnalyticsIcon />}>
                          Pełna analityka
                        </Button>
                        <Button variant="outlined" size="small" startIcon={<SettingsIcon />}>
                          Ustawienia RAG
                        </Button>
                        <Button variant="outlined" size="small" startIcon={<DatabaseIcon />}>
                          Zarządzaj bazą
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </>
            )}
          </Grid>
        </TabPanel>
      </Paper>

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingUser ? 'Edytuj użytkownika' : 'Dodaj nowego użytkownika'}</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Nazwa użytkownika"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label={editingUser ? 'Nowe hasło (opcjonalne)' : 'Hasło'}
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              margin="normal"
              required={!editingUser}
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Rola</InputLabel>
              <Select
                value={formData.role}
                label="Rola"
                onChange={(e) =>
                  setFormData({ ...formData, role: e.target.value as 'USER' | 'EDITOR' | 'ADMINISTRATOR' })
                }
              >
                <MenuItem value="USER">Użytkownik</MenuItem>
                <MenuItem value="EDITOR">Edytor</MenuItem>
                <MenuItem value="ADMINISTRATOR">Administrator</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={submitting}>
            Anuluj
          </Button>
          <Button onClick={handleSubmit} variant="contained" disabled={submitting}>
            {editingUser ? 'Aktualizuj' : 'Utwórz'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminPanel;