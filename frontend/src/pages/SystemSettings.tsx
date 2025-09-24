import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Grid,
  TextField,
  Button,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Slider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Save as SaveIcon,
  RestoreFromTrash as RestoreIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';

interface SystemSettingsConfig {
  // RAG Configuration
  chunk_size: number;
  chunk_overlap: number;
  max_tokens: number;
  similarity_threshold: number;
  embedding_model: string;
  
  // Search Configuration
  max_results: number;
  context_limit: number;
  
  // Performance Settings
  cache_enabled: boolean;
  parallel_processing: boolean;
  
  // Model Settings
  openai_model: string;
  temperature: number;
  max_response_tokens: number;
}

const defaultSettings: SystemSettingsConfig = {
  chunk_size: 1000,
  chunk_overlap: 200,
  max_tokens: 4000,
  similarity_threshold: 0.7,
  embedding_model: 'sentence-transformers/all-MiniLM-L6-v2',
  max_results: 10,
  context_limit: 8000,
  cache_enabled: true,
  parallel_processing: true,
  openai_model: 'gpt-3.5-turbo',
  temperature: 0.7,
  max_response_tokens: 1000,
};

const SystemSettings: React.FC = () => {
  const isAdmin = () => true;
  const [settings, setSettings] = useState<SystemSettingsConfig>(defaultSettings);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadSettings = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/system-settings');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setSettings(data);
      setError(null);
    } catch (err) {
      setError('Błąd podczas ładowania ustawień systemowych');
      console.error('Error loading settings:', err);
      // Fallback to default settings
      setSettings(defaultSettings);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAdmin()) {
      setError('Brak uprawnień do panelu ustawień systemowych');
      return;
    }
    void loadSettings();
  }, [loadSettings]);

  const saveSettings = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('/api/admin/system-settings', {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save settings');
      }

      const updatedSettings = await response.json();
      setSettings(updatedSettings);
      setSuccess('Ustawienia zostały zapisane pomyślnie');
    } catch (err) {
      setError(`Błąd podczas zapisywania ustawień: ${err instanceof Error ? err.message : 'Unknown error'}`);
      console.error('Error saving settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = async () => {
    try {
      setError(null);
      setSuccess(null);
      
      const response = await fetch('/api/admin/system-settings/reset', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reset settings');
      }
      
      // Reload settings after reset
      await loadSettings();
      setSuccess('Przywrócono ustawienia domyślne');
    } catch (err) {
      setError(`Błąd podczas resetowania ustawień: ${err instanceof Error ? err.message : 'Unknown error'}`);
      console.error('Error resetting settings:', err);
    }
  };

  const handleInputChange = (field: keyof SystemSettingsConfig, value: any) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (!isAdmin()) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Brak uprawnień do panelu ustawień systemowych
        </Alert>
      </Box>
    );
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <SettingsIcon sx={{ mr: 2, fontSize: 32 }} />
        <Typography variant="h4" component="h1">
          Ustawienia Systemowe
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* RAG Configuration */}
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Konfiguracja RAG</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Rozmiar fragmentu (chunk size)"
                    type="number"
                    value={settings.chunk_size}
                    onChange={(e) => handleInputChange('chunk_size', parseInt(e.target.value))}
                    helperText="Maksymalna liczba znaków w jednym fragmencie tekstu"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Nakładanie fragmentów (overlap)"
                    type="number"
                    value={settings.chunk_overlap}
                    onChange={(e) => handleInputChange('chunk_overlap', parseInt(e.target.value))}
                    helperText="Liczba znaków nakładających się między fragmentami"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Maksymalna liczba tokenów"
                    type="number"
                    value={settings.max_tokens}
                    onChange={(e) => handleInputChange('max_tokens', parseInt(e.target.value))}
                    helperText="Limit tokenów dla kontekstu RAG"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box sx={{ px: 2 }}>
                    <Typography gutterBottom>
                      Próg podobieństwa: {settings.similarity_threshold}
                    </Typography>
                    <Slider
                      value={settings.similarity_threshold}
                      onChange={(_, value) => handleInputChange('similarity_threshold', value)}
                      min={0}
                      max={1}
                      step={0.1}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Model embeddings</InputLabel>
                    <Select
                      value={settings.embedding_model}
                      onChange={(e) => handleInputChange('embedding_model', e.target.value)}
                    >
                      <MenuItem value="sentence-transformers/all-MiniLM-L6-v2">
                        all-MiniLM-L6-v2 (szybki)
                      </MenuItem>
                      <MenuItem value="sentence-transformers/all-mpnet-base-v2">
                        all-mpnet-base-v2 (dokładny)
                      </MenuItem>
                      <MenuItem value="text-embedding-ada-002">
                        OpenAI Ada-002 (premium)
                      </MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Search Configuration */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Konfiguracja wyszukiwania</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Maksymalna liczba wyników"
                    type="number"
                    value={settings.max_results}
                    onChange={(e) => handleInputChange('max_results', parseInt(e.target.value))}
                    helperText="Liczba fragmentów zwracanych przez wyszukiwanie"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Limit kontekstu"
                    type="number"
                    value={settings.context_limit}
                    onChange={(e) => handleInputChange('context_limit', parseInt(e.target.value))}
                    helperText="Maksymalna długość kontekstu w znakach"
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Model Settings */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Ustawienia modelu językowego</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Model OpenAI</InputLabel>
                    <Select
                      value={settings.openai_model}
                      onChange={(e) => handleInputChange('openai_model', e.target.value)}
                    >
                      <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
                      <MenuItem value="gpt-4">GPT-4</MenuItem>
                      <MenuItem value="gpt-4-turbo">GPT-4 Turbo</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Maksymalne tokeny odpowiedzi"
                    type="number"
                    value={settings.max_response_tokens}
                    onChange={(e) => handleInputChange('max_response_tokens', parseInt(e.target.value))}
                    helperText="Limit tokenów dla generowanej odpowiedzi"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Box sx={{ px: 2 }}>
                    <Typography gutterBottom>
                      Temperatura: {settings.temperature}
                    </Typography>
                    <Slider
                      value={settings.temperature}
                      onChange={(_, value) => handleInputChange('temperature', value)}
                      min={0}
                      max={2}
                      step={0.1}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </Box>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Performance Settings */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Ustawienia wydajności</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.cache_enabled}
                        onChange={(e) => handleInputChange('cache_enabled', e.target.checked)}
                      />
                    }
                    label="Włącz cache'owanie"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.parallel_processing}
                        onChange={(e) => handleInputChange('parallel_processing', e.target.checked)}
                      />
                    }
                    label="Przetwarzanie równoległe"
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Action Buttons */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              startIcon={<RestoreIcon />}
              onClick={resetToDefaults}
            >
              Przywróć domyślne
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={saveSettings}
              disabled={saving}
            >
              {saving ? <CircularProgress size={20} /> : 'Zapisz ustawienia'}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SystemSettings;