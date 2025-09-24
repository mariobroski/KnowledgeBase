import React, { useEffect, useMemo, useState } from 'react';
import authService, { type UpdateUserRequest, type User } from '../services/authService';
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  TextField,
  Typography,
} from '@mui/material';
import {
  Badge as BadgeIcon,
  CalendarToday as CalendarIcon,
  Cancel as CancelIcon,
  Edit as EditIcon,
  Email as EmailIcon,
  Person as PersonIcon,
  Save as SaveIcon,
} from '@mui/icons-material';

interface ProfileFormData {
  username: string;
  email: string;
  full_name: string;
}

const MOCK_USER: User = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com',
  full_name: 'Administrator',
  role: 'ADMINISTRATOR',
  is_active: true,
  is_verified: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-06-01T00:00:00Z',
  last_login: '2024-01-15T10:30:00Z',
};

const Profile: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<ProfileFormData>({ username: '', email: '', full_name: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const hydrateForm = (source: User) => {
    setFormData({
      username: source.username,
      email: source.email,
      full_name: source.full_name || '',
    });
  };

  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true);
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
        hydrateForm(currentUser);
        setError(null);
      } catch (err) {
        console.error('Error loading profile:', err);
        setError('Błąd podczas wczytywania profilu. Wyświetlam dane przykładowe.');
        setUser(MOCK_USER);
        hydrateForm(MOCK_USER);
      } finally {
        setLoading(false);
      }
    };

    void loadProfile();
  }, []);

  const roleMetadata = useMemo(() => ({
    label: user?.role === 'ADMINISTRATOR' ? 'Administrator' : user?.role === 'EDITOR' ? 'Edytor' : 'Użytkownik',
    color: user?.role === 'ADMINISTRATOR' ? 'warning' : user?.role === 'EDITOR' ? 'info' : 'default',
  }), [user?.role]);

  const handleEdit = () => {
    if (!user) {
      return;
    }
    setIsEditing(true);
    hydrateForm(user);
    setSuccess(null);
    setError(null);
  };

  const handleCancel = () => {
    if (user) {
      hydrateForm(user);
    }
    setIsEditing(false);
    setError(null);
  };

  const handleSave = async () => {
    if (!user) {
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const updatePayload: UpdateUserRequest = {
        username: formData.username,
        email: formData.email,
        full_name: formData.full_name,
      };

      const updatedUser = await authService.updateCurrentUser(updatePayload);
      setUser(updatedUser);
      hydrateForm(updatedUser);
      setSuccess('Profil został zaktualizowany pomyślnie');
      setIsEditing(false);
    } catch (err) {
      console.error('Error updating profile:', err);
      setError('Błąd podczas aktualizacji profilu');
    } finally {
      setSaving(false);
    }
  };

  if (loading && !user) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        Profil użytkownika
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

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 33%' } }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar sx={{ width: 80, height: 80, mx: 'auto', mb: 2 }}>
                <PersonIcon sx={{ fontSize: 40 }} />
              </Avatar>
              <Typography variant="h6" gutterBottom>
                {user.full_name || user.username}
              </Typography>
              <Chip label={roleMetadata.label} color={roleMetadata.color as 'default' | 'info' | 'warning'} sx={{ mb: 2 }} />
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />
                <Typography variant="body2" color="text.secondary">
                  {user.email}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                <BadgeIcon sx={{ mr: 1, color: 'text.secondary' }} />
                <Typography variant="body2" color="text.secondary">
                  {user.username}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <CalendarIcon sx={{ mr: 1, color: 'text.secondary' }} />
                <Typography variant="body2" color="text.secondary">
                  Dołączył: {new Date(user.created_at).toLocaleDateString('pl-PL')}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 66%' } }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">Informacje osobiste</Typography>
                {!isEditing ? (
                  <Button variant="outlined" startIcon={<EditIcon />} onClick={handleEdit}>
                    Edytuj
                  </Button>
                ) : (
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button variant="outlined" startIcon={<CancelIcon />} onClick={handleCancel} disabled={saving}>
                      Anuluj
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                      onClick={handleSave}
                      disabled={saving}
                    >
                      {saving ? 'Zapisywanie...' : 'Zapisz'}
                    </Button>
                  </Box>
                )}
              </Box>

              <Divider sx={{ mb: 3 }} />

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  fullWidth
                  label="Nazwa użytkownika"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  disabled={!isEditing}
                  variant={isEditing ? 'outlined' : 'filled'}
                />

                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={!isEditing}
                  variant={isEditing ? 'outlined' : 'filled'}
                />

                <TextField
                  fullWidth
                  label="Imię i nazwisko"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  disabled={!isEditing}
                  variant={isEditing ? 'outlined' : 'filled'}
                />

                <TextField
                  fullWidth
                  label="Rola"
                  value={roleMetadata.label}
                  disabled
                  variant="filled"
                  helperText="Rola może zostać zmieniona tylko przez administratora"
                />

                <TextField
                  fullWidth
                  label="Status konta"
                  value={user.is_active ? 'Aktywne' : 'Nieaktywne'}
                  disabled
                  variant="filled"
                />

                <TextField
                  fullWidth
                  label="Ostatnie logowanie"
                  value={user.last_login ? new Date(user.last_login).toLocaleString('pl-PL') : 'Nigdy'}
                  disabled
                  variant="filled"
                />
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

export default Profile;
