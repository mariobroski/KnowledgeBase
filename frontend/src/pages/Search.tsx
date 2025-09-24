import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Slider,
  Switch,
  Tab,
  Tabs,
  TextField,
  Typography,
  Button,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import { Search as SearchIcon, AutoAwesome as AutoIcon } from '@mui/icons-material';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';

interface Policy {
  id: string;
  name: string;
  description: string;
}

interface SearchResult {
  query: string;
  policy_type: string;
  response: string;
  justification: {
    type: string;
    [key: string]: any;
  };
  metrics: {
    search_time: number;
    generation_time: number;
    total_time: number;
    tokens_used: number;
    context_relevance: number;
    hallucination_score: number;
    faithfulness?: number;
    avg_degree_centrality?: number;
    avg_pagerank?: number;
    cost: number;
  };
  search_id: number;
  policy_selection?: {
    selected_policy: string;
    confidence: number;
    all_scores: { [key: string]: number };
    explanation: string;
    auto_selected: boolean;
  };
  response_details?: {
    response: string;
    elapsed_time: number;
    tokens_used: number;
    model?: string;
    [key: string]: any;
  };
  context?: Record<string, any>;
}

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [selectedPolicy, setSelectedPolicy] = useState<string>('text');
  const [autoSelectPolicy, setAutoSelectPolicy] = useState<boolean>(false);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [tabValue, setTabValue] = useState<number>(0);
  const [similarityThreshold, setSimilarityThreshold] = useState<number>(0.7);
  const [topKResults, setTopKResults] = useState<number>(5);
  const [graphDepth, setGraphDepth] = useState<number>(3);
  const [defaultSettings, setDefaultSettings] = useState<Record<string, number>>({});
  const [settingsLoaded, setSettingsLoaded] = useState<boolean>(false);

  useEffect(() => {
    setPolicies([
      {
        id: 'text',
        name: 'TekstRAG',
        description: 'Standardowa polityka RAG, która wykorzystuje fragmenty tekstu jako kontekst.'
      },
      {
        id: 'facts',
        name: 'FaktRAG',
        description: 'Polityka RAG, która wykorzystuje wyekstrahowane fakty jako kontekst.'
      },
      {
        id: 'graph',
        name: 'GrafRAG',
        description: 'Polityka RAG, która wykorzystuje graf wiedzy jako kontekst.'
      },
      {
        id: 'hybrid',
        name: 'HybrydRAG',
        description: 'Polityka RAG łącząca wyniki TekstRAG, FaktRAG i GrafRAG.'
      }
    ]);
  }, []);

  useEffect(() => {
    const fetchDefaults = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/search/settings/defaults');
        if (!response.ok) {
          throw new Error('Nie udało się pobrać ustawień domyślnych');
        }
        const data = await response.json();
        setDefaultSettings(data);
        if (typeof data.similarity_threshold === 'number') {
          setSimilarityThreshold(data.similarity_threshold);
        }
        if (typeof data.top_k_results === 'number') {
          setTopKResults(data.top_k_results);
        }
        if (typeof data.graph_max_depth === 'number') {
          setGraphDepth(data.graph_max_depth);
        }
      } catch (error) {
        console.error('Błąd pobierania ustawień domyślnych:', error);
      } finally {
        setSettingsLoaded(true);
      }
    };

    fetchDefaults().catch(console.error);
  }, []);

  const resetToDefaults = () => {
    if (!defaultSettings) return;
    if (typeof defaultSettings.similarity_threshold === 'number') {
      setSimilarityThreshold(defaultSettings.similarity_threshold);
    }
    if (typeof defaultSettings.top_k_results === 'number') {
      setTopKResults(defaultSettings.top_k_results);
    }
    if (typeof defaultSettings.graph_max_depth === 'number') {
      setGraphDepth(defaultSettings.graph_max_depth);
    }
  };

  const handleSearch = async (): Promise<void> => {
    if (!query.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      let response;
      const sanitizedTopK = Math.max(1, Math.min(20, Math.round(topKResults)));
      const settingsPayload: Record<string, number> = {
        similarity_threshold: Number(similarityThreshold.toFixed(2)),
        top_k_results: sanitizedTopK,
      };

      if (selectedPolicy === 'graph' || autoSelectPolicy) {
        settingsPayload.graph_max_depth = Math.max(1, Math.min(5, Math.round(graphDepth)));
      }

      if (autoSelectPolicy) {
        // Użyj automatycznego wyboru polityki
        response = await fetch('http://localhost:8000/api/search/auto', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: query,
            limit: sanitizedTopK,
            settings: settingsPayload
          }),
        });
      } else {
        // Użyj wybranej polityki
        response = await fetch('http://localhost:8000/api/search/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: query,
            policy: selectedPolicy,
            limit: sanitizedTopK,
            settings: settingsPayload
          }),
        });
      }

      if (!response.ok) {
        throw new Error('Błąd podczas wyszukiwania');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Błąd wyszukiwania:', error);
      // Fallback do demonstracyjnych danych
      setTimeout(() => {
        let demoResult: SearchResult;

      if (selectedPolicy === 'text') {
        demoResult = {
          query: query,
          policy_type: 'text',
          response: `TekstRAG znalazł odpowiedź na podstawie fragmentów tekstu. ${query} jest ważnym zagadnieniem w kontekście RAG. Fragmenty tekstu dostarczają kontekstu dla modelu językowego.`,
          justification: {
            type: 'fragments',
            fragments: [
              {
                id: 1,
                content: `Fragment tekstu zawierający informacje o ${query}.`,
                relevance: 0.92,
                article_title: 'Wprowadzenie do RAG'
              },
              {
                id: 2,
                content: `Inny fragment tekstu związany z ${query} i jego zastosowaniami.`,
                relevance: 0.85,
                article_title: 'Zastosowania RAG'
              }
            ]
          },
          metrics: {
            search_time: 0.25,
            generation_time: 0.45,
            total_time: 0.70,
            tokens_used: 350,
            context_relevance: 0.80,
            hallucination_score: 0.15,
            cost: 0.0070
          },
          search_id: 1
        };
      } else if (selectedPolicy === 'facts') {
        demoResult = {
          query: query,
          policy_type: 'facts',
          response: `FaktRAG znalazł odpowiedź na podstawie wyekstrahowanych faktów. ${query} jest powiązane z kilkoma kluczowymi faktami, które zostały wykorzystane do wygenerowania odpowiedzi.`,
          justification: {
            type: 'facts',
            facts: [
              {
                id: 1,
                content: `${query} jest związane z technologią RAG.`,
                source_fragment_id: 5,
                article_title: 'Fakty o RAG'
              },
              {
                id: 2,
                content: `${query} wykorzystuje modele językowe do generowania odpowiedzi.`,
                source_fragment_id: 5,
                article_title: 'Fakty o RAG'
              }
            ]
          },
          metrics: {
            search_time: 0.35,
            generation_time: 0.30,
            total_time: 0.65,
            tokens_used: 280,
            context_relevance: 0.85,
            hallucination_score: 0.10,
            cost: 0.0056
          },
          search_id: 2
        };
      } else {
        demoResult = {
          query: query,
          policy_type: 'graph',
          response: `GrafRAG znalazł odpowiedź na podstawie grafu wiedzy. ${query} jest powiązane z innymi encjami w grafie, co pozwala na wygenerowanie bardziej kontekstowej odpowiedzi.`,
          justification: {
            type: 'graph_paths',
            paths: [
              {
                id: 1,
                path: [
                  {id: 10, name: 'RAG', type: 'Technologia'},
                  {relation: 'ZAWIERA', id: 5},
                  {id: 11, name: 'GrafRAG', type: 'Wariant'}
                ],
                relevance: 0.95
              },
              {
                id: 2,
                path: [
                  {id: 11, name: 'GrafRAG', type: 'Wariant'},
                  {relation: 'WYKORZYSTUJE', id: 6},
                  {id: 12, name: 'Graf Wiedzy', type: 'Struktura Danych'}
                ],
                relevance: 0.92
              }
            ]
          },
          metrics: {
            search_time: 0.40,
            generation_time: 0.35,
            total_time: 0.75,
            tokens_used: 300,
            context_relevance: 0.90,
            hallucination_score: 0.08,
            cost: 0.0060
          },
          search_id: 3
        };
      }

      setResult(demoResult);
      setLoading(false);
    }, 1500);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const renderJustification = () => {
    if (!result) return null;

    if (result.justification.type === 'fragments') {
      return (
        <Box>
          <Typography variant="h6" gutterBottom>Fragmenty tekstu</Typography>
          {result.justification.fragments.map((fragment: any) => (
            <Paper key={fragment.id} sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                Artykuł: {fragment.article_title} (Trafność: {fragment.relevance.toFixed(2)})
              </Typography>
              <Typography variant="body1">{fragment.content}</Typography>
            </Paper>
          ))}
        </Box>
      );
    } else if (result.justification.type === 'facts') {
      return (
        <Box>
          <Typography variant="h6" gutterBottom>Fakty</Typography>
          {result.justification.facts.map((fact: any) => (
            <Paper key={fact.id} sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                Źródło: {fact.article_title}
              </Typography>
              <Typography variant="body1">{fact.content}</Typography>
            </Paper>
          ))}
        </Box>
      );
    } else if (result.justification.type === 'graph_paths') {
      return (
        <Box>
          <Typography variant="h6" gutterBottom>Ścieżki w grafie</Typography>
          {result.justification.paths.map((path: any) => (
            <Paper key={path.id} sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                Trafność: {path.relevance.toFixed(2)}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', mt: 1 }}>
                {path.path.map((item: any, index: number) => (
                  <React.Fragment key={index}>
                    {index % 2 === 0 ? (
                      <Paper sx={{ p: 1, bgcolor: 'primary.light', color: 'white' }}>
                        <Typography variant="body2">
                          {item.name} ({item.type})
                        </Typography>
                      </Paper>
                    ) : (
                      <Typography variant="body2" sx={{ mx: 1 }}>
                        --{item.relation}--&gt;
                      </Typography>
                    )}
                  </React.Fragment>
                ))}
              </Box>
            </Paper>
          ))}
        </Box>
      );
    }

    return null;
  };

  const renderMetrics = () => {
    if (!result) return null;

    const { metrics, context } = result;
    const appliedSettings = context?.applied_settings ?? {};

    const performanceData = [
      { name: 'Wyszukiwanie', value: Number(metrics.search_time.toFixed(3)) },
      { name: 'Generowanie', value: Number(metrics.generation_time.toFixed(3)) },
      { name: 'Razem', value: Number(metrics.total_time.toFixed(3)) },
    ];

    const qualityData = [
      { name: 'Trafność', value: Number(((metrics.context_relevance ?? 0) * 100).toFixed(1)) },
      { name: 'Halucynacje', value: Number(((metrics.hallucination_score ?? 0) * 100).toFixed(1)) },
      { name: 'Zgodność', value: Number(((metrics.faithfulness ?? 0) * 100).toFixed(1)) },
    ];

    const costData = [
      { name: 'Tokeny', value: metrics.tokens_used },
      { name: 'Koszt (¢)', value: Number((metrics.cost * 100).toFixed(3)) },
    ];

    return (
      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Wydajność</Typography>
            <Typography variant="body2">
              Czas wyszukiwania: {metrics.search_time.toFixed(2)}s
            </Typography>
            <Typography variant="body2">
              Czas generowania: {metrics.generation_time.toFixed(2)}s
            </Typography>
            <Typography variant="body2">
              Całkowity czas: {metrics.total_time.toFixed(2)}s
            </Typography>
            <Box sx={{ height: 180, mt: 2 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis unit="s" />
                  <Tooltip formatter={(value: number) => `${value}s`} />
                  <Legend />
                  <Bar dataKey="value" fill="#1976d2" name="Czas [s]" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Jakość</Typography>
            <Typography variant="body2">
              Trafność kontekstu: {((metrics.context_relevance ?? 0) * 100).toFixed(0)}%
            </Typography>
            <Typography variant="body2">
              Poziom halucynacji: {((metrics.hallucination_score ?? 0) * 100).toFixed(0)}%
            </Typography>
            {typeof metrics.faithfulness === 'number' && (
              <Typography variant="body2">
                Zgodność (faithfulness): {((metrics.faithfulness ?? 0) * 100).toFixed(0)}%
              </Typography>
            )}
            <Box sx={{ height: 180, mt: 2 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={qualityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis unit="%" domain={[0, 100]} />
                  <Tooltip formatter={(value: number) => `${value}%`} />
                  <Legend />
                  <Bar
                    dataKey="value"
                    fill="#9c27b0"
                    name="Wskaźnik [%]"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Koszty</Typography>
            <Typography variant="body2">
              Użyte tokeny: {metrics.tokens_used}
            </Typography>
            <Typography variant="body2">
              Koszt: ${metrics.cost.toFixed(4)}
            </Typography>
            <Box sx={{ height: 180, mt: 2 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={costData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#2e7d32" name="Wartość" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Zastosowane ustawienia</Typography>
            <Grid container spacing={1}>
              {Object.entries(appliedSettings).map(([key, value]) => (
                <Grid item key={key}>
                  <Chip label={`${key}: ${value}`} color="default" variant="outlined" />
                </Grid>
              ))}
              {result?.context?.avg_degree_centrality !== undefined && (
                <Grid item>
                  <Chip label={`avg_degree_centrality: ${Number(result.context.avg_degree_centrality).toFixed(3)}`} variant="outlined" />
                </Grid>
              )}
              {result?.context?.avg_pagerank !== undefined && (
                <Grid item>
                  <Chip label={`avg_pagerank: ${Number(result.context.avg_pagerank).toFixed(4)}`} variant="outlined" />
                </Grid>
              )}
              {(!appliedSettings || Object.keys(appliedSettings).length === 0) && (
                <Typography variant="body2" color="textSecondary">
                  Brak dodatkowych ustawień dla tego zapytania.
                </Typography>
              )}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Wyszukiwanie z RAG
      </Typography>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Zapytanie"
                variant="outlined"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Wprowadź swoje zapytanie..."
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth disabled={autoSelectPolicy}>
                <InputLabel>Polityka RAG</InputLabel>
                <Select
                  value={selectedPolicy}
                  label="Polityka RAG"
                  onChange={(e) => setSelectedPolicy(e.target.value)}
                >
                  {policies.map((policy) => (
                    <MenuItem key={policy.id} value={policy.id}>
                      {policy.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={1}>
              <Button
                fullWidth
                variant="contained"
                color="primary"
                onClick={handleSearch}
                disabled={loading || !query.trim()}
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : (autoSelectPolicy ? <AutoIcon /> : <SearchIcon />)}
                sx={{ height: '56px' }}
              >
                {loading ? 'Szukam...' : 'Szukaj'}
              </Button>
            </Grid>
          </Grid>

          <Box mt={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={autoSelectPolicy}
                  onChange={(e) => setAutoSelectPolicy(e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <AutoIcon fontSize="small" />
                  <Typography variant="body2">
                    Automatyczny wybór polityki
                  </Typography>
                </Box>
              }
            />
          </Box>

          <Box mt={2}>
            <Typography variant="body2" color="textSecondary">
              {autoSelectPolicy 
                ? "System automatycznie wybierze najlepszą politykę RAG na podstawie analizy Twojego zapytania."
                : (selectedPolicy && policies.find(p => p.id === selectedPolicy)?.description)
              }
            </Typography>
          </Box>

          <Box mt={3}>
            <Typography variant="subtitle1" gutterBottom>
              Personalizacja wyników
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle2">Próg podobieństwa</Typography>
                <Slider
                  value={similarityThreshold}
                  min={0}
                  max={1}
                  step={0.05}
                  onChange={(_, value) => setSimilarityThreshold(value as number)}
                  valueLabelDisplay="auto"
                />
                <Typography variant="caption" color="textSecondary">
                  Aktualna wartość: {similarityThreshold.toFixed(2)}
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  type="number"
                  label="Liczba wyników (top-k)"
                  value={topKResults}
                  onChange={(e) => setTopKResults(Math.max(1, Math.min(20, Math.round(Number(e.target.value) || 1))))}
                  fullWidth
                  inputProps={{ min: 1, max: 20 }}
                />
              </Grid>
              {(selectedPolicy === 'graph' || autoSelectPolicy) && (
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2">Maksymalna głębokość ścieżki</Typography>
                  <Slider
                    value={graphDepth}
                    min={1}
                    max={5}
                    step={1}
                    marks
                    onChange={(_, value) => setGraphDepth(value as number)}
                    valueLabelDisplay="auto"
                  />
                </Grid>
              )}
            </Grid>
            <Box display="flex" justifyContent="flex-end" mt={2}>
              <Button
                variant="text"
                size="small"
                onClick={resetToDefaults}
                disabled={!settingsLoaded}
              >
                Przywróć wartości domyślne
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {result && (
        <Box>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h5" gutterBottom>Odpowiedź</Typography>
              
              {result.policy_selection?.auto_selected && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      Automatycznie wybrano politykę: {result.policy_selection.selected_policy}
                    </Typography>
                    <Typography variant="body2">
                      Pewność: {(result.policy_selection.confidence * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2">
                      {result.policy_selection.explanation}
                    </Typography>
                    <Box mt={1}>
                      {Object.entries(result.policy_selection.all_scores).map(([policy, score]) => (
                        <Chip
                          key={policy}
                          label={`${policy}: ${(score * 100).toFixed(0)}%`}
                          size="small"
                          variant={policy === result.policy_selection?.selected_policy ? "filled" : "outlined"}
                          color={policy === result.policy_selection?.selected_policy ? "primary" : "default"}
                          sx={{ mr: 1, mb: 1 }}
                        />
                      ))}
                    </Box>
                  </Box>
                </Alert>
              )}
              
              <Typography variant="body1" paragraph>
                {result.response}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Polityka: {policies.find(p => p.id === result.policy_type)?.name} | 
                ID wyszukiwania: {result.search_id}
              </Typography>
              {result.response_details?.model && (
                <Typography variant="caption" color="textSecondary" display="block">
                  Model / strategia: {result.response_details.model}
                </Typography>
              )}
            </CardContent>
          </Card>

          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab label="Uzasadnienie" />
              <Tab label="Metryki" />
            </Tabs>
          </Box>

          {tabValue === 0 && renderJustification()}
          {tabValue === 1 && renderMetrics()}
        </Box>
      )}
    </Box>
  );
};

export default SearchPage;
