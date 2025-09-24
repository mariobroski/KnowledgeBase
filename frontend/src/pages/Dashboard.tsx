import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Chip,
  LinearProgress,
  Container,
  Switch,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
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
  Storage as StorageIcon,
  People as PeopleIcon,
  Backup as BackupIcon,
  Update as UpdateIcon,
  MonitorHeart as MonitoringIcon,
  AccountTree as AccountTreeIcon,
  Search as SearchIcon,
  Tune as TuneIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
interface AdminDashboardStats {
  // Prawdziwe statystyki systemu z /api/admin/system-stats
  system_status?: 'healthy' | 'warning' | 'critical';
  uptime?: string;
  uptime_seconds?: number;
  cpu_usage?: number;
  cpu_usage_percent?: number;
  cpu_cores?: number;
  memory_usage?: number;
  memory_usage_percent?: number;
  memory_used_gb?: number;
  disk_usage?: number;
  disk_usage_percent?: number;
  disk_used_gb?: number;
  memory_total_gb?: number;
  memory_available_gb?: number;
  disk_total_gb?: number;
  disk_free_gb?: number;
  cpu_count?: number;
  load_average?: number[];
  
  // Prawdziwe statystyki użytkowników z /api/admin/users-stats
  total_users?: number;
  active_users?: number;
  admin_users?: number;
  editor_users?: number;
  regular_users?: number;
  new_users_today?: number;
  user_growth_rate?: number;
  
  // Content stats (from existing API)
  article_count: number;
  fragment_count: number;
  fact_count: number;
  entity_count: number;
  relation_count: number;
  
  // Statystyki bazy danych z /api/admin/database-stats
  database_stats?: {
    articles?: number;
    total_articles?: number;
    facts?: number;
    total_facts?: number;
    entities?: number;
    total_entities?: number;
    relations?: number;
    total_relations?: number;
    users?: number;
    database_size_mb?: number;
    total_records?: number;
  };
  
  // Activity stats (from existing API + mock)
  query_count: number;
  queries_today?: number;
  total_searches?: number;
  successful_searches?: number;
  avg_response_time?: number;
  error_rate?: number;
  
  // Security stats (mock data for now)
  failed_logins?: number;
  security_alerts?: number;
  
  // Policy data (from existing API)
  policy_data?: {
    [key: string]: number;
  };

  // Dodatkowe statystyki dla RAG i grafu
  graph_stats?: {
    nodes?: number;
    edges?: number;
  };

  rag_stats?: {
    text_searches?: number;
    fact_searches?: number;
    graph_searches?: number;
  };

  recent_activities?: Array<{
    action: string;
    user: string;
    timestamp: string;
    type: 'info' | 'warning' | 'error';
  }>;
}

const PanelAdministratora: React.FC = () => {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [backupLoading, setBackupLoading] = useState(false);
  const [lastBackup, setLastBackup] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Pobierz podstawowe dane analytics
        const analyticsResponse = await fetch('http://localhost:8000/api/analytics/dashboard');
        if (!analyticsResponse.ok) {
          throw new Error('Failed to fetch analytics data');
        }
        const analyticsData = await analyticsResponse.json();
        
        // Pobierz prawdziwe statystyki systemu
        const token = localStorage.getItem('auth_token');
        const headers: Record<string, string> = {};
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        const systemResponse = await fetch('http://localhost:8000/api/admin/system-stats', { headers });
        const systemData = systemResponse.ok ? await systemResponse.json() : {};
        
        // Pobierz statystyki użytkowników
        const usersResponse = await fetch('http://localhost:8000/api/admin/users-stats', { headers });
        const usersData = usersResponse.ok ? await usersResponse.json() : {};
        
        // Pobierz statystyki bazy danych
        const dbResponse = await fetch('http://localhost:8000/api/admin/database-stats', { headers });
        const dbData = dbResponse.ok ? await dbResponse.json() : {};
        
        // Połącz wszystkie dane
        const adminData = {
          ...analyticsData,
          ...systemData,
          ...usersData,
          database_stats: dbData,
          
          // Fallback mock dane jeśli API nie działa
          queries_today: analyticsData.total_queries || 234,
          avg_response_time: 850,
          error_rate: 2.1,
          failed_logins: 5,
          security_alerts: 0,
        };
        
        setStats(adminData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    fetchMaintenanceStatus();
    fetchLastBackup();
  }, []);

  const fetchMaintenanceStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/admin/maintenance-status');
      if (response.ok) {
        const data = await response.json();
        setMaintenanceMode(data.maintenance_mode || false);
      }
    } catch (err) {
      console.error('Failed to fetch maintenance status:', err);
    }
  };

  const fetchLastBackup = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/admin/last-backup');
      if (response.ok) {
        const data = await response.json();
        setLastBackup(data.last_backup || null);
      }
    } catch (err) {
      console.error('Failed to fetch last backup info:', err);
    }
  };

  const handleMaintenanceToggle = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/admin/maintenance-mode', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled: !maintenanceMode }),
      });
      
      if (response.ok) {
        setMaintenanceMode(!maintenanceMode);
      } else {
        throw new Error('Failed to toggle maintenance mode');
      }
    } catch (err) {
      console.error('Error toggling maintenance mode:', err);
      setError('Nie udało się zmienić trybu konserwacji');
    }
  };

  const handleCreateBackup = async () => {
    setBackupLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/admin/create-backup', {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        setLastBackup(data.backup_time || 'Właśnie utworzona');
      } else {
        throw new Error('Failed to create backup');
      }
    } catch (err) {
      console.error('Error creating backup:', err);
      setError('Nie udało się utworzyć kopii zapasowej');
    } finally {
      setBackupLoading(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 4, fontWeight: 'bold', color: '#1976d2' }}>
        Panel administracyjny
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {/* Statystyki Systemu */}
          <Grid item xs={12} md={3}>
            <Card sx={{ 
              height: '100%', 
              background: stats?.cpu_usage_percent && stats.cpu_usage_percent > 80 
                ? 'linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)' 
                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
              color: 'white',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.15)'
              }
            }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                      CPU
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {stats?.cpu_usage_percent?.toFixed(1) || stats?.cpu_usage?.toFixed(1) || '0.0'}%
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      {stats?.cpu_count || stats?.cpu_cores || 'N/A'} rdzeni
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={stats?.cpu_usage_percent || stats?.cpu_usage || 0} 
                      sx={{ 
                        mt: 1, 
                        backgroundColor: 'rgba(255,255,255,0.3)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: 'rgba(255,255,255,0.9)'
                        }
                      }} 
                    />
                  </Box>
                  <ComputerIcon sx={{ fontSize: 48, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Pamięć RAM */}
          <Grid item xs={12} md={3}>
            <Card sx={{ 
              height: '100%', 
              background: stats?.memory_usage_percent && stats.memory_usage_percent > 85 
                ? 'linear-gradient(135deg, #ff9ff3 0%, #f368e0 100%)' 
                : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', 
              color: 'white',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.15)'
              }
            }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                      Pamięć RAM
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {stats?.memory_usage_percent?.toFixed(1) || stats?.memory_usage?.toFixed(1) || '0.0'}%
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      {stats?.memory_used_gb?.toFixed(1) || 'N/A'} / {stats?.memory_total_gb?.toFixed(1) || 'N/A'} GB
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={stats?.memory_usage_percent || stats?.memory_usage || 0} 
                      sx={{ 
                        mt: 1, 
                        backgroundColor: 'rgba(255,255,255,0.3)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: 'rgba(255,255,255,0.9)'
                        }
                      }} 
                    />
                  </Box>
                  <MemoryIcon sx={{ fontSize: 48, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Dysk */}
          <Grid item xs={12} md={3}>
            <Card sx={{ 
              height: '100%', 
              background: stats?.disk_usage_percent && stats.disk_usage_percent > 90 
                ? 'linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)' 
                : 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', 
              color: 'white',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.15)'
              }
            }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                      Dysk
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {stats?.disk_usage_percent?.toFixed(1) || stats?.disk_usage?.toFixed(1) || '0.0'}%
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      {stats?.disk_used_gb?.toFixed(1) || 'N/A'} / {stats?.disk_total_gb?.toFixed(1) || 'N/A'} GB
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={stats?.disk_usage_percent || stats?.disk_usage || 0} 
                      sx={{ 
                        mt: 1, 
                        backgroundColor: 'rgba(255,255,255,0.3)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: 'rgba(255,255,255,0.9)'
                        }
                      }} 
                    />
                  </Box>
                  <StorageIcon sx={{ fontSize: 48, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Status Systemu */}
          <Grid item xs={12} md={3}>
            <Card sx={{ 
              height: '100%', 
              background: stats?.system_status === 'critical' 
                ? 'linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)'
                : stats?.system_status === 'warning'
                ? 'linear-gradient(135deg, #feca57 0%, #ff9ff3 100%)'
                : 'linear-gradient(135deg, #54a0ff 0%, #2e86de 100%)', 
              color: 'white',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.15)'
              }
            }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                      Status Systemu
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
                      {stats?.system_status === 'healthy' ? 'Zdrowy' :
                       stats?.system_status === 'warning' ? 'Ostrzeżenie' :
                       stats?.system_status === 'critical' ? 'Krytyczny' : 'Nieznany'}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Uptime: {stats?.uptime || 'N/A'}
                    </Typography>
                  </Box>
                  {stats?.system_status === 'healthy' ? 
                    <SuccessIcon sx={{ fontSize: 48, opacity: 0.8 }} /> :
                   stats?.system_status === 'warning' ? 
                    <WarningIcon sx={{ fontSize: 48, opacity: 0.8 }} /> :
                    <ErrorIcon sx={{ fontSize: 48, opacity: 0.8 }} />
                  }
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Zarządzanie Użytkownikami */}
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PeopleIcon color="primary" />
                  Zarządzanie Użytkownikami
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#f5f5f5', borderRadius: 2 }}>
                      <Typography variant="h4" color="primary" sx={{ fontWeight: 'bold' }}>
                        {stats?.total_users || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Wszyscy użytkownicy
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#e8f5e8', borderRadius: 2 }}>
                      <Typography variant="h4" color="success.main" sx={{ fontWeight: 'bold' }}>
                        {stats?.active_users || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Aktywni użytkownicy
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#fff3e0', borderRadius: 2 }}>
                      <Typography variant="h4" color="warning.main" sx={{ fontWeight: 'bold' }}>
                        {stats?.editor_users || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Redaktorzy
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#fce4ec', borderRadius: 2 }}>
                      <Typography variant="h4" color="error.main" sx={{ fontWeight: 'bold' }}>
                        {stats?.admin_users || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Administratorzy
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
                <Box mt={2}>
                  <Button variant="outlined" fullWidth startIcon={<PeopleIcon />}>
                    Zarządzaj użytkownikami
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Statystyki Bazy Danych */}
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <DatabaseIcon color="primary" />
                  Baza Danych i Treści
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#e3f2fd', borderRadius: 2 }}>
                      <Typography variant="h4" color="primary" sx={{ fontWeight: 'bold' }}>
                        {stats?.database_stats?.total_articles || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Dokumenty
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#f3e5f5', borderRadius: 2 }}>
                      <Typography variant="h4" color="secondary" sx={{ fontWeight: 'bold' }}>
                        {stats?.database_stats?.total_facts || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Fakty
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#e8f5e8', borderRadius: 2 }}>
                      <Typography variant="h4" color="success.main" sx={{ fontWeight: 'bold' }}>
                        {stats?.database_stats?.total_entities || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Encje
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#fff3e0', borderRadius: 2 }}>
                      <Typography variant="h4" color="warning.main" sx={{ fontWeight: 'bold' }}>
                        {stats?.database_stats?.total_relations || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Relacje
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
                <Box mt={2}>
                  <Button variant="outlined" fullWidth startIcon={<DatabaseIcon />}>
                    Zarządzaj bazą danych
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Analityka i Monitoring */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AnalyticsIcon color="primary" />
                  Analityka Systemu
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Box textAlign="center" p={3} sx={{ backgroundColor: '#f8f9fa', borderRadius: 2 }}>
                      <Typography variant="h3" color="primary" sx={{ fontWeight: 'bold' }}>
                        {stats?.total_searches || 0}
                      </Typography>
                      <Typography variant="h6" color="textSecondary">
                        Wyszukiwania
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        w tym miesiącu
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box textAlign="center" p={3} sx={{ backgroundColor: '#f8f9fa', borderRadius: 2 }}>
                      <Typography variant="h3" color="success.main" sx={{ fontWeight: 'bold' }}>
                        {stats?.avg_response_time?.toFixed(0) || 0}ms
                      </Typography>
                      <Typography variant="h6" color="textSecondary">
                        Czas odpowiedzi
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        średni
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box textAlign="center" p={3} sx={{ backgroundColor: '#f8f9fa', borderRadius: 2 }}>
                      <Typography variant="h3" color="warning.main" sx={{ fontWeight: 'bold' }}>
                        {((stats?.successful_searches || 0) / Math.max(stats?.total_searches || 1, 1) * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="h6" color="textSecondary">
                        Skuteczność
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        wyszukiwań
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
                <Box mt={3}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Button variant="outlined" fullWidth startIcon={<AnalyticsIcon />}>
                        Szczegółowe raporty
                      </Button>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Button variant="outlined" fullWidth startIcon={<TrendingUpIcon />}>
                        Trendy użytkowania
                      </Button>
                    </Grid>
                  </Grid>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Ustawienia Systemu */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SettingsIcon color="primary" />
                  Ustawienia Systemu
                </Typography>
                <Box display="flex" flexDirection="column" gap={2}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" p={2} sx={{ backgroundColor: '#f5f5f5', borderRadius: 2 }}>
                    <Box>
                      <Typography variant="body1" fontWeight="medium">
                        Tryb konserwacji
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {maintenanceMode ? 'Włączony' : 'Wyłączony'}
                      </Typography>
                    </Box>
                    <Switch
                      checked={maintenanceMode}
                      onChange={handleMaintenanceToggle}
                      color="warning"
                    />
                  </Box>
                  
                  <Box p={2} sx={{ backgroundColor: '#f5f5f5', borderRadius: 2 }}>
                    <Typography variant="body1" fontWeight="medium" gutterBottom>
                      Kopia zapasowa
                    </Typography>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Ostatnia: {lastBackup || 'Brak'}
                    </Typography>
                    <Button
                      variant="contained"
                      fullWidth
                      onClick={handleCreateBackup}
                      disabled={backupLoading}
                      startIcon={backupLoading ? <CircularProgress size={20} /> : <BackupIcon />}
                      sx={{ mt: 1 }}
                    >
                      {backupLoading ? 'Tworzenie...' : 'Utwórz kopię'}
                    </Button>
                  </Box>

                  <Box p={2} sx={{ backgroundColor: '#f5f5f5', borderRadius: 2 }}>
                    <Typography variant="body1" fontWeight="medium" gutterBottom>
                      Zarządzanie systemem
                    </Typography>
                    <Grid container spacing={1}>
                      <Grid item xs={12}>
                        <Button variant="outlined" fullWidth startIcon={<SecurityIcon />} size="small">
                          Logi bezpieczeństwa
                        </Button>
                      </Grid>
                      <Grid item xs={12}>
                        <Button variant="outlined" fullWidth startIcon={<UpdateIcon />} size="small">
                          Aktualizacje systemu
                        </Button>
                      </Grid>
                      <Grid item xs={12}>
                        <Button variant="outlined" fullWidth startIcon={<MonitoringIcon />} size="small">
                          Monitoring wydajności
                        </Button>
                      </Grid>
                    </Grid>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Graf Wiedzy */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AccountTreeIcon color="primary" />
                  Graf Wiedzy
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#e8f5e8', borderRadius: 2 }}>
                      <Typography variant="h4" color="success.main" sx={{ fontWeight: 'bold' }}>
                        {stats?.graph_stats?.nodes || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Węzły
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#e3f2fd', borderRadius: 2 }}>
                      <Typography variant="h4" color="primary" sx={{ fontWeight: 'bold' }}>
                        {stats?.graph_stats?.edges || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Połączenia
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
                <Box mt={2}>
                  <Button variant="outlined" fullWidth startIcon={<AccountTreeIcon />}>
                    Wizualizuj graf
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Wyszukiwanie i RAG */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SearchIcon color="primary" />
                  Strategie RAG
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={4}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#f3e5f5', borderRadius: 2 }}>
                      <Typography variant="h4" color="secondary" sx={{ fontWeight: 'bold' }}>
                        {stats?.rag_stats?.text_searches || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Text-RAG
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#fff3e0', borderRadius: 2 }}>
                      <Typography variant="h4" color="warning.main" sx={{ fontWeight: 'bold' }}>
                        {stats?.rag_stats?.fact_searches || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Facts-RAG
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box textAlign="center" p={2} sx={{ backgroundColor: '#e8f5e8', borderRadius: 2 }}>
                      <Typography variant="h4" color="success.main" sx={{ fontWeight: 'bold' }}>
                        {stats?.rag_stats?.graph_searches || 0}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Graph-RAG
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
                <Box mt={2}>
                  <Button variant="outlined" fullWidth startIcon={<TuneIcon />}>
                    Konfiguruj strategie
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Ostatnie Aktywności */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <HistoryIcon color="primary" />
                  Ostatnie Aktywności Systemu
                </Typography>
                <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                  {stats?.recent_activities?.map((activity, index) => (
                    <Box key={index} display="flex" alignItems="center" gap={2} p={2} sx={{ borderBottom: '1px solid #eee' }}>
                      <Box sx={{ minWidth: 8, height: 8, borderRadius: '50%', backgroundColor: 'primary.main' }} />
                      <Box flex={1}>
                        <Typography variant="body2" fontWeight="medium">
                          {activity.action}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {activity.user} • {activity.timestamp}
                        </Typography>
                      </Box>
                      <Chip 
                        label={activity.type} 
                        size="small" 
                        color={activity.type === 'error' ? 'error' : activity.type === 'warning' ? 'warning' : 'default'}
                      />
                    </Box>
                  )) || (
                    <Typography variant="body2" color="textSecondary" textAlign="center" p={4}>
                      Brak ostatnich aktywności
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default PanelAdministratora;