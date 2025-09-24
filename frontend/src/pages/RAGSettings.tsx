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
  Card,
  CardContent,
  Divider,
  Tabs,
  Tab,
  Paper,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Save as SaveIcon,
  RestoreFromTrash as RestoreIcon,
  ExpandMore as ExpandMoreIcon,
  Tune as TuneIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  Analytics as AnalyticsIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
} from '@mui/icons-material';

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
      id={`rag-tabpanel-${index}`}
      aria-labelledby={`rag-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

interface RAGConfiguration {
  // Podstawowe ustawienia RAG
  chunk_size: number;
  chunk_overlap: number;
  max_tokens: number;
  similarity_threshold: number;
  embedding_model: string;
  
  // Ustawienia wyszukiwania
  max_results: number;
  context_limit: number;
  
  // Ustawienia wydajności
  cache_enabled: boolean;
  parallel_processing: boolean;
  
  // Ustawienia modelu
  openai_model: string;
  temperature: number;
  max_response_tokens: number;
  
  // Ustawienia polityk RAG
  text_rag_enabled: boolean;
  fact_rag_enabled: boolean;
  graph_rag_enabled: boolean;
  hybrid_rag_enabled: boolean;
  
  // Parametry specjalistyczne
  fact_confidence_threshold: number;
  graph_max_depth: number;
  hybrid_text_weight: number;
  hybrid_fact_weight: number;
  hybrid_graph_weight: number;
}

interface RAGPolicy {
  id: string;
  name: string;
  description: string;
  type: 'text' | 'fact' | 'graph' | 'hybrid';
  enabled: boolean;
  config: Partial<RAGConfiguration>;
}

const defaultConfiguration: RAGConfiguration = {
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
  text_rag_enabled: true,
  fact_rag_enabled: true,
  graph_rag_enabled: true,
  hybrid_rag_enabled: true,
  fact_confidence_threshold: 0.8,
  graph_max_depth: 3,
  hybrid_text_weight: 0.4,
  hybrid_fact_weight: 0.3,
  hybrid_graph_weight: 0.3,
};

const defaultPolicies: RAGPolicy[] = [
  {
    id: 'text-rag',
    name: 'TekstRAG',
    description: 'Tradycyjne wyszukiwanie oparte na fragmentach tekstu',
    type: 'text',
    enabled: true,
    config: {
      chunk_size: 1000,
      similarity_threshold: 0.7,
      max_results: 10,
    }
  },
  {
    id: 'fact-rag',
    name: 'FaktRAG',
    description: 'Wyszukiwanie oparte na wyekstrahowanych faktach',
    type: 'fact',
    enabled: true,
    config: {
      fact_confidence_threshold: 0.8,
      max_results: 8,
    }
  },
  {
    id: 'graph-rag',
    name: 'GrafRAG',
    description: 'Wyszukiwanie wykorzystujące graf wiedzy',
    type: 'graph',
    enabled: true,
    config: {
      graph_max_depth: 3,
      max_results: 6,
    }
  },
  {
    id: 'hybrid-rag',
    name: 'HybrydowyRAG',
    description: 'Kombinacja wszystkich metod RAG',
    type: 'hybrid',
    enabled: true,
    config: {
      hybrid_text_weight: 0.4,
      hybrid_fact_weight: 0.3,
      hybrid_graph_weight: 0.3,
    }
  }
];

const RAGSettings: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [configuration, setConfiguration] = useState<RAGConfiguration>(defaultConfiguration);
  const [policies, setPolicies] = useState<RAGPolicy[]>(defaultPolicies);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const isAdmin = () => true; // Mock function

  const loadConfiguration = useCallback(async () => {
    try {
      setLoading(true);
      // Mock API call - w rzeczywistości tutaj byłoby wywołanie API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Symulacja załadowania konfiguracji
      setConfiguration(defaultConfiguration);
      setPolicies(defaultPolicies);
      setError(null);
    } catch (err) {
      setError('Błąd podczas ładowania konfiguracji RAG');
      console.error('Error loading configuration:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAdmin()) {
      setError('Brak uprawnień do zarządzania ustawieniami RAG');
      return;
    }
    void loadConfiguration();
  }, [loadConfiguration]);

  const saveConfiguration = async () => {
    try {
      setSaving(true);
      setError(null);
      
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setSuccess('Konfiguracja RAG została zapisana pomyślnie');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Błąd podczas zapisywania konfiguracji');
      console.error('Error saving configuration:', err);
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = () => {
    setConfiguration(defaultConfiguration);
    setPolicies(defaultPolicies);
    setSuccess('Przywrócono ustawienia domyślne');
    setTimeout(() => setSuccess(null), 3000);
  };

  const handleConfigChange = (field: keyof RAGConfiguration, value: any) => {
    setConfiguration(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handlePolicyToggle = (policyId: string) => {
    setPolicies(prev => prev.map(policy => 
      policy.id === policyId 
        ? { ...policy, enabled: !policy.enabled }
        : policy
    ));
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (!isAdmin()) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Brak uprawnień do zarządzania ustawieniami RAG
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
        <TuneIcon sx={{ mr: 2, fontSize: 32 }} />
        <Typography variant="h4" component="h1">
          Ustawienia RAG
        </Typography>
      </Box>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Centralny panel zarządzania wszystkimi ustawieniami systemu Retrieval-Augmented Generation
      </Typography>

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

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="RAG settings tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<SettingsIcon />} label="Konfiguracja podstawowa" />
          <Tab icon={<SpeedIcon />} label="Polityki RAG" />
          <Tab icon={<SecurityIcon />} label="Wydajność" />
          <Tab icon={<AnalyticsIcon />} label="Monitoring" />
        </Tabs>

        {/* Tab 1: Konfiguracja podstawowa */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {/* Ustawienia fragmentacji tekstu */}
            <Grid item xs={12}>
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Fragmentacja tekstu</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Rozmiar fragmentu (chunk size)"
                        type="number"
                        value={configuration.chunk_size}
                        onChange={(e) => handleConfigChange('chunk_size', parseInt(e.target.value))}
                        helperText="Maksymalna liczba znaków w jednym fragmencie tekstu"
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Nakładanie fragmentów (overlap)"
                        type="number"
                        value={configuration.chunk_overlap}
                        onChange={(e) => handleConfigChange('chunk_overlap', parseInt(e.target.value))}
                        helperText="Liczba znaków nakładających się między fragmentami"
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>

            {/* Ustawienia wyszukiwania */}
            <Grid item xs={12}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Parametry wyszukiwania</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Maksymalna liczba wyników"
                        type="number"
                        value={configuration.max_results}
                        onChange={(e) => handleConfigChange('max_results', parseInt(e.target.value))}
                        helperText="Liczba fragmentów zwracanych przez wyszukiwanie"
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Box sx={{ px: 2 }}>
                        <Typography gutterBottom>
                          Próg podobieństwa: {configuration.similarity_threshold}
                        </Typography>
                        <Slider
                          value={configuration.similarity_threshold}
                          onChange={(_, value) => handleConfigChange('similarity_threshold', value)}
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
                          value={configuration.embedding_model}
                          onChange={(e) => handleConfigChange('embedding_model', e.target.value)}
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

            {/* Ustawienia modelu językowego */}
            <Grid item xs={12}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Model językowy</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Model OpenAI</InputLabel>
                        <Select
                          value={configuration.openai_model}
                          onChange={(e) => handleConfigChange('openai_model', e.target.value)}
                        >
                          <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
                          <MenuItem value="gpt-4">GPT-4</MenuItem>
                          <MenuItem value="gpt-4-turbo">GPT-4 Turbo</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Box sx={{ px: 2 }}>
                        <Typography gutterBottom>
                          Temperatura: {configuration.temperature}
                        </Typography>
                        <Slider
                          value={configuration.temperature}
                          onChange={(_, value) => handleConfigChange('temperature', value)}
                          min={0}
                          max={1}
                          step={0.1}
                          marks
                          valueLabelDisplay="auto"
                        />
                      </Box>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Maksymalna liczba tokenów odpowiedzi"
                        type="number"
                        value={configuration.max_response_tokens}
                        onChange={(e) => handleConfigChange('max_response_tokens', parseInt(e.target.value))}
                        helperText="Limit tokenów dla generowanej odpowiedzi"
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 2: Polityki RAG */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Dostępne polityki RAG
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Zarządzaj różnymi strategiami wyszukiwania i generowania odpowiedzi
              </Typography>
            </Grid>

            {policies.map((policy) => (
              <Grid item xs={12} md={6} key={policy.id}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          {policy.name}
                        </Typography>
                        <Chip 
                          label={policy.type.toUpperCase()} 
                          size="small" 
                          color="primary" 
                          variant="outlined"
                          sx={{ mb: 1 }}
                        />
                      </Box>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={policy.enabled}
                            onChange={() => handlePolicyToggle(policy.id)}
                          />
                        }
                        label=""
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {policy.description}
                    </Typography>
                    
                    {/* Parametry specyficzne dla polityki */}
                    {policy.type === 'fact' && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Próg pewności faktów: {configuration.fact_confidence_threshold}
                        </Typography>
                        <Slider
                          value={configuration.fact_confidence_threshold}
                          onChange={(_, value) => handleConfigChange('fact_confidence_threshold', value)}
                          min={0}
                          max={1}
                          step={0.1}
                          size="small"
                          disabled={!policy.enabled}
                        />
                      </Box>
                    )}
                    
                    {policy.type === 'graph' && (
                      <Box sx={{ mt: 2 }}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Maksymalna głębokość grafu"
                          type="number"
                          value={configuration.graph_max_depth}
                          onChange={(e) => handleConfigChange('graph_max_depth', parseInt(e.target.value))}
                          disabled={!policy.enabled}
                        />
                      </Box>
                    )}
                    
                    {policy.type === 'hybrid' && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Wagi fuzji
                        </Typography>
                        <Grid container spacing={1}>
                          <Grid item xs={4}>
                            <TextField
                              fullWidth
                              size="small"
                              label="Tekst"
                              type="number"
                              inputProps={{ step: 0.1, min: 0, max: 1 }}
                              value={configuration.hybrid_text_weight}
                              onChange={(e) => handleConfigChange('hybrid_text_weight', parseFloat(e.target.value))}
                              disabled={!policy.enabled}
                            />
                          </Grid>
                          <Grid item xs={4}>
                            <TextField
                              fullWidth
                              size="small"
                              label="Fakty"
                              type="number"
                              inputProps={{ step: 0.1, min: 0, max: 1 }}
                              value={configuration.hybrid_fact_weight}
                              onChange={(e) => handleConfigChange('hybrid_fact_weight', parseFloat(e.target.value))}
                              disabled={!policy.enabled}
                            />
                          </Grid>
                          <Grid item xs={4}>
                            <TextField
                              fullWidth
                              size="small"
                              label="Graf"
                              type="number"
                              inputProps={{ step: 0.1, min: 0, max: 1 }}
                              value={configuration.hybrid_graph_weight}
                              onChange={(e) => handleConfigChange('hybrid_graph_weight', parseFloat(e.target.value))}
                              disabled={!policy.enabled}
                            />
                          </Grid>
                        </Grid>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* Tab 3: Wydajność */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Optymalizacja wydajności
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Cache'owanie
                  </Typography>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={configuration.cache_enabled}
                        onChange={(e) => handleConfigChange('cache_enabled', e.target.checked)}
                      />
                    }
                    label="Włącz cache'owanie wyników"
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Przyspieszenie powtarzających się zapytań
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Przetwarzanie równoległe
                  </Typography>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={configuration.parallel_processing}
                        onChange={(e) => handleConfigChange('parallel_processing', e.target.checked)}
                      />
                    }
                    label="Włącz przetwarzanie równoległe"
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Równoczesne przetwarzanie wielu fragmentów
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Limity zasobów
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Maksymalna liczba tokenów kontekstu"
                        type="number"
                        value={configuration.max_tokens}
                        onChange={(e) => handleConfigChange('max_tokens', parseInt(e.target.value))}
                        helperText="Limit tokenów dla całego kontekstu RAG"
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Limit kontekstu (znaki)"
                        type="number"
                        value={configuration.context_limit}
                        onChange={(e) => handleConfigChange('context_limit', parseInt(e.target.value))}
                        helperText="Maksymalna długość kontekstu w znakach"
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 4: Monitoring */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Metryki i monitoring
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Konfiguracja zbierania metryk i alertów dla systemu RAG
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Metryki jakości
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Context Relevance"
                    />
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Hallucination Score"
                    />
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Answer Relevancy"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Metryki wydajności
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Response Time"
                    />
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Search Time"
                    />
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Cost per Query"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Alerty i progi
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        label="Próg czasu odpowiedzi (s)"
                        type="number"
                        defaultValue={5}
                        helperText="Alert gdy czas odpowiedzi > próg"
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        label="Próg halucynacji"
                        type="number"
                        inputProps={{ step: 0.1, min: 0, max: 1 }}
                        defaultValue={0.3}
                        helperText="Alert gdy hallucination score > próg"
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        label="Próg kosztów dziennych ($)"
                        type="number"
                        defaultValue={100}
                        helperText="Alert gdy koszt dzienny > próg"
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 3 }}>
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
          onClick={saveConfiguration}
          disabled={saving}
        >
          {saving ? <CircularProgress size={20} /> : 'Zapisz konfigurację'}
        </Button>
      </Box>
    </Box>
  );
};

export default RAGSettings;